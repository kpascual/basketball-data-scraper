import sys
import time
import datetime
import os
import logging
import json
import sqlite3

from config import constants
import configg
import league
import source.main
import extract.main
import clean.main
import load.main


logging.basicConfig(filename='etl.log',level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

conn = sqlite3.connect("metadata/leagues.db")
conn.row_factory = sqlite3.Row
curs = conn.cursor()


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

    curs.execute("SELECT id FROM league WHERE name = ?", (league_name))
    league_id = curs.fetchone()[0]

    args = {'league_id': league_id, 'start_date': dt, 'end_date': dt, 'files': files}
    return args


def getParamsManual():
    # Choose league
    curs.execute("SELECT * FROM league")
    leagues = []
    lgs = curs.fetchall()
    for lg in lgs:
        leagues.append(dict(zip(lg.keys(), lg)))
    print leagues

    print 'ID:   League Name'
    for l in leagues:
        print '%s:   %s' % (l['id'], l['name'])
    league_input = raw_input('Choose league by ID: ')
    league_input = int(league_input)

    # Choose league season
    lgobj = league.League(league_id=league_input)
    league_seasons = lgobj.getLeagueSeasons()
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

    print "+++ Database name: %s" % (str(configg.db_params['db']))
    return {'league_id': league_input, 'league_season_id': league_season_input, 'files': [], 'start_date': start_date_input, 'end_date': end_date_input}


def _verifyLeague(params):
    args = params.copy()
    for arg in ['start_date', 'end_date', 'files', 'league_season_id']:
        del args[arg]
    lgobj = league.League(**args)
    if not lgobj.obj:
        return False
    else:
        return lgobj


def run(params):
    step_time = time.time()

    lgobj = _verifyLeague(params)

    if lgobj:
        dt = params['start_date']
        while dt <= params['end_date']:

            print "+++ MASTER ETL - league: %s, date: %s" % (lgobj.name, dt)
            logging.info("MASTER - starting ETL job - league: %s - date: %s" % (lgobj.name, dt))

            print "+++ League identified: %s" % (str(lgobj.obj))

            # Choose games
            games = lgobj.getGames(dt, params['league_season_id'])
            print "+++ %s games found" % (len(games))
            if not params['files']:
                files = lgobj.getModules(params['league_season_id'])
            else: 
                files = params['files']

            _scrape(games, files, lgobj)

            time_elapsed = "Total time: %.2f sec" % (time.time() - step_time)
            logging.info(time_elapsed)

            dt = dt + datetime.timedelta(days=1)

    else:
        print "Could not find league. Quitting."


def _scrape(games, files, lgobj):

    # Get source
    # Scrape
    gamedata = source.main.go(games, files)
    extract.main.go(gamedata)

    # Clean
    #clean.main.go(gamedata, dbobj, lgobj)
    #load.main.go(gamedata, dbobj)



def main():

    if len(sys.argv) > 1:
        params = getParamsAutoCurrent()
    else:
        params = getParamsManual()

    run(params)


if __name__ == '__main__':
    main()
