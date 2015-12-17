import boxscore_nbacom_v2015


def run(game, filename, dbobj):
    boxscore_nbacom_v2015.Clean(filename, game, dbobj).clean()


