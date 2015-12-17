import json
from config import constants

LOGDIR_CLEAN = constants.LOGDIR_CLEAN

def run(filename, dbobj):
    data = json.loads(open(LOGDIR_CLEAN + filename, 'r').readline())


    dbobj.insert_or_update('boxscore_nbacom_v2015', data)

    team = json.loads(open(LOGDIR_CLEAN + filename + '_game_stats_team', 'r').readline())
    dbobj.insert_or_update('boxscore_nbacom_v2015_team', team)

    stats = json.loads(open(LOGDIR_CLEAN + filename + '_game_stats', 'r').readline())
    dbobj.insert_or_update('game_stats_nbacom_v2015', stats)

    return len(data)
