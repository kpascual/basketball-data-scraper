import MySQLdb
import sys
import datetime
import urllib2
import os

from ..config import constants


LOGDIR_SOURCE = constants.LOGDIR_SOURCE




def saveToFile(filename, body):
    f = open('%s%s' % (LOGDIR_SOURCE, filename),'w')
    f.write(body)
    f.close()

def getSourceDoc(url):
    print "    + %s" % (url)
    response = urllib2.urlopen(url)
    return response.read()


def func_boxscore_cbssports(game):
    # Data comes from shotchart_cbssports file
    return False


def func_shotchart_cbssports(game):
    return getSourceDoc(constants.URL['shotchart_cbssports'] + game['cbssports_game_id']) 


def func_playbyplay_nbacom(game):
    url = constants.URL['playbyplay_nbacom'].replace('<game_id>',str(game['nbacom_game_id']))
    return getSourceDoc(url) 


def func_shotchart_nbacom(game):
    return getSourceDoc(constants.URL['shotchart_nbacom'].replace('<game_id>',str(game['nbacom_game_id']))) 


def func_boxscore_nbacom(game):
    return getSourceDoc(constants.URL['boxscore_nbacom'].replace('<game_id>',str(game['nbacom_game_id']))) 


def func_playbyplay_espn(game):
    return getSourceDoc(constants.URL['playbyplay_espn'].replace('<game_id>',str(game['espn_game_id']))) 


def func_shotchart_espn(game):
    return getSourceDoc(constants.URL['shotchart_espn'].replace('<game_id>',str(game['espn_game_id']))) 


def func_shotchart_wnbacom(game):
    return getSourceDoc(constants.URL['shotchart_wnbacom'].replace('<game_id>',str(game['nbacom_game_id']))) 


def func_playbyplay_statsnbacom(game):
    return getSourceDoc(constants.URL['playbyplay_statsnbacom'].replace('<game_id>',str(game['statsnbacom_game_id']))) 


def func_shotchart_statsnbacom(game):
    return getSourceDoc(constants.URL['shotchart_statsnbacom'].replace('<game_id>',str(game['statsnbacom_game_id']))) 


def func_boxscore_statsnbacom(game):
    return getSourceDoc(constants.URL['boxscore_statsnbacom'].replace('<game_id>',str(game['statsnbacom_game_id']))) 


def func_boxscore_wnbacom(game):
    return getSourceDoc(constants.URL['boxscore_wnbacom'].replace('<game_id>',str(game['nbacom_game_id']))) 


def func_playbyplay_espn_wnba(game):
    return getSourceDoc(constants.URL['playbyplay_espn_wnba'].replace('<game_id>',str(game['espn_game_id']))) 


def func_playbyplay_wnbacom(game):
    return getSourceDoc(constants.URL['playbyplay_wnbacom'].replace('<game_id>',str(game['nbacom_game_id']))) 

def func_shotchart_espn_wnba(game):
    return getSourceDoc(constants.URL['shotchart_espn_wnba'].replace('<game_id>',str(game['espn_game_id']))) 




def getAndSaveFiles(game, files):

    print "+++ SOURCE: %s - %s" % (game['id'], game['abbrev'])

    filenames = {}
    for f in files:
        filename = '%s_%s' % (game['abbrev'],f)
        if not _doesFileExist(filename):
            print "  + %s" % (f)
            body = globals()["func_" + f](game)
            if body is not False:
                saveToFile(filename, body)
                print "    + saved"
            else:
                print "    + passed"
        else:
            print "  + %s found. Skipping." % (f)
        filenames[f] = filename

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
