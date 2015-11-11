import json
import os
import time
import logging
import csv
import importlib

from config import constants


LOGDIR_LOAD = constants.LOGDIR_LOAD
LOGDIR_CLEAN = constants.LOGDIR_CLEAN



def go(tuple_games_and_files, dbobj):

    for gamedata, files in tuple_games_and_files:
        print "+++ LOAD: %s - %s" % (gamedata['id'], gamedata['abbrev'])
        s_time = time.time()

        for module, filename in files.items():
            step_time = time.time()

            if os.path.isfile(LOGDIR_CLEAN + filename):
                lib = importlib.import_module('load.%s' % (module))
                rows_loaded = getattr(lib, 'run')(filename, dbobj)
 
                print "  + %s - %s rows loaded - %.2f sec" % (module, rows_loaded, time.time() - step_time)



        logging.info("LOAD - game_id: %s - time_elapsed %.2f" % (gamedata['id'], time.time() - s_time))
        
