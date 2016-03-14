import logging
import find_player
import json

class PlayerEspn: 
    def __init__(self, filename, gamedata, dbobj, lgobj):

        self.gamedata = gamedata
        self.data = json.loads(open(filename,'r').read())
        self.date_played = self.gamedata['date_played']
        self.dbobj = dbobj
        self.lgobj = lgobj


    def _parse(self):

        for row in self.data:

            insert_data = {
                'game_id': self.gamedata['id'],
                'espn_player_id': row['espn_player_id'],
                'url': 'unknown',
                'team_id': row['team_id'],
                'full_name': row['full_name'],
                'first_name': row['full_name'].split(' ')[0],
                'last_name': ' '.join(row['full_name'].split(' ')[1:]),
            }
            self.dbobj.insert_or_update('player_espn_by_game', [insert_data])



    def insert(self):
        self._parse()

        players = self.dbobj.query_dict("SELECT * FROM player_espn_by_game WHERE game_id = %s" % (self.gamedata['id']))

        for player in players:
        
            existing_player = self.dbobj.query_dict("""
                SELECT
                    id
                FROM
                    player
                WHERE
                    espn_player_id = %s
            """ % (player['espn_player_id']))
            if existing_player:
                player_id = existing_player[0]['id']
                newdata = player.copy()
                newdata['player_id'] = player_id
                self.dbobj.insert_or_update('player_espn_by_game', [newdata])
            else:
                # Find a player resolution from prior games
                prior = self.dbobj.query_dict("""
                    SELECT DISTINCT espn_player_id, url, player_id
                    FROM player_espn_by_game
                    WHERE 
                        espn_player_id = %s
                        AND player_id IS NOT NULL
                """ % (player['espn_player_id']))
                if prior:
                    if len(prior) == 1:
                        data = {
                            'player_id': prior[0]['player_id'],
                            'espn_player_id': player['espn_player_id'],
                            'url': 'unknown',
                            'game_id': self.gamedata['id']
                        }
                        player_id = prior[0]['player_id']  
                        self.dbobj.insert_or_update('player_espn_by_game', [data])
                    else:
                        print "   + espn_player_id found with multiple player_ids in prior games: %s" % (player['espn_player_id'])
                        logging.debug("PLAYER - %s - espn_player_id found with multiple player_ids in prior games %s" % (self.gamedata['id'], player['espn_player_id']))

                else:
                    # Insert new player
                    insert_data = {
                        'espn_player_id': player['espn_player_id'],
                        'espn_player_url': 'unknown',
                        'full_name': player['full_name'],
                        'first_name': player['first_name'],
                        'last_name': player['last_name']
                    }
                    self.dbobj.insert_or_update('player',[insert_data])

                    # Update with player_id
                    data = self.dbobj.query_dict("SELECT id FROM player WHERE espn_player_id = %s " % (player['espn_player_id']))
                    update_data = {
                        'player_id': data[0]['id'],
                        'espn_player_id': player['espn_player_id'],
                        'url': 'unknown',
                        'game_id': self.gamedata['id']
                    }
                    self.dbobj.insert_or_update('player_espn_by_game',[update_data])

                    logging.debug("PLAYER - game_id: %s - Creating new player: %s" % (self.gamedata['id'], player['full_name']))
                    print "  + Creating new player: %s" % (player['full_name'])

        self._updatePlayerByGame()



    def append(self):
        self._parse()
        players = self.dbobj.query_dict("""
            SELECT 
                p.id,
                p.full_name,
                pbg.team_id
            FROM player_by_game pbg 
                INNER JOIN player p ON p.id = pbg.player_id
            WHERE
                pbg.game_id = %s
        """ % (self.gamedata['id']))

        for row in self.data:
            team_id = row['team_id']
            player_name = row['full_name']
            espn_player_id = row['espn_player_id']

            player_list = [(line['id'], line['full_name']) for line in players if line['team_id'] == long(team_id)]
            player_id = find_player.FindPlayer(self.dbobj).matchPlayerByNameApproximate(player_name, player_list)
            if player_id > 0:
                append_data = {'game_id': self.gamedata['id'], 'espn_player_id': espn_player_id, 'player_id': player_id, 'url': 'unknown'}
                self.dbobj.insert_or_update('player_espn_by_game', [append_data])


    def _updatePlayerByGame(self):
        data = self.dbobj.query_dict("""
            SELECT 
                player_id,
                team_id,
                game_id
            FROM
                player_espn_by_game
            WHERE
                game_id = %s
                AND player_id IS NOT NULL
                AND player_id > 0
        """ % (self.gamedata['id']))
        self.dbobj.insert_or_update('player_by_game',data)


    def addNewPlayer(self, data):
        self.dbobj.insert_or_update('player', [data])
                


            
def resolveNewPlayers(game, filename, dbobj, lgobj):
    obj = PlayerEspn(filename + '_players', game, dbobj, lgobj)
    obj.insert()


def appendPlayerKeys(game, filename, dbobj, lgobj):
    obj = PlayerEspn(filename + '_players', game, dbobj, lgobj)
    obj.append()
