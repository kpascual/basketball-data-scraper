import boxscore_nbacom_v2015

import json
import find_player
import logging


def resolveNewPlayers(game, filename, dbobj, lgobj):
    obj = boxscore_nbacom_v2015.Player(filename, game, dbobj, lgobj)
    obj.resolveNewPlayers()


def appendPlayerKeys(game, filename, dbobj, lgobj):
    obj = boxscore_nbacom_v2015.Player(filename, game, dbobj, lgobj)
    obj.append()
