from bs4 import BeautifulSoup
import csv
import os
import logging
import datetime
import re
import difflib
import json
from config import db
from config import constants 

import shotchart_espn


LOGDIR_CLEAN = constants.LOGDIR_CLEAN
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT


class Clean(shotchart_espn.Clean):

    def __init__(self, filename, gamedata, dbobj):
        self.xml = open(LOGDIR_EXTRACT + filename,'r').read()
        self.filename = filename
        self.soup = BeautifulSoup(self.xml, 'lxml')
        self.date_played = filename.replace(LOGDIR_EXTRACT,'')[:10]
        self.gamedata = gamedata
        self.db = dbobj



def run(game, filename, dbobj):
    Clean(filename, game, dbobj).cleanAll()



def main():

    files = [
        '2011-12-25_LAC@GS_shotchart_espn',
        '2011-12-25_MIA@DAL_shotchart_espn',
        '2011-12-25_BOS@NY_shotchart_espn',
        '2011-12-25_CHI@LAL_shotchart_espn',
        '2011-12-25_ORL@OKC_shotchart_espn'
    ]

    files = [f for f in os.listdir('../../logs/extract') if 'shotchart_espn' in f]

    f = '2011-12-25_LAC@GS_shotchart_espn'
    gamedata = db.nba_query_dict("SELECT * FROM game WHERE id = 1267")[0]
    obj = ShotChartEspn(f, gamedata)
    obj.cleanAll()



if __name__ == '__main__':
    main()
