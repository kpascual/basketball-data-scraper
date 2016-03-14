import csv
import logging
import find_player


class PlayerCbsSports: 
    def __init__(self, filename, gamedata, dbobj, lgobj):
        reader = csv.reader(open(filename,'r'),delimiter=',',lineterminator='\n')

        self.gamedata = gamedata
        self.data = [row for row in reader]
        self.date_played = self.gamedata['date_played']
        self.dbobj = dbobj
        self.lgobj = lgobj


    def _parse(self):
        for row in self.data:
            cbssports_player_id = row[1]
            full_name = row[2].replace('&nbsp;',' ').strip()
            team_id = row[0]

            if cbssports_player_id:

                insert_data = {
                    'game_id'             : self.gamedata['id'],
                    'cbssports_player_id' : cbssports_player_id,
                    'full_name'           : full_name,
                    'first_name'          : full_name.split(' ')[0],
                    'last_name'           : ' '.join(full_name.split(' ')[1:]),
                    'jersey_number'       : row[3],
                    'team_id'             : row[0],
                    'position'            : row[4]
                }
                jersey_number = row[3]
                position = row[4]
                self.dbobj.insert_or_update('player_cbssports_by_game', [insert_data])

                # Resolving for cbssports player ids
                result = self.dbobj.query("SELECT * FROM player_cbssports WHERE cbssports_player_id = '%s'" % (cbssports_player_id))
                if not result:
                    insert_data = {
                        'cbssports_player_id'   : cbssports_player_id,
                        'full_name'             : full_name,
                        'first_name'            : full_name.split(' ')[0],
                        'last_name'             : ' '.join(full_name.split(' ')[1:]),
                        'date_found'            : self.date_played
                    }
                    self.dbobj.insert_or_update('player_cbssports', [insert_data])
                    logging.debug("Found new player in CBSSports.com files: %s" % (full_name))


    def insert(self):
        self._parse()
        query = self.dbobj.query_dict("SELECT * FROM player_cbssports_by_game WHERE game_id = %s" % (self.gamedata['id']))
        
        for row in query:
            player_id = self._matchWithResolvedPlayer(row['cbssports_player_id'], row['full_name'], row['team_id'], self.gamedata['id'])
            if player_id == 0:
                print "   + Adding new player: %s" % (row['full_name'])
                self.addNewPlayer(row['cbssports_player_id'], row['full_name'], row['first_name'], row['last_name'])
                player_id = self._matchWithResolvedPlayer(row['cbssports_player_id'], row['full_name'], row['team_id'], self.gamedata['id'])
                # Update _by_game table
                append_data = {
                    'cbssports_player_id': row['cbssports_player_id'],
                    'game_id': row['game_id'],
                    'player_id': player_id
                }
                self.dbobj.insert_or_update('player_cbssports_by_game',[append_data])

            self.dbobj.insert_or_update('player_by_game', [
                {
                    'player_id': player_id, 
                    'game_id': self.gamedata['id'], 
                    'team_id': row['team_id'],
                    'jersey_number': row['jersey_number'], 
                    'position': row['position']
                }
            ])



    def _matchWithResolvedPlayer(self, cbssports_player_id, full_name, team_id, game_id):
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
                    AND player_id IS NOT NULL
            """ % (cbssports_player_id))
            if prior:
                if len(prior) == 1:
                    data = {
                        'player_id': prior[0]['player_id'],
                        'cbssports_player_id': cbssports_player_id,
                        'game_id': game_id
                    }
                    player_id = prior[0]['player_id']  
                    self.dbobj.insert_or_update('player_cbssports_by_game', [data])

                    return player_id
                else:
                    print "   + cbssports_player_id found with multiple player_ids in prior games: %s" % (cbssports_player_id)
                    logging.debug("PLAYER - %s - cbssports_player_id found with multiple player_ids in prior games: %s" % (self.gamedata['id'], cbssports_player_id))

            else:
                return 0


    def append(self):
        self._parse()

        players_in_game = self.dbobj.query_dict("SELECT pbg.*, p.full_name FROM player_by_game pbg INNER JOIN player p ON p.id = pbg.player_id WHERE pbg.game_id = %s" % (self.gamedata['id']))
        query = self.dbobj.query_dict("SELECT * FROM player_cbssports_by_game WHERE game_id = %s" % (self.gamedata['id']))

        for row in query:
            player_id = self._matchWithResolvedPlayer(row['cbssports_player_id'], row['full_name'], row['team_id'], self.gamedata['id'])
            if player_id > 0:
                player_data = {
                    'player_id': player_id,
                    'game_id': row['game_id'],
                    'jersey_number': row['jersey_number'],
                    'position': row['position']
                }
                self.dbobj.insert_or_update('player_by_game',[player_data])
            if player_id == 0:
                player_list = [(line['player_id'], line['full_name']) for line in players_in_game if line['team_id'] == row['team_id']]
                player_id = find_player.FindPlayer(self.dbobj).matchPlayerByNameApproximate(row['full_name'], player_list)
                if player_id > 0:
                    # Append cbssports player id to an existing player
                    player_data = {
                        'id': player_id,
                        'cbssports_player_id': row['cbssports_player_id']
                    }
                    self.dbobj.insert_or_update('player', [player_data])

                    player_data = {
                        'player_id': player_id,
                        'game_id': row['game_id'],
                        'team_id': row['team_id'],
                        'jersey_number': row['jersey_number'],
                        'position': row['position']
                    }
                    self.dbobj.insert_or_update('player_by_game',[player_data])

                # Attempt to match players in player_by_game with players in cbssports_by_game
                # Match using names first
                # Throw an error/logging/print statement if here exists an unmatched cbssports id
                # Update player to include cbssports_player_id 




    def addNewPlayer(self, cbssports_player_id, full_name, first_name, last_name):
        data = {
            'cbssports_player_id'   : cbssports_player_id,
            'full_name'             : full_name,
            'first_name'            : first_name,
            'last_name'             : last_name
        }
        self.dbobj.insert_or_update('player', [data])
                


            
def resolveNewPlayers(game, filename, dbobj, lgobj):
    obj = PlayerCbsSports(filename + '_players', game, dbobj, lgobj)
    obj.insert()


def appendPlayerKeys(game, filename, dbobj, lgobj):
    obj = PlayerCbsSports(filename + '_players', game, dbobj, lgobj)
    obj.append()
