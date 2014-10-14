import re
import datetime
import csv
from bs4 import BeautifulSoup
import os
import json

import boxscore_nbacom

from config import db
from config import constants 


LOGDIR_CLEAN = constants.LOGDIR_CLEAN
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT


class CleanBoxScore(boxscore_nbacom.CleanBoxScore):

    def __init__(self, filename, gamedata, dbobj):
        self.xml = open(LOGDIR_EXTRACT + filename,'r').read()
        self.soup = BeautifulSoup(self.xml, 'lxml')
        self.gamedata = gamedata
        self.filename = filename
        self.db = dbobj



def run(game, filename, dbobj):
    CleanBoxScore(filename,game, dbobj).clean()


def main():

    files = [f for f in os.listdir(LOGDIR_EXTRACT) if '2011-12' in f and 'boxscore' in f]
    f = '2012-01-18_OKC@WAS_boxscore_nbacom'

    gamedata = db.nba_query_dict("SELECT * FROM game where date_played <= '2012-02-10'") 
    dbobj = db.Db(db.dbconn_nba)

    for game in gamedata:
        #print game['abbrev']
        filename = game['abbrev'] + '_boxscore_nbacom'

        obj = CleanBoxScore(filename, game, dbobj)
        result = obj.getGameInfo()
        

    
       
    

if __name__ == '__main__':
    main()
