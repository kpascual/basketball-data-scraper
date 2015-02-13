from bs4 import BeautifulSoup
import csv
import json
import os
import logging
import datetime
import difflib

from config import constants 
import utils


# Script to resolve player differences between NBA.com, CBSSports.com, and ESPN.com sources
# Use NBA.com and CBSSports first, because they're more well-defined


# Take the new files provided, and look them up in the master player table
# Add league limiter to all the things

LOGDIR_CLEAN = constants.LOGDIR_CLEAN
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT


class PlayerNbaCom:

    def __init__(self, filename, gamedata, dbobj):
        self.gamedata = gamedata
        self.xml = open(filename,'r').read()
        self.soup = BeautifulSoup(self.xml, 'lxml')
        self.date_played = self.gamedata['date_played']
        self.db = dbobj


    def resolveNewPlayers(self):
        players = self.getPlayers()
        self.checkStaging(players)


    def getPlayers(self):
        soup = self.soup
        playbyplaydata = soup.findAll("pl")

        home_team = soup.find("htm")
        away_team = soup.find("vtm")

        all_players = []
        for team_name, team in [('home',home_team), ('away',away_team)]:
            
            players = team.findAll("pl")
            team_data = team['tm'].split('|')[-1]


            for player in players:
                player_data = player['name'].split('|')
                player_data.append(team_data)
                all_players.append(player_data)

        return all_players


    def checkStaging(self, players):
        for row in players:
            nbacom_player_id    = row[0]
            player_tag          = row[1]
            last_name           = row[2].split(',')[0].strip()
            first_name          = ' '.join(row[2].split(',')[1:]).strip()
            jersey_number       = row[5]
            team                = row[6]


            if nbacom_player_id:
                data = {
                    'nbacom_player_id':nbacom_player_id,
                    'game_id':self.gamedata['id'],
                    'player_tag':player_tag,
                    'last_name':last_name,
                    'first_name':first_name,
                    'jersey_number':jersey_number,
                    'team':team
                }
                self.db.insert_or_update('player_nbacom_by_game',[data])

                result = self.db.query("SELECT * FROM player_nbacom WHERE nbacom_player_id = '%s'" % (nbacom_player_id))
                if not result:
                    print "  + PLAYER: cannot find %s.  inserting into db" % (row[2])

                    result = self.db.query("""
                        INSERT IGNORE INTO player
                            (nbacom_player_id, nbacom_player_tag, last_name, first_name, full_name, date_found, position) 
                        VALUES ("%s","%s","%s","%s","%s","%s","U")
                    """ % (nbacom_player_id, player_tag, last_name, first_name, first_name + ' ' + last_name, self.date_played))
                    logging.info("PLAYER - game_id: %s - adding new player to resolved player table: %s" % (self.gamedata['id'], row[2]))

                # Update player_tags
                result = self.db.query("SELECT * FROM player_nbacom WHERE nbacom_player_id = '%s' AND player_tag = '%s'" % (nbacom_player_id, player_tag))
                if not result:
                    sql = """
                        INSERT INTO player_nbacom 
                            (nbacom_player_id, player_tag, last_name, first_name, date_found) 
                        VALUES ("%s","%s","%s","%s","%s")
                    """ % (nbacom_player_id, player_tag, last_name, first_name, self.date_played)
                    
                    self.db.query(sql)
                    logging.info("PLAYER - game_id: %s - Found new player or tag in NBA.com files: %s" % (self.gamedata['id'], row[2]))
                else:
                    # check if there exists a different nbacom_player tag. if so, unpack player_tag and add to list
                    has_tag = self.db.query("SELECT * FROM player WHERE nbacom_player_id = '%s' AND (nbacom_player_tag LIKE '%%,%s%%' OR nbacom_player_tag LIKE '%s,%%' OR nbacom_player_tag = '%s')" % (nbacom_player_id, player_tag, player_tag, player_tag))
                    if not has_tag:
                        data = self.db.query_dict("SELECT * FROM player WHERE nbacom_player_id = '%s'" % (nbacom_player_id))[0]
                        data['nbacom_player_tag'] = "%s,%s" % (data['nbacom_player_tag'], player_tag)
                        print "  + PLAYER: Could not find player tag %s. Adding to db" % (player_tag)
                        self.db.insert_or_update('player', [{'id': data['id'], 'nbacom_player_tag': data['nbacom_player_tag']}])

                # Update player
                self.db.query("""
                    UPDATE player_nbacom_by_game pnba
                        INNER JOIN player p ON p.nbacom_player_id = pnba.nbacom_player_id 
                        AND pnba.nbacom_player_id != '' and p.id != 0
                    SET pnba.player_id = p.id
                    WHERE pnba.game_id = %s
                """ % (self.gamedata['id']))

                # Update team
                self.db.query("""
                    UPDATE player_nbacom_by_game pnba
                        INNER JOIN team t ON t.nbacom_code = pnba.team
                    SET pnba.team_id = t.id
                    WHERE pnba.game_id = %s
                        AND (t.id = %s OR t.id = %s)
                """ % (self.gamedata['id'], self.gamedata['home_team_id'], self.gamedata['away_team_id']))
            else:
                data = {
                    'nbacom_player_id':nbacom_player_id,'game_id':self.gamedata['id'],
                    'player_tag':player_tag,'last_name':last_name,'first_name':first_name,
                    'jersey_number':jersey_number,'team':team
                }
                self.db.insert_or_update('player_nbacom_unknown_by_game',[data])

                #self.managePlayerTeamHistory(nbacom_player_id, team)
    
    
    def managePlayerTeamHistory(self, nbacom_player_id, nbacom_team_code): 

        player_id = self.db.query("""
            SELECT p.id
            FROM 
                player p 
            WHERE 
                p.nbacom_player_id = "%s"
        """ % (nbacom_player_id))[0][0]
       
        team_id = '' 
        team_id = self.db.query("""
            SELECT id
            FROM team
            WHERE nbacom_code = "%s"
        """ % (nbacom_team_code))[0][0]
        
        # Add to team-player history table if it isn't already existing
        check_team = self.db.query("""
            SELECT id FROM player_team_history
            WHERE player_id = %s AND team_id = "%s" AND end_date IS NULL
        """ % (player_id, team_id)) 

        if not check_team:
            # If exists, close out most recent record
            player_team_history = self.db.query("""
                SELECT id FROM player_team_history
                WHERE player_id = %s AND end_date IS NULL
            """ % (player_id))
           
            if player_team_history:
                player_team_history_id = player_team_history[0][0] 
                self.db.query("""
                    UPDATE player_team_history SET end_date = "%s" WHERE id = %s
                """ % (self.date_played, player_team_history_id))
                logging.info("""PLAYER - game_id: %s - Closing out player team history for player_id: %s, player_team_history_id: %s""" % (self.gamedata['id'], player_id, player_team_history_id))

            # Add new record
            self.db.query("""
                INSERT IGNORE INTO player_team_history
                (player_id, team_id, start_date)
                SELECT id, %s, "%s"
                FROM
                    player p
                WHERE
                    p.id = "%s"
            """ % (team_id, self.date_played, player_id))
            logging.info("""PLAYER - game_id: %s - Added new player team history for player_id %s; date: %s; team: %s""" % (self.gamedata['id'], player_id, self.date_played, team_id))


