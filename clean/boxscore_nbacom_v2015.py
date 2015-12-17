import re
import datetime
import time
import json
import logging

from config import constants 


LOGDIR_CLEAN = constants.LOGDIR_CLEAN
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT


class Clean:

    def __init__(self, filename, gamedata, dbobj):
        self.raw_data = open(LOGDIR_EXTRACT + filename,'r').read()
        self.dbobj = dbobj
        self.game = gamedata
        self.filename = filename


    def clean(self):
        data = json.loads(self.raw_data)
        self.parseTeamData(data['g'])
        self.parseGameStats(data['g'])
        self.parsePlayers(data['g'])
        #self.parseOfficials(data)


    def parsePlayers(self, data):
        newdata = []

        for key, team_id in [('vls', self.game['away_team_id']), ('hls', self.game['home_team_id'])]:
            for line in data[key]['pstsg']:
                newline = {}
                newline['team_id'] = team_id
                newline['game_id'] = self.game['id']
                newline['league_season_id'] = self.game['league_season_id']
                newline['player_id'] = self._resolvePlayer(line['pid'])
                newline['fgm'] = line['fgm']
                newline['fga'] = line['fga']
                newline['ftm'] = line['ftm']
                newline['fta'] = line['fta']
                newline['threeptm'] = line['tpm']
                newline['threepta'] = line['tpa']
                newline['rebounds_offensive'] = line['oreb']
                newline['rebounds_defensive'] = line['dreb']
                newline['rebounds'] = line['reb']
                newline['assists'] = line['ast']
                newline['fouls'] = line['pf']
                newline['steals'] = line['stl']
                newline['turnovers'] = line['tov']
                newline['blocks'] = line['blk']
                newline['blocks_against'] = line['blka']
                newline['plus_minus'] = line['pm']
                newline['points'] = line['pts']
                # Deal with time played
                if 'totsec' in line.keys():
                    newline['sec_played'] = line['totsec']
                    newline['deciseconds_played'] = line['totsec'] * 10
                elif 'min' in line.keys():
                    newline['sec_played'] = line['min'] * 60
                    newline['deciseconds_played'] = line['min'] * 60 * 10

                newdata.append(newline)


        self._dumpFile(newdata, self.filename)


    def parseTeamData(self, data):
        newdata = []

        for key, team_id in [('vls', self.game['away_team_id']), ('hls', self.game['home_team_id'])]:
            line = data[key]['tstsg']

            newline = {}
            newline['team_id'] = team_id
            newline['game_id'] = self.game['id']
            newline['fgm'] = line['fgm']
            newline['fga'] = line['fga']
            newline['ftm'] = line['ftm']
            newline['fta'] = line['fta']
            newline['threeptm'] = line['tpm']
            newline['threepta'] = line['tpa']
            newline['rebounds_offensive'] = line['oreb']
            newline['rebounds_defensive'] = line['dreb']
            newline['rebounds'] = line['reb']
            newline['assists'] = line['ast']
            newline['fouls'] = line['pf']
            newline['steals'] = line['stl']
            newline['turnovers'] = line['tov']
            newline['blocks'] = line['blk']
            newline['bench_points'] = line['bpts']
            newline['points_in_paint'] = line['pip']
            newline['points_in_paint_made'] = line['pipm']
            newline['points_in_paint_attempted'] = line['pipa']
            newline['fast_break_points'] = line['fbpts']
            newline['fast_break_points_made'] = line['fbptsm']
            newline['fast_break_points_attempted'] = line['fbptsa']
            newline['second_chance_points'] = line['scp']
            newline['technical_fouls'] = line['tf']
            newline['biggest_lead'] = line['ble']
            newdata.append(newline)

                
        self._dumpFile(newdata, self.filename + '_game_stats_team')


    def parseGameStats(self, data):
        newdata = {}
        newdata['game_id'] = self.game['id']
        newdata['ties'] = data['gsts']['tt']
        newdata['lead_changes'] = data['gsts']['lc']
        newdata['attendance'] = data['at']
        newdata['arena_city'] = data['ac']
        newdata['arena_state'] = data['as']
        newdata['arena_name'] = data['an']
        newdata['duration'] = data['dur']
        newdata['date_utc'] = data['gdtutc']
        newdata['time_utc'] = data['utctm']
        newdata['status'] = data['stt']

        newdata['away_score'] = data['vls']['s']
        newdata['home_score'] = data['hls']['s']

        self._dumpFile([newdata], self.filename + '_game_stats')


    def parseOfficials(self, raw):
        data = []
        for line in raw['resultSets']:
            if line['name'] == 'Officials':
                header = line['headers']
                for row in line['rowSet']:
                    newdata = dict(zip([a.lower() for a in header], row))
                    newdata['statsnbacom_official_id'] = newdata['official_id']
                    newdata['jersey_number'] = newdata['jersey_num']
                    newdata['game_id'] = self.game['id']

                    del newdata['official_id']
                    del newdata['jersey_num']

                    data.append(newdata)

        self._dumpFile(data, self.filename + '_referee')


    def _cleanGameIdKeys(self, data):
        d = data.copy()
        if 'game_id' in d.keys():
            d['statsnbacom_game_id'] = d['game_id']

        d['game_id'] = self.game['id']

        return d


    def _resolveTeam(self, data):
        away_team = self.dbobj.query_dict("SELECT * FROM team WHERE id = %s" % (self.game['away_team_id']))[0]
        home_team = self.dbobj.query_dict("SELECT * FROM team WHERE id = %s" % (self.game['home_team_id']))[0]

        d = data.copy()
        d['statsnbacom_team_id'] = d['team_id']
        d['statsnbacom_team_abbreviation'] = d['team_abbreviation']
        del d['team_abbreviation']

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


    def _removeKeys(self, data):
        newdata = []
        remove_keys = [
            'game_date_est',
            'league_id',
        ]

        for line in data:
            for rk in remove_keys:
                if rk in line.keys():
                    del line[rk]

            newdata.append(line)

        return newdata


    def _convertKeys(self, data):
        newdata = []
        key_conversion = {
            'pts': 'points',
            'reb': 'rebounds',
            'ast': 'assists',
            'blk': 'blocks',
            'stl': 'steals',
            'to': 'turnovers',
            'pf': 'fouls',
            'oreb': 'rebounds_offensive',
            'dreb': 'rebounds_defensive',
            'fg3m': 'threeptm',
            'fg3a': 'threepta',
            'fg3_pct': 'threeptfg',
            'fg_pct': 'fg',
            'ft_pct': 'ft',
            'pts_2nd_chance': 'points_second_chance',
            'pts_paint': 'points_in_paint',
            'pts_fb': 'points_fb',
            'season_id': 'statsnbacom_season_id',
        }

        for line in data:
            for key, value in key_conversion.items():
                if key in line.keys():
                    line[value] = line[key]
                    del line[key]

            newdata.append(line)

        return newdata


    def _resolveDeciseconds(self, data, key_name):
        newdata = []
        for line in data:
            line[key_name] = 0

            if 'min' in line.keys(): 
                if line['min'] is not None:
                    if type(line['min']) is str or type(line['min']) is unicode:
                        minutes, seconds = line['min'].split(':')
                    elif type(line['min']) is int:
                        minutes = line['min']
                        seconds = 0

                    line[key_name] = (int(minutes) * 60 + int(seconds)) * 10

                del line['min']

            newdata.append(line)

        return newdata


    def _resolvePlayer(self, statsnbacom_player_id):

        players = self._getPlayerIdsInGame()
        dict_players = dict([(p['statsnbacom_player_id'],p['id']) for p in players])
        if statsnbacom_player_id in dict_players.keys():
            player_id = dict_players[statsnbacom_player_id]
        else:
            player_id = -1
            logging.info("BOXSCORE_NBACOM_DLEAGUE - game_id: %s - Did not find match by statsnbacom_player_id: %s" % (self.game['id'], newdata['statsnbacom_player_id']))

        return player_id


    def _getPlayerIdsInGame(self):
        return self.dbobj.query_dict("""
            SELECT * 
            FROM player_by_game pbg
                INNER JOIN player p ON p.id = pbg.player_id
            WHERE pbg.game_id = %s
        """ % (self.game['id']))



    def _dumpFile(self, data, filename):
        f = open(LOGDIR_CLEAN + filename,'w')
        data_json = json.dumps(data)
        f.write(data_json)


def run(game, filename, dbobj):
    Clean(filename, game, dbobj).clean()


