import re
import datetime
import time
import csv
import json
import logging

import player_resolution.find_player as find_player
from config import constants


LOGDIR_CLEAN = constants.LOGDIR_CLEAN
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT




class Clean:

    def __init__(self, filename, gamedata, dbobj):
        self.filename = filename
        self.gamedata = gamedata
        self.dbobj = dbobj
        self.find_player = find_player.FindPlayer(dbobj)

        # Save the players for each team in this variable -- speed is slow when relying solely on find_player module
        self.players_home = []
        self.players_away = []
        self.players = []




    def cleanAll(self):
        newshots = []

        players = self.getPlayersInGame() 

        shots = self._getShots()
        for shot in shots:
            shot['game_id'] = self.gamedata['id']

            # Translate coordinates
            if shot['team_id'] == self.gamedata['away_team_id']:
                shot['y'] = int(float(shot['y']) * 47 * 10 / 50)
                shot['x'] = int(((float(shot['x'])/2) - 25) * 10 * -1)
            elif shot['team_id'] == self.gamedata['home_team_id']:
                shot['y'] = int((100 - float(shot['y'])) * 47 * 10 / 50)
                shot['x'] = int(((float(shot['x'])/2) - 25) * 10)
            else:
                shot['y'] = -999
                shot['x'] = -999

            # Add player id
            if (int(shot['espn_player_id']), shot['team_id']) in players.keys():
                shot['player_id'] = players[int(shot['espn_player_id']), shot['team_id']]
            else:
                shot['player_id'] = 0

            newshots.append(shot)

        logging.info("CLEAN - shotchart_espn_v2016 - game_id: %s - shot count: %s" % (self.gamedata['id'], len(newshots)))
        self.dumpIntoFile(newshots) 


    def getPlayersInGame(self):
        query = self.dbobj.query_dict("""
            SELECT
                player_id,
                team_id,
                espn_player_id,
                full_name
            FROM
                player_espn_by_game
            WHERE
                game_id = %s
        """ % (self.gamedata['id']))

        players = {}
        for row in query:
            players[(row['espn_player_id'], row['team_id'])] = row['player_id']

        return players


    def _getShots(self):
        data = json.loads(open(LOGDIR_EXTRACT + self.filename, 'r').read())

        return data


    def dumpIntoFile(self, data):
        f = open(LOGDIR_CLEAN + self.filename,'wb')
        f.write(json.dumps(data))


def run(game, filename, dbobj):
    pbpvars = {
        'filename':  filename,
        'gamedata':  game,
        'dbobj'   :  dbobj
    }
    Clean(**pbpvars).cleanAll()



