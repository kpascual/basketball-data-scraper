from bs4 import BeautifulSoup
import csv
import logging


class PlayerNbaCom:

    def __init__(self, filename, gamedata, dbobj, lgobj):
        self.gamedata = gamedata
        self.xml = open(filename,'r').read()
        self.soup = BeautifulSoup(self.xml, 'lxml')
        self.date_played = self.gamedata['date_played']
        self.db = dbobj
        self.lgobj = lgobj


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

                    player_id = self.db.query_dict("SELECT id FROM player WHERE nbacom_player_id = '%s'" % (nbacom_player_id))[0]['id']
                    self.db.insert_or_update('player_by_game', [{'player_id': player_id, 'game_id': self.gamedata['id'], 'jersey_number': jersey_number}])


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

            obj = player.PlayerNbaCom(LOGDIR_EXTRACT + files['boxscore_nbacom'], gamedata, dbobj)
            obj.resolveNewPlayers()


def resolveNewPlayers(game, filename, dbobj, lgobj):
    obj = PlayerNbaCom(filename, game, dbobj, lgobj)
    obj.resolveNewPlayers()

