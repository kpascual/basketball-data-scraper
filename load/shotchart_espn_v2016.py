import json
from config import constants

LOGDIR_CLEAN = constants.LOGDIR_CLEAN

def run(filename, dbobj):
    data = json.loads(open(constants.LOGDIR_CLEAN + filename, 'r').read())
    dbobj.insert_or_update('shotchart_espn_v2016',data)

    return len(data)
