import re
import datetime
import time
import json
import player_resolution.find_player as find_player
import logging

from config import config
from config import constants 


LOGDIR_CLEAN = constants.LOGDIR_CLEAN
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT
LOGDIR_SOURCE = constants.LOGDIR_SOURCE


class Clean:

    def __init__(self, filename, gamedata, dbobj):
        self.raw_data = open(LOGDIR_EXTRACT + filename,'r').read()
        self.dbobj = dbobj
        self.game = gamedata
        self.filename = filename



    def clean(self):
        plays = self._parse()
        plays = self._resolveDecisecondsLeft(plays)
        plays = self._addGameId(plays)
        plays = self._resolveTeam(plays)
        plays = self._resolvePlayers(plays)

        self._dumpFile(plays)


    def _parse(self):
        plays = []

        data = json.loads(self.raw_data)
        for period, line in sorted(data.items(), key=lambda x: x[0]):
            for play in line['g']['pla']:
                play['period'] = period

                mappings = {
                    'vs': 'away_score',
                    'hs': 'home_score',
                    'locX': 'x',
                    'de': 'description',
                    'evt': 'event_index'
                }
                for nbacom_key, vorped_key in mappings.items():
                    play[vorped_key] = play[nbacom_key]
                    del play[nbacom_key]

                # Alter the y-value, as it's in relation to the basket
                play['y'] = int(play['locY']) + 50
                del play['locY']

                plays.append(play)

        return plays

                # play['oftid'] - offensive team id, translate
                # play['cl'] - clock, in mm:ss
                # play['epid'] - appears to be supporting player (substitution or assists)
                # play['de'] - text description of play
                # play['pid'] - player id
                # play['mtype']
                # play['etype'] - appears to be a simplistic play type
                # play['opt1']
                # play['vs'] - visitor/away score?
                # play['hs'] - home score?
                # play['tid'] - team id
                # play['locX'] - x location
                # play['locY'] - y location
                # play['evt'] - in-game play index
                # play['opid'] - opposing player id - the acted upon player (my player2_id, usually)
                # play['opt2']

        return plays


    def _resolveTeam(self, plays):
        data = []
        teams = self.dbobj.query_dict("SELECT id, statsnbacom_team_id FROM team WHERE id IN (%s, %s)" % (self.game['away_team_id'], self.game['home_team_id']))
        lookup = dict((team['statsnbacom_team_id'], team['id']) for team in teams)
        for play in plays:
            if play['tid'] in lookup.keys():
                play['team_id'] = lookup[play['tid']]

            if 'oftid' in play.keys() and play['oftid'] in lookup.keys():
                play['off_team_id'] = lookup[play['oftid']]

            data.append(play)

        return data


    def _resolvePlayers(self, plays):
        data = []
        players = self.dbobj.query_dict("SELECT player_id, statsnbacom_player_id FROM player_nbacom_v2015_by_game WHERE game_id = %s" % (self.game['id']))
        lookup = dict((player['statsnbacom_player_id'], player['player_id']) for player in players)
        for play in plays:
            if play['pid'] in lookup.keys() and play['pid'] > 0:
                play['player_id'] = lookup[play['pid']]

            if 'epid' in play.keys() and play['epid'] and int(play['epid']) in lookup.keys() and int(play['epid']) > 0:
                play['secondary_player_id'] = lookup[int(play['epid'])]

            if play['opid'] and int(play['opid']) in lookup.keys() and int(play['opid']) > 0:
                play['opposing_player_id'] = lookup[int(play['opid'])]

            data.append(play)

        return data



    def _addGameId(self, plays):
        data = []
        for play in plays:
            play['game_id'] = self.game['id']
            data.append(play)

        return data


    def _resolveDecisecondsLeft(self, plays):
        data = []
        for play in plays:
            if ':' in play['cl']:
                time_left = play['cl'].split(':')        
            else:
                time_left = (play['cl'], 0)
            play['deciseconds_left'] = (int(time_left[0]) * 60 + float(time_left[1])) * 10
            data.append(play)

        return data


    def _dumpFile(self, plays):
        f = open(LOGDIR_CLEAN + self.filename,'w')
        play_json = json.dumps(plays)
        f.write(play_json)


def run(game, filename, dbobj):
    Clean(filename, game, dbobj).clean()


