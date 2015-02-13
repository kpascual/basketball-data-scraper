import re
import datetime
import time
import sys
import os
import logging
import importlib

import player

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



def go(tuple_games_and_files, dbobj, lgobj):
    resolution_strategy = lgobj.getPlayerResolveStrategy()

    for gamedata, files in tuple_games_and_files:

        print "+++ CLEAN: %s - %s" % (gamedata['id'], gamedata['abbrev'])

        # add a player resolution folder, then have the resolution strategy call the correct module, and let them implement these details
        print "+++ CLEAN: primary"
        module = resolution_strategy['primary']
        
        if module in files.keys():
            lib = importlib.import_module('clean.player_resolution.%s' % (module))
            getattr(lib,'resolveNewPlayers')(gamedata, LOGDIR_EXTRACT + files[module], dbobj, lgobj)

        # Secondary
        print "+++ CLEAN: secondary"
        # for module in resolution_strategy['secondary']:
        #   lib = importlib.import_module('clean.player_resolution.%s' % (module))
        #   getattr(lib,'appendPlayerKeys')(gamedata, filename, dbobj)

        """
        print "  + Player database"
        if 'boxscore_nbacom' in files:
            obj = player.PlayerNbaCom(LOGDIR_EXTRACT + files['boxscore_nbacom'], gamedata, dbobj)
            obj.resolveNewPlayers()
    
        if 'boxscore_wnbacom' in files:
            obj = player.PlayerNbaCom(LOGDIR_EXTRACT + files['boxscore_wnbacom'], gamedata, dbobj)
            obj.resolveNewPlayers()
    
        if 'shotchart_cbssports' in files:
            obj = player.PlayerCbsSports(LOGDIR_EXTRACT + files['shotchart_cbssports'] + '_players', gamedata, dbobj, lgobj)
            obj.resolveNewPlayers()
            player.updatePlayerFullName(dbobj)

        if 'shotchart_cbssports_ncaam' in files:
            obj = player.PlayerCbsSports(LOGDIR_EXTRACT + files['shotchart_cbssports_ncaam'] + '_players', gamedata, dbobj, lgobj)
            obj.resolveNewPlayers()
            player.updatePlayerFullName(dbobj)

        if 'boxscore_statsnbacom' in files:
            obj = player.PlayerStatsNbaCom(LOGDIR_EXTRACT + files['boxscore_statsnbacom'], gamedata, dbobj)
            obj.resolveNewPlayers()

            # Resolve with master player list
            obj = player.Resolve(dbobj)
            obj.resolveStatsNbacom()
            obj.resolveStatsNbacomByGame(gamedata['id'])

        if 'boxscore_statswnbacom' in files:
            obj = player.PlayerStatsNbaCom(LOGDIR_EXTRACT + files['boxscore_statswnbacom'], gamedata, dbobj)
            obj.resolveNewPlayers()

            # Resolve with master player list
            obj = player.Resolve(dbobj)
            obj.resolveStatsNbacom()
            obj.resolveStatsNbacomByGame(gamedata['id'])
        """

        for module, filename in files.items():
            print "  + %s" % (module)
            step_time = time.time()
            lib = importlib.import_module('clean.%s' % (module))
            getattr(lib,'run')(gamedata, filename, dbobj)

            logging.info("CLEAN - %s - game_id: %s - : time_elapsed %.2f" % (module, gamedata['id'], time.time() - step_time))



if __name__ == '__main__':
    sys.exit(main())
