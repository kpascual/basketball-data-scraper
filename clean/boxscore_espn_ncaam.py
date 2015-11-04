import csv
import json
import logging
import difflib
import shutil

import player_resolution.find_player as find_player

from config import constants 
import config.constants



LOGDIR_CLEAN = constants.LOGDIR_CLEAN
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT


class Clean:
    def __init__(self, filename, gamedata, dbobj):
        self.gamedata = gamedata
        self.away_team = self.gamedata['away_team_id']
        self.home_team = self.gamedata['home_team_id']
        self.game_name = self.gamedata['abbrev']
        self.game_id = self.gamedata['id']
        self.date_played = self.gamedata['date_played']
        self.dbobj = dbobj
        self.filename = filename

        self.data = [line for line in csv.reader(open(LOGDIR_EXTRACT + self.filename,'r'),delimiter=',',lineterminator='\n')]
        self.data = json.loads(open(LOGDIR_EXTRACT + self.filename,'r').read())


    def _getPlayerIdsInGame(self):
        return self.dbobj.query_dict("""
            SELECT * 
            FROM player_by_game pbg
                INNER JOIN player p ON p.id = pbg.player_id
            WHERE pbg.game_id = %s
        """ % (self.gamedata['id']))


    def clean(self):
        data = self.resolvePlayers()
        self.dumpIntoFile(data)

        self.copyGameStats()


    def resolvePlayers(self):
        players = self._getPlayerIdsInGame()
        player_list = [(p['id'], p['full_name']) for p in players]
        dict_player_espn_ids = dict([(p['espn_player_id'],p['id']) for p in players])

        boxscore_data = []
        for (team_id, player_name, espn_id, minutes, fg, threept, ft, oreb, dreb, reb, ast, stl, blk, tov, fouls, points) in self.data:
            player_id = 0
            if espn_id > 0 and long(espn_id) in dict_player_espn_ids.keys():
                player_id = dict_player_espn_ids[long(espn_id)]
            
            if player_id == 0:
                if espn_id == 0:
                    player_id = find_player.FindPlayer(self.dbobj).matchPlayerByNameApproximate(player_name, player_list)

            if player_id > 0:
                newdata = {
                    'player_id': player_id,
                    'team_id': team_id,
                    'game_id': self.game_id,
                    'time_played': minutes,
                    'deciseconds_played': int(minutes) * 60 * 10,
                    'fgm': fg.split('-')[0],
                    'fga': fg.split('-')[1],
                    'threeptm': threept.split('-')[0],
                    'threepta': threept.split('-')[1],
                    'ftm': ft.split('-')[0],
                    'fta': ft.split('-')[1],
                    'rebounds_offensive': oreb,
                    'rebounds_defensive': dreb,
                    'rebounds': reb,
                    'assists': ast,
                    'steals': stl,
                    'blocks': blk,
                    'turnovers': tov,
                    'fouls': fouls,
                    'points': points
                }
                boxscore_data.append(newdata)
            else:
                print "   + CLEAN - boxscore_espn - cant match player - %s" % (player_name)
                logging.warning("CLEAN - boxscore_cbssports - game_id: %s - cant match player: '%s'" % (self.gamedata['id'],player_name))
                player_id = -1

        return boxscore_data


    def dumpIntoFile(self, data):
        f = open(LOGDIR_CLEAN + self.filename,'wb')
        f.write(json.dumps(data))


    def copyGameStats(self):
        shutil.copyfile(LOGDIR_EXTRACT + self.filename + '_game_stats', LOGDIR_CLEAN + self.filename + '_game_stats')
         

def run(game, filename, dbobj):
    Clean(filename, game, dbobj).clean()