class PlayerStatsNbaCom:
    def __init__(self, filename, gamedata, dbobj):
        self.raw_data = open(filename,'r').read()
        self.dbobj = dbobj
        self.game = gamedata
        self.filename = filename

    
    def resolveNewPlayers(self):
        data = json.loads(self.raw_data)

        for line in data['resultSets']:
            if line['name'] in ['PlayerStats']:
                header = line['headers']
                for row in line['rowSet']:
                    newdata = dict(zip([a.lower() for a in header], row))
                    team_id = self._matchTeam(newdata['team_id'])
                    insert_data = {
                        'statsnbacom_player_id': newdata['player_id'], 
                        'statsnbacom_player_name': newdata['player_name'], 
                        'statsnbacom_team_id': newdata['team_id'], 
                        'game_id': self.game['id'],
                        'team_id': team_id
                    }
                    # Log data into the database, for double-checking purposes
                    self.dbobj.insert_or_update('player_statsnbacom', [insert_data])


    def _matchTeam(self, statsnbacom_team_id):
        team_id = 0
        query = self.dbobj.query_dict("SELECT id FROM team WHERE statsnbacom_team_id = '%s'" % (statsnbacom_team_id))
        if query:
            team_id = query[0]['id']

        return team_id


class PlayerCbsSports: 
    def __init__(self, filename, gamedata, dbobj, lgobj):
        reader = csv.reader(open(filename,'r'),delimiter=',',lineterminator='\n')

        self.gamedata = gamedata
        self.data = [row for row in reader]
        self.date_played = self.gamedata['date_played']
        self.dbobj = dbobj
        self.lgobj = lgobj


    def resolveNewPlayers(self):
        game_id = self.gamedata['id']
        for row in self.data:
            cbssports_player_id = row[1]
            full_name = row[2].replace('&nbsp;',' ').strip()
            team_id = row[0]

            if cbssports_player_id:
                insert_data = {
                    'game_id'             : game_id,
                    'cbssports_player_id' : cbssports_player_id,
                    'full_name'           : full_name,
                    'first_name'          : full_name.split(' ')[0],
                    'last_name'           : ' '.join(full_name.split(' ')[1:]),
                    'jersey_number'       : row[3],
                    'team_id'             : row[0],
                    'position'            : row[4]
                }
                self.dbobj.insert_or_update('player_cbssports_by_game', [insert_data])

                result = self.dbobj.query("SELECT * FROM player_cbssports WHERE cbssports_player_id = '%s'" % (cbssports_player_id))

                if not result:
                    print "  + cannot find CBS Sports player.  inserting into db"
                    insert_data = {
                        'cbssports_player_id'   : cbssports_player_id,
                        'full_name'             : full_name,
                        'first_name'            : full_name.split(' ')[0],
                        'last_name'             : ' '.join(full_name.split(' ')[1:]),
                        'date_found'            : self.date_played
                    }
                    self.dbobj.insert_or_update('player_cbssports', [insert_data])
                    print "  + cannot find %s in CBS Sports.  inserting into db" % (full_name)
                    logging.debug("Found new player in CBSSports.com files: %s" % (full_name))

                self.matchWithResolvedPlayer(cbssports_player_id, full_name, team_id, self.gamedata['id'])


    def matchWithResolvedPlayer(self, cbssports_player_id, full_name, team_id, game_id):
        existing_player = self.dbobj.query("""
            SELECT * 
            FROM player
            WHERE cbssports_player_id = %s
        """ % (cbssports_player_id))
        # Must check: are cbssports_player_ids unique across leagues?

        if not existing_player:

            # Find a player resolution from prior games
            prior = self.dbobj.query_dict("""
                SELECT DISTINCT cbssports_player_id, player_id
                FROM player_cbssports_by_game
                WHERE 
                    cbssports_player_id = %s
            """ % (cbssports_player_id))
            if prior and len(prior) == 1:
                data = {
                    'player_id': prior[0]['player_id'],
                    'cbssports_player_id': cbssports_player_id,
                    'game_id': game_id
                }
                player_id = prior[0]['player_id']  
                self.dbobj.insert_or_update('player_cbssports_by_game', [data])

            else:
                logging.debug("PLAYER - game_id: %s - Could not match cbs sports player %s.  Skipping." % (game_id, full_name))
                print "  + Could not match player %s, %s. Skipping" % (full_name, cbssports_player_id)
                
            # Else, check by first name/last name, game_id


