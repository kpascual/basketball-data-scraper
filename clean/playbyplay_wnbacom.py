import re
import datetime
import time
import json
import logging

from bs4 import BeautifulSoup
import player_resolution.find_player as find_player

from config import constants 

import playbyplay_nbacom


LOGDIR_CLEAN = constants.LOGDIR_CLEAN
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT
LOGDIR_SOURCE = constants.LOGDIR_SOURCE



# action_type: 1 = made, 2 = missed
# msg_type:

class Clean(playbyplay_nbacom.Clean):

    def __init__(self, filename, gamedata, dbobj):
        self.qry = dbobj
        self.dbobj = dbobj
        self.game = gamedata
        self.filename = filename
        self.find_player = find_player.FindPlayer(dbobj)

        self.home_players = self._getHomePlayers()
        self.away_players = self._getAwayPlayers()




def run(game, filename, dbobj):
    Clean(filename, game, dbobj).clean()


# I think msg_type is actually play_type
# And I think action_type is really just the shot type
def main():

    dbobj = db.Db(db.dbconn_nba)

    game = dbobj.query_dict("SELECT * FROM game WHERE id = %s" % (2734))[0]
    filename = '%s_playbyplay_nbacom' % (game['abbrev'])
    obj = Clean(filename,game,dbobj)
    data = obj.getPlayByPlayData()
    #for row in data:
    #    print dict([(key,val) for key,val in row.items() if 'player' in key or 'play_desc' in key])


if __name__ == '__main__':
    main()
