import json
from config import constants

LOGDIR_CLEAN = constants.LOGDIR_CLEAN

def run(filename, dbobj):
    data = json.loads(open(LOGDIR_CLEAN + filename, 'r').readline())

    newdata = []
    for line in data:
        del line['unknown13']

        newdata.append(line)

    dbobj.insert_or_update('boxscore_nbacom', newdata)


    stats = json.loads(open(LOGDIR_CLEAN + filename + '_game_stats', 'r').readline())
    dbobj.insert_or_update('game_stats_nbacom', [stats])

    return len(newdata)