class Resolve:
    def __init__(self, dbobj):
        self.dbobj = dbobj
        self.utils = utils.Utils(self.dbobj)


    # Make statsnbacom the "primary key" in the resolved player table
    def add(self):
        new_players = self.dbobj.query_dict("""
            SELECT DISTINCT
                ps.statsnbacom_player_id
            FROM
                player_statsnbacom ps
                LEFT JOIN player p ON p.statsnbacom_player_id = ps.statsnbacom_player_id
            WHERE
                p.id IS NULL
        """)
        print new_players


    def resolveNbacom(self):
        new_players = self.dbobj.query_dict("""
            SELECT DISTINCT
                pn.nbacom_player_id
            FROM
                player_nbacom pn
                LEFT JOIN player p ON p.nbacom_player_id = pn.nbacom_player_id
            WHERE
                p.id IS NULL
        """)
        all_players = [line for line in self.utils.getAllPlayers() if line['nbacom_player_id'] is None and line['id'] > 0]
        print all_players


    def resolveStatsNbacom(self):
        new_players = self.dbobj.query_dict("""
            SELECT DISTINCT
                pn.statsnbacom_player_id, 
                pn.statsnbacom_player_name
            FROM
                player_statsnbacom pn
                LEFT JOIN player p ON p.statsnbacom_player_id = pn.statsnbacom_player_id
            WHERE
                p.id IS NULL
        """)
        all_players = [(line['id'], line['name']) for line in self.utils.getAllPlayers() if line['statsnbacom_player_id'] is None and line['id'] > 0]

        for line in new_players:
            matched_player_id = self.matchByNameApproximate(line['statsnbacom_player_name'], all_players)
            
            if matched_player_id > 0:
                self.dbobj.insert_or_update('player', [{'id': matched_player_id, 'statsnbacom_player_id': line['statsnbacom_player_id']}])


    def resolveStatsNbacomByGame(self, game_id):
        data = self.dbobj.query_dict("""
            SELECT DISTINCT
                pn.statsnbacom_player_id, pn.game_id, p.id as player_id
            FROM
                player_statsnbacom pn
                INNER JOIN player p ON p.statsnbacom_player_id = pn.statsnbacom_player_id
            WHERE
                pn.player_id IS NULL
                AND pn.game_id = %s
        """ % (game_id))

        if data:
            self.dbobj.insert_or_update('player_statsnbacom', data)


    def matchByNameApproximate(self, player_name, player_list):
        player_id = 0

        player_names = [name.lower() for id, name in player_list]
        player_ids = [id for id, name in player_list]

        match = difflib.get_close_matches(player_name.lower(),player_names,1, 0.8)
        if match:
            player_id = player_ids[player_names.index(match[0])]
            name = match[0]

            if len(match) > 1:
                logging.warning("CLEAN - resolve player - game_id: ? - multiple matching players found: %s" % (str(match)))
        else:
            logging.warning("CLEAN - resolve player - game_id: ? - cant match player name to resolved player: '%s'" % (player_name))

        return player_id


    def matchByStatsNbaComId(self, statsnbacom_player_id):
        player_id = 0
        match = self.dbobj.query_dict("SELECT * FROM player WHERE statsnbacom_player_id = %s" % (statsnbacom_player_id))

        if match:
            return match[0]['id']

        return player_id


    def getPlayers(self):
        print self.utils.getAllPlayers()



def populateOldPlayers():
    nbacom_files = sorted([f for f in os.listdir(LOGDIR_EXTRACT) if 'boxscore_nbacom' in f])
    cbssports_files = sorted([f for f in os.listdir(LOGDIR_EXTRACT) if 'cbssports_players' in f])
  
    """
    for f in nbacom_files:
        print f
        game_data = self.db_dict("SELECT * FROM nba.game WHERE abbrev = '%s'" % (f.replace('_boxscore_nbacom','')))[0]
        obj = PlayerNbaCom(LOGDIR_EXTRACT + f, game_data)
        obj.resolveNewPlayers()
    """

    for f in cbssports_files:
        print f
        gamedata = self.nba_query_dict("SELECT * FROM nba.game WHERE abbrev = '%s'" % (f.replace('_shotchart_cbssports_players','')))[0]
        obj = PlayerCbsSports(LOGDIR_EXTRACT + f, gamedata)
        obj.resolveNewPlayers()    


def updatePlayerFullName(dbobj):
    dbobj.query("""
        UPDATE player SET full_name = CONCAT(first_name,' ',last_name)
        WHERE full_name IS NULL
    """)




if __name__ == '__main__':
    #populateOldPlayers()
    main()
