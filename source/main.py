import MySQLdb
import sys
import datetime
import urllib2
import os

from config import constants


LOGDIR_SOURCE = constants.LOGDIR_SOURCE




def saveToFile(filename, body):
    f = open('%s%s' % (LOGDIR_SOURCE, filename),'w')
    f.write(body)
    f.close()

def getSourceDoc(url):
    print "    + %s" % (url)
    response = urllib2.urlopen(url)
    return response.read()


def func_boxscore_cbssports(game, url):
    # Data comes from shotchart_cbssports file
    return False


def func_shotchart_cbssports(game, url):
    return getSourceDoc(url + game['cbssports_game_id']) 


def func_playbyplay_nbacom(game, url):
    url = url.replace('<game_id>',str(game['nbacom_game_id'])).replace('<year>',game['season_name'][:4]) 
    return getSourceDoc(url) 


def func_shotchart_nbacom(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['nbacom_game_id'])).replace('<year>',game['season_name'][:4])) 


def func_boxscore_nbacom(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['nbacom_game_id'])).replace('<year>',game['season_name'][:4])) 


def func_playbyplay_espn(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['espn_game_id']))) 


def func_shotchart_espn(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['espn_game_id']))) 


def func_shotchart_wnbacom(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['nbacom_game_id'])).replace('<year>',game['season_name'][:4])) 


def func_playbyplay_statsnbacom(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['statsnbacom_game_id']))) 


def func_shotchart_statsnbacom(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['statsnbacom_game_id']))) 


def func_boxscore_statsnbacom(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['statsnbacom_game_id']))) 


def func_boxscore_wnbacom(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['nbacom_game_id'])).replace('<year>',game['season_name'][:4])) 


def func_playbyplay_espn_wnba(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['espn_game_id']))) 


def func_playbyplay_wnbacom(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['nbacom_game_id']))) 

def func_shotchart_espn_wnba(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['espn_game_id']))) 

def func_playbyplay_espn_ncaam(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['espn_game_id']))) 

def func_shotchart_cbssports_ncaam(game, url):
    return getSourceDoc(url.replace('<game_id>','%s_%s@%s' % (game['date_played'].isoformat().replace('-',''), game['away_team_cbssports_code'], game['home_team_cbssports_code']))) 

def func_boxscore_espn_ncaam(game, url):
    return getSourceDoc(url.replace('<game_id>',str(game['espn_game_id']))) 



def getAndSaveFiles(game, files):

    print "+++ SOURCE: %s - %s" % (game['id'], game['abbrev'])

    filenames = {}
    for f in files:
        filename = '%s_%s' % (game['abbrev'],f['module_name'])
        if not _doesFileExist(filename):
            print "  + %s" % (f['module_name'])
            body = globals()["func_" + f['module_name']](game, f['source_url'])
            if body is not False:
                saveToFile(filename, body)
                print "    + saved"
            else:
                print "    + passed"
        else:
            print "  + %s found. Skipping." % (f['module_name'])
        filenames[f['module_name']] = filename

    return filenames



def _doesFileExist(filename):
    if filename in os.listdir(LOGDIR_SOURCE):
        return True
    else:
        return False


def go(games, files):
    return [(gamedata, getAndSaveFiles(gamedata, files)) for gamedata in games]


if __name__ == '__main__':
    sys.exit(main())
