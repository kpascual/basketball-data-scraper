import playbyplay_nbacom_v2015


def run(game, filename, dbobj):
    playbyplay_nbacom_v2015.Clean(filename, game, dbobj).clean()


