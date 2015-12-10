import json
import find_player
import logging


class Player:

    def __init__(self, filename, gamedata, dbobj, lgobj):
        self.game = gamedata
        self.dbobj = dbobj
        self.lgobj = lgobj
        self.data = json.loads(open(filename,'r').read())
        self.table_name = 'player_nbacom_v2015_by_game'


    def resolveNewPlayers(self):
        data = self._parse()
        self.dbobj.insert_or_update('player_nbacom_v2015_by_game', data)

        self._resolveNewPlayers(data)
        self._updatePlayerByGame()


    def _parse(self):
        data = []

        for key, team_id in [('vls', self.game['away_team_id']), ('hls', self.game['home_team_id'])]:
            for line in self.data['g'][key]['pstsg']:
                newline = {}
                newline['game_id'] = self.game['id']
                newline['team_id'] = team_id
                newline['statsnbacom_player_id'] = line['pid']
                newline['jersey_number'] = line['num']
                newline['position'] = line['pos']
                newline['status'] = line['status']
                newline['first_name'] = line['fn']
                newline['last_name'] = line['ln']
                data.append(newline)

        return data


    def _resolveTeam(self, data):
        away_team = self.dbobj.query_dict("SELECT * FROM team WHERE id = %s" % (self.game['away_team_id']))[0]
        home_team = self.dbobj.query_dict("SELECT * FROM team WHERE id = %s" % (self.game['home_team_id']))[0]

        d = data.copy()
        d['statsnbacom_team_id'] = d['team_id']

        if 'team_city_name' in d.keys():
            d['statsnbacom_team_city'] = d['team_city_name']
            del d['team_city_name']
        if 'team_city' in d.keys():
            d['statsnbacom_team_city'] = d['team_city']
            del d['team_city']
        if 'team_name' in d.keys():
            d['statsnbacom_team_name'] = d['team_name']
            del d['team_name']

        if away_team['nbacom_code'] == data['team_abbreviation'] or away_team['statsnbacom_team_id'] == data['team_id']:
            d['team_id'] = away_team['id']
        elif home_team['nbacom_code'] == data['team_abbreviation'] or home_team['statsnbacom_team_id'] == data['team_id']:
            d['team_id'] = home_team['id']
        else:
            d['team_id'] = 0

        return d

    def _updatePlayerByGame(self):
        data = self.dbobj.query_dict("""
            SELECT 
                player_id,
                team_id,
                game_id,
                position,
                jersey_number
            FROM
                %s
            WHERE
                game_id = %s
                AND player_id IS NOT NULL
                AND player_id > 0
        """ % (self.table_name, self.game['id']))
        self.dbobj.insert_or_update('player_by_game',data)


    def append(self):
        data = self._parse()
        players = self.dbobj.query_dict("""
            SELECT 
                p.id,
                p.full_name,
                pbg.team_id
            FROM player_by_game pbg 
                INNER JOIN player p ON p.id = pbg.player_id
            WHERE
                pbg.game_id = %s
        """ % (self.game['id']))

        for line in data:
            # Match by statsnbacom_player_id
            resolved_player = self.dbobj.query_dict("SELECT id FROM player WHERE statsnbacom_player_id = %s" % (line['statsnbacom_player_id']))
            if resolved_player:
                player_id = resolved_player[0]['id']
            else:
                # Approximate match
                player_list = [(player['id'], player['full_name']) for player in players if player['team_id'] == line['team_id']]
                player_id = find_player.FindPlayer(self.dbobj).matchPlayerByNameApproximate(line['statsnbacom_player_name'], player_list)

            if player_id > 0:
                append_data = {'game_id': self.game['id'], 'statsnbacom_player_id': line['statsnbacom_player_id'], 'player_id': player_id}
                self.dbobj.insert_or_update(self.table_name, [append_data])



    def _resolveNewPlayers(self, data):
        for line in data:
            existing_player = self.dbobj.query_dict("""
                SELECT
                    id
                FROM
                    player
                WHERE
                    statsnbacom_player_id = %s
            """ % (line['statsnbacom_player_id']))
            if existing_player:
                player_id = existing_player[0]['id']
                self.dbobj.insert_or_update(self.table_name,[{
                    'player_id': player_id, 
                    'game_id': self.game['id'], 
                    'statsnbacom_player_id': line['statsnbacom_player_id']
                }])
            else:
                # Check prior player resolutions
                prior = self.dbobj.query_dict("""
                    SELECT
                        player_id
                    FROM
                        %s
                    WHERE
                        player_id IS NOT NULL
                        AND statsnbacom_player_id = %s
                """ % (self.table_name, line['statsnbacom_player_id']))
                if prior:
                    if len(prior) == 1:
                        player_id = prior[0]['player_id']
                        self.dbobj.insert_or_update(self.table_name,[{
                            'player_id': player_id, 
                            'game_id': self.game['id'], 
                            'statsnbacom_player_id': line['statsnbacom_player_id']
                        }])
                    else:
                        print "   + statsnbacom_player_id found with multiple player_ids in prior games: %s" % (line['statsnbacom_player_id'])
                        logging.debug("PLAYER - %s - statsnbacom_player_id found with multiple player_ids in prior games %s" % (self.game['id'], line['statsnbacom_player_id']))
                else:
                    # Insert a new player
                    insert = {
                        'statsnbacom_player_id': line['statsnbacom_player_id'],
                        'full_name': line['first_name'] + ' ' + line['last_name'],
                        'first_name': line['first_name'],
                        'last_name': line['last_name']
                    }
                    self.dbobj.insert_or_update('player',[insert])

                    # Update with new player_id created
                    player = self.dbobj.query_dict("SELECT * FROM player WHERE statsnbacom_player_id = %s" % (line['statsnbacom_player_id']))[0]
                    print "  + Created new player: %s, id: %s" % (player['full_name'], player['id'])
                    update = {
                        'player_id': player['id'],
                        'game_id': self.game['id'],
                        'statsnbacom_player_id': line['statsnbacom_player_id']
                    }
                    self.dbobj.insert_or_update(self.table_name,[update])




def resolveNewPlayers(game, filename, dbobj, lgobj):
    obj = Player(filename, game, dbobj, lgobj)
    obj.resolveNewPlayers()


def appendPlayerKeys(game, filename, dbobj, lgobj):
    obj = Player(filename, game, dbobj, lgobj)
    obj.append()
