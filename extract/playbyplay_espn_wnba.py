from config import constants
from bs4 import BeautifulSoup
#from BeautifulSoup import BeautifulSoup
import csv
import re
import logging
from config import db

import playbyplay_espn


LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT
LOGDIR_SOURCE = constants.LOGDIR_SOURCE

class Extract(playbyplay_espn.Extract):

    def __init__(self, html, filename, gamedata):
        self.html = html
        self.gamedata = gamedata
        self.game_name = self.gamedata['abbrev']
        self.filename = filename

        self.home_team_city = self.gamedata['home_team_city']
        self.away_team_city = self.gamedata['away_team_city']



def run(game, filename):
    params = {
        'html': open(LOGDIR_SOURCE + filename,'r').read(),
        'filename':  filename,
        'gamedata':  game
    }
    Extract(**params).extractAndDump()


def main():
    dbobj = db.Db(db.dbconn_prod)
    game = dbobj.query_dict("""
        SELECT g.*, home_team.city home_team_city, away_team.city away_team_city 
        FROM game g 
            INNER JOIN team home_team on home_team.id = g.home_team_id
            INNER JOIN team away_team on away_team.id = g.away_team_id
        WHERE g.id = 1
            AND g.should_fetch_data = 1
    """)[0]
    filename = game['abbrev'] + '_playbyplay_espn'

    obj = Extract(open(LOGDIR_SOURCE + filename,'r').read(),filename ,game)
    data = obj._getData()
    for row in data:
        print row


if __name__ == '__main__':
    main()

