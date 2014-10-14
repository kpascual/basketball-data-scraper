import re
import datetime
import time
import csv
import difflib
import json
import logging

import find_player
import resolve
from config import config
from config import db
from config import constants 

import playbyplay_espn


LOGDIR_CLEAN = constants.LOGDIR_CLEAN
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT




class Clean(playbyplay_espn.Clean):

    def __init__(self, filename, gamedata, dbobj):
        self.filename = filename
        self.gamedata = gamedata
        self.away_team_id = self.gamedata['away_team_id']
        self.home_team_id = self.gamedata['home_team_id']
        self.game_name = self.gamedata['abbrev']
        self.game_id = self.gamedata['id']
        self.date_played = self.gamedata['date_played']
        self.db = dbobj
        self.find_player = find_player.FindPlayer(dbobj)

        # Save the players for each team in this variable -- speed is slow when relying solely on find_player module
        self.players_home = []
        self.players_away = []
        self.players = []
        self.known_plays = []
        self.home_team = {}
        self.away_team = {}

        self.plays = ''



def run(game, filename, dbobj):
    pbpvars = {
        'filename':  filename,
        'gamedata':  game,
        'dbobj'   :  dbobj
    }
    Clean(**pbpvars).cleanAll()



def main():
    dbobj = db.Db(config.dbconn_prod_nba)
    game = dbobj.query_dict("SELECT * FROM game WHERE id = 5378")[0]
    obj = Clean(game['abbrev'] + '_playbyplay_espn',game, dbobj)
    obj._clean()


if __name__ == '__main__':
    main()
