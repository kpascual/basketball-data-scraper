import csv
import logging

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
                player_id = self.matchWithResolvedPlayer(cbssports_player_id, full_name, team_id, self.gamedata['id'])
                if player_id == 0:
                    player_data = {
                        'cbssports_player_id'   : cbssports_player_id,
                        'full_name'             : full_name,
                        'first_name'            : full_name.split(' ')[0],
                        'last_name'             : ' '.join(full_name.split(' ')[1:]),
                    }
                    print "   + Adding new player: %s" % (full_name)
                    self.addNewPlayer(player_data)
                    player_id = self.matchWithResolvedPlayer(cbssports_player_id, full_name, team_id, self.gamedata['id'])

                insert_data = {
                    'game_id'             : game_id,
                    'cbssports_player_id' : cbssports_player_id,
                    'player_id'           : player_id,
                    'full_name'           : full_name,
                    'first_name'          : full_name.split(' ')[0],
                    'last_name'           : ' '.join(full_name.split(' ')[1:]),
                    'jersey_number'       : row[3],
                    'team_id'             : row[0],
                    'position'            : row[4]
                }
                self.dbobj.insert_or_update('player_cbssports_by_game', [insert_data])
                self.dbobj.insert_or_update('player_by_game', [{'player_id': player_id, 'game_id': game_id}])

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

                    



    def matchWithResolvedPlayer(self, cbssports_player_id, full_name, team_id, game_id):
        existing_player = self.dbobj.query_dict("""
            SELECT * 
            FROM player
            WHERE cbssports_player_id = %s
        """ % (cbssports_player_id))
        # Must check: are cbssports_player_ids unique across leagues?

        if existing_player:
            return existing_player[0]['id']
        else:

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
                return player_id

            else:
                logging.debug("PLAYER - game_id: %s - Could not match cbs sports player %s.  Skipping." % (game_id, full_name))
                print "  + Could not match player %s, %s. Skipping" % (full_name, cbssports_player_id)
                return 0


    def addNewPlayer(self, data):
        self.dbobj.insert_or_update('player', [data])
                


            
def resolveNewPlayers(game, filename, dbobj, lgobj):
    obj = PlayerCbsSports(filename + '_players', game, dbobj, lgobj)
    obj.resolveNewPlayers()
