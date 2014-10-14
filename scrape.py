import sys
import time
import datetime
import MySQLdb
import os
import logging

from config import constants
import configg
import league
import source.main
import extract.main
import clean.main
import load.main


LOGDIR_SOURCE = constants.LOGDIR_SOURCE
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT

logging.basicConfig(filename='etl.log',level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')


class Scrape:
    def __init__(self, dbobj, league):
        league_map = {
            'nba': 1,
            'wnba': 2,
            'fiba': 3
        }
        self.league = league
        self.league_season_id = self._getLeagueSeason({league_id: league_map[league]})


    def _scrape(self):
        pass


    def run(self):
        pass

    def _getLeagueSeason(self, params):
        pass

    def _getModules(self):
        module_map = {
            'nba': [
                'boxscore_nbacom',
                'boxscore_cbssports',
                'playbyplay_espn',
                'playbyplay_nbacom',
                'shotchart_cbssports',
                'shotchart_espn',
                'shotchart_nbacom',
                'playbyplay_statsnbacom',
                'shotchart_statsnbacom',
                'boxscore_statsnbacom'
            ],
            'wnba': [
                'boxscore_nbacom',
                'playbyplay_espn',
                'playbyplay_nbacom',
                'shotchart_espn',
                'shotchart_wnbacom'
            ]    
            
        }

        return module_map(self.league)



def scrapeAuto(league_name, dt, files = None):
    step_time = time.time()

    config_no_pw = configg.dbobj.getCredentials()
    

    # MAIN ETL PROCESS
    print "+++ MASTER ETL - league: %s - database: %s" % (league_name, config_no_pw)
    logging.info("MASTER - starting ETL job - league: %s - date: %s - database: %s" % (league_name, dt, config_no_pw))

    args = {'dbobj': configg.dbobj, 'league_name': league_name, 'dt': dt, 'files': files}
    scrape(**args)

    time_elapsed = "Total time: %.2f sec" % (time.time() - step_time)
    logging.info(time_elapsed)


def scrape(dbobj, dt, files, league_name = '', league_id = 0, league_season_id = 0):

    # Get league-level info from user-input
    args = {'dbobj': dbobj, 'name': league_name, 'league_id': league_id, 'league_season_id': league_season_id}
    lgobj = league.League(**args)

    if not lgobj.obj or not lgobj.league_season:
        print "Could not find league. Quitting."
        return False
    else:
        print "+++ League identified: %s" % (str(lgobj.obj))
        print "+++ League season identified: %s" % (str(lgobj.league_season))

        # Choose games
        games = lgobj.getGames(dt)
        print "+++ %s games found" % (len(games))
        if not files:
            files = lgobj.getModules()

        # Get source
        gamedata = source.main.go(games, files)

        # Scrape
        extract.main.go(gamedata)
        clean.main.go(gamedata, dbobj)
        load.main.go(gamedata, dbobj)


# League-specific methods

def run(league = '', league_id = 0, league_season_id = 0, start_date = 0, end_date = 0, date = 0):
    pass



def backfill(league = '', league_id = 0, league_season_id = 0, start_date = 0, end_date = 0, date = 0):
    pass


def menu():
    # Choose league
    leagues = configg.dbobj.query_dict("SELECT * FROM league")
    print 'ID:   League Name'
    for l in leagues:
        print '%s:   %s' % (l['id'], l['name'])
    league_input = raw_input('Choose league by ID: ')
    league_input = int(league_input)

    # Choose league season
    league_seasons = configg.dbobj.query_dict("SELECT ls.id, s.name as season_name FROM league_season ls INNER JOIN league l ON l.id = ls.league_id INNER JOIN season s ON s.id = ls.season_id WHERE l.id = %s" % (league_input))
    print 'ID:   Season Name'
    for ls in league_seasons:
        print '%s:   %s' % (ls['id'], ls['season_name'])
    league_season_input = raw_input('Choose season: ')

    # Choose dates to scrape
    start_date_input = raw_input('Choose START date (yyyy-mm-dd or blank for today\'s date of %s): ' % (datetime.date.today()))
    if not start_date_input:
        start_date_input = datetime.date.today()
        end_date_input = start_date_input
    else:
        start_date_input = datetime.datetime.strptime(start_date_input, '%Y-%m-%d').date()
        end_date_input = raw_input('Choose END date (yyyy-mm-dd or blank for START date): ')
        if not end_date_input:
            end_date_input = start_date_input
        else:
            end_date_input = datetime.datetime.strptime(end_date_input, '%Y-%m-%d').date()


    files = []
    dt = start_date_input
    while dt <= end_date_input:
        args = {'dbobj': configg.dbobj, 'league_id': league_input, 'dt': dt, 'files': files, 'league_season_id': league_season_input}
        scrape(**args)

        dt = dt + datetime.timedelta(days=1)


def main():

    files = []
    try:
        league_name = sys.argv[1]
        dt = sys.argv[2]
        dt = datetime.date(*map(int,dt.split('-')))

        if len(sys.argv) > 3:
            files = sys.argv[3:]
    except:
        dt = datetime.date.today() - datetime.timedelta(days=1)

    print dt
    if len(sys.argv) > 1:
        scrapeAuto(league_name, dt, files)
    else:
        menu()


if __name__ == '__main__':
    main()
