import json
from config import constants

LOGDIR_CLEAN = constants.LOGDIR_CLEAN

def run(filename, dbobj):
    data = json.loads(open(LOGDIR_CLEAN + filename + '_game_stats', 'r').readline())
    dbobj.insert_or_update('game_stats', [data])

    data = json.loads(open(LOGDIR_CLEAN + filename, 'r').readline())
    dbobj.insert_or_update('boxscore_espn', data)

    return len(data)
