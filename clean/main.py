import re
import datetime
import time
import sys
import os
import logging
import importlib


from config import constants

LOGDIR_CLEAN = constants.LOGDIR_CLEAN
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT


def main():
    try:
        dt = sys.argv[1]
    except:
        dt = datetime.date.today() - datetime.timedelta(days=1)
        dt = dt.isoformat()
    dt = dt.replace('-','')  
 
    list_files = os.listdir(LOGDIR_EXTRACT)
    list_cbssports = []
    list_espn = []
    list_cbssports_players = []
   
    for l in list_files:
        if re.search('.*%s.*' % dt,l) and re.search('espn',l):
            list_espn.append(l)

        if re.search('.*%s.*' % dt,l) and re.search('_shotchart',l):
            list_cbssports.append(l)

        if re.search('.*%s.*' % dt,l) and re.search('_players',l):
            list_cbssports_players.append(l)

    espn_playbyplay.main(list_espn)
    #cleanCBSSportsPlayers(list_cbssports_players)



def go(tuple_games_and_files, dbobj, lgobj, league_season_id):
    resolution_strategy = lgobj.getPlayerResolveStrategy(league_season_id)

    for gamedata, files in tuple_games_and_files:

        print "+++ CLEAN: %s - %s" % (gamedata['id'], gamedata['abbrev'])

        # add a player resolution folder, then have the resolution strategy call the correct module, and let them implement these details
        print "+++ CLEAN: PLAYER primary"
        primary_module = resolution_strategy['primary']
        
        if primary_module in files.keys():
            print "   + %s" % (primary_module)
            lib = importlib.import_module('clean.player_resolution.%s' % (primary_module))
            getattr(lib,'resolveNewPlayers')(gamedata, LOGDIR_EXTRACT + files[primary_module], dbobj, lgobj)

        # Secondary
        print "+++ CLEAN: PLAYER secondary"
        for module in resolution_strategy['secondary']:
            if module in files.keys():
                print "   + %s" % (module)
                lib = importlib.import_module('clean.player_resolution.%s' % (module))
                getattr(lib,'appendPlayerKeys')(gamedata, LOGDIR_EXTRACT + files[module], dbobj, lgobj)

        print "+++ CLEAN: game results"
        for module, filename in files.items():
            print "   + %s" % (module)
            step_time = time.time()
            lib = importlib.import_module('clean.%s' % (module))
            getattr(lib,'run')(gamedata, filename, dbobj)

            logging.info("CLEAN - %s - game_id: %s - : time_elapsed %.2f" % (module, gamedata['id'], time.time() - step_time))



if __name__ == '__main__':
    sys.exit(main())
