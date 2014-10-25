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


logging.basicConfig(filename='etl.log',level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')


def getParamsAutoCurrent():
    files = []
    league_name = False
    try:
        league_name = sys.argv[1]
        dt = sys.argv[2]
        dt = datetime.date(*map(int,dt.split('-')))

        if len(sys.argv) > 3:
            files = sys.argv[3:]
    except:
        dt = datetime.date.today() - datetime.timedelta(days=1)

    league_id = configg.dbobj.query_dict("SELECT id FROM league WHERE name = '%s'" % (league_name))[0]['id']

    args = {'dbobj': configg.dbobj, 'league_id': league_id, 'start_date': dt, 'end_date': dt, 'files': files}
    return args


def getParamsManual():
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

    return {'dbobj': configg.dbobj, 'league_id': league_input, 'league_season_id': league_season_input, 'files': [], 'start_date': start_date_input, 'end_date': end_date_input}


def _verifyLeague(params):
    args = params.copy()
    for arg in ['start_date', 'end_date', 'files']:
        del args[arg]
    lgobj = league.League(**args)
    if not lgobj.obj or not lgobj.league_season:
        return False
    else:
        return lgobj


def run(params):
    step_time = time.time()

    lgobj = _verifyLeague(params)

    if lgobj:
        dt = params['start_date']
        while dt <= params['end_date']:

            print "+++ MASTER ETL - league: %s" % (lgobj.name)
            logging.info("MASTER - starting ETL job - league: %s - date: %s" % (lgobj.name, dt))

            print "+++ League identified: %s" % (str(lgobj.obj))
            print "+++ League season identified: %s" % (str(lgobj.league_season))

            # Choose games
            games = lgobj.getGames(dt)
            print "+++ %s games found" % (len(games))
            files = params['files']

            _scrape(params['dbobj'], games, files)

            time_elapsed = "Total time: %.2f sec" % (time.time() - step_time)
            logging.info(time_elapsed)

            dt = dt + datetime.timedelta(days=1)

    else:
        print "Could not find league. Quitting."


def _scrape(dbobj, games, files):

    # Get source
    gamedata = source.main.go(games, files)

    # Scrape
    extract.main.go(gamedata)
    clean.main.go(gamedata, dbobj)
    load.main.go(gamedata, dbobj)



def main():

    if len(sys.argv) > 1:
        params = getParamsAutoCurrent()
    else:
        params = getParamsManual()

    run(params)


if __name__ == '__main__':
    main()
