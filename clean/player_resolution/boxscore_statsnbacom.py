import json
import find_player
import logging


class Player:

    def __init__(self, filename, gamedata, dbobj, lgobj):
        self.game = gamedata
        self.dbobj = dbobj
        self.lgobj = lgobj
        self.data = json.loads(open(filename,'r').read())


    def resolveNewPlayers(self):
        data = self._parse()
        self._resolveNewPlayers(data)
        self._updatePlayerByGame()


    def _parse(self):
        data = []
        for line in self.data['resultSets']:
            if line['name'] == 'PlayerStats':
                for stat in line['rowSet']:
                    rawdata = dict(zip([a.lower() for a in line['headers']], stat))
                    rawdata = self._resolveTeam(rawdata)

                    newdata = {
                        'game_id': self.game['id'],
                        'team_id': rawdata['team_id'],
                        'statsnbacom_team_id': rawdata['statsnbacom_team_id'],
                        'statsnbacom_team_abbreviation': rawdata['team_abbreviation'],
                        'statsnbacom_team_city': rawdata['statsnbacom_team_city'],
                        'statsnbacom_player_id': rawdata['player_id'],
                        'statsnbacom_player_name': rawdata['player_name']
                    }
                    data.append(newdata)

        self.dbobj.insert_or_update('player_statsnbacom_by_game',data)

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
                game_id
            FROM
                player_statsnbacom_by_game
            WHERE
                game_id = %s
                AND player_id IS NOT NULL
                AND player_id > 0
        """ % (self.game['id']))
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
                self.dbobj.insert_or_update('player_statsnbacom_by_game', [append_data])



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
                self.dbobj.insert_or_update('player_statsnbacom_by_game',[{'player_id': player_id, 'game_id': self.game['id'], 'statsnbacom_player_id': line['statsnbacom_player_id']}])
            else:
                # Check prior player resolutions
                prior = self.dbobj.query_dict("""
                    SELECT
                        player_id
                    FROM
                        player_statsnbacom_by_game
                    WHERE
                        player_id IS NOT NULL
                        AND statsnbacom_player_id = %s
                """ % (line['statsnbacom_player_id']))
                if prior:
                    if len(prior) == 1:
                        player_id = prior[0]['player_id']
                        self.dbobj.insert_or_update('player_statsnbacom_by_game',[{'player_id': player_id, 'game_id': self.game['id'], 'statsnbacom_player_id': line['statsnbacom_player_id']}])
                    else:
                        print "   + statsnbacom_player_id found with multiple player_ids in prior games: %s" % (line['statsnbacom_player_id'])
                        logging.debug("PLAYER - %s - statsnbacom_player_id found with multiple player_ids in prior games %s" % (self.game['id'], line['statsnbacom_player_id']))
                else:
                    # Insert a new player
                    insert = {
                        'statsnbacom_player_id': line['statsnbacom_player_id'],
                        'full_name': line['statsnbacom_player_name'],
                        'first_name': line['statsnbacom_player_name'].split(' ')[0],
                        'last_name': ' '.join(line['statsnbacom_player_name'].split(' ')[1:])
                    }
                    self.dbobj.insert_or_update('player',[insert])

                    # Update with new player_id created
                    player = self.dbobj.query_dict("SELECT * FROM player WHERE statsnbacom_player_id = %s" % (line['statsnbacom_player_id']))[0]
                    print "  + Created new player: %s, id: %s" % (player['full_name'], player['id'])
                    update = {
                        'game_id': self.game['id'],
                        'player_id': player['id'],
                        'statsnbacom_player_id': line['statsnbacom_player_id']
                    }
                    self.dbobj.insert_or_update('player_statsnbacom_by_game',[update])




def resolveNewPlayers(game, filename, dbobj, lgobj):
    obj = Player(filename, game, dbobj, lgobj)
    obj.resolveNewPlayers()


def appendPlayerKeys(game, filename, dbobj, lgobj):
    obj = Player(filename, game, dbobj, lgobj)
    obj.append()
