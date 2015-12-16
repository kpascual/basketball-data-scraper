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

        self.home_players = self._getPlayersInGame(self.game['home_team_id'])
        self.away_players = self._getPlayersInGame(self.game['away_team_id'])


    def clean(self):
        plays = self._parse()
        plays = self._resolveDecisecondsLeft(plays)
        plays = self._addGameId(plays)
        plays = self._resolveTeam(plays)
        plays = self._resolvePlayers(plays)
        #plays = self._resolvePlays(plays)

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

            if play['oftid'] in lookup.keys():
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

            if play['epid'] and int(play['epid']) in lookup.keys() and int(play['epid']) > 0:
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


    def _resolvePlays(self, plays):
        data = []
        patterns = self.dbobj.query_dict("SELECT id, re FROM play_type_statsnbacom ORDER BY priority ASC")


        for play in plays:
            play['play_type_statsnbacom_id'] = 0
            
            for pattern in patterns:
                match = re.match(pattern['re'], play['description'])
                if match:
                    matched_attributes = match.groupdict()
                    if 'player_id' in matched_attributes.keys():
                        player_id = 0
                        # Try last name first, then full name second
                        if play['team_id'] == self.game['home_team_id']:
                            player_list_last_name = [(line['id'], line['last_name']) for line in self.home_players]
                            player_list_full_name = [(line['id'], line['full_name']) for line in self.home_players]
                        elif play['team_id'] == self.game['away_team_id']: 
                            player_list_last_name = [(line['id'], line['last_name']) for line in self.away_players]
                            player_list_full_name = [(line['id'], line['full_name']) for line in self.away_players]

                        player_match = find_player.matchPlayerByNameApproximate(matched_attributes['player_id'], player_list_last_name)
                        if player_match:
                            player_id = player_match
                        else:
                            player_match = find_player.matchPlayerByNameApproximate(matched_attributes['player_id'], player_list_full_name)
                            if player_match:
                                player_id = player_match

                        play['player_id'] = player_id


                    play['play_type_statsnbacom_id'] = pattern['id']
                    #print (play['play_type_statsnbacom_id'], play['description'], match.groupdict())
                    break

            data.append(play)

        return data


    def _getPlayersInGame(self, team_id):
        return self.dbobj.query_dict("""
            SELECT p.id, p.full_name, p.last_name
            FROM player_statsnbacom ps
                INNER JOIN player p ON p.id = ps.player_id
            WHERE ps.game_id = %s AND ps.team_id = %s
        """ % (self.game['id'], team_id))


    def _dumpFile(self, plays):
        f = open(LOGDIR_CLEAN + self.filename,'w')
        play_json = json.dumps(plays)
        f.write(play_json)


def run(game, filename, dbobj):
    Clean(filename, game, dbobj).clean()


