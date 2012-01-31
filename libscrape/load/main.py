import json

from libscrape.config import db
from libscrape.config import constants


LOGDIR_LOAD = constants.LOGDIR_LOAD
LOGDIR_CLEAN = constants.LOGDIR_CLEAN


class Load:

    def __init__(self, dbobj):
        self.db = dbobj


    def loadCbsSportsShotData(self, f):
       
        str_fields = open(constants.LOGDIR_CLEAN + f, 'r').readline()
        sql = """
            LOAD DATA LOCAL INFILE '%s' REPLACE
            INTO TABLE shotchart_cbssports
            FIELDS TERMINATED BY ','
            LINES TERMINATED BY '\n'
            IGNORE 1 LINES
            (%s)
        """ % (constants.LOGDIR_CLEAN + f, tables['shotchart_cbssports'], str_fields)
        self.db.query(sql)


    def loadEspnPlayByPlayData(self, f):

        str_fields = open(constants.LOGDIR_CLEAN + f, 'r').readline()
        sql = """
            LOAD DATA LOCAL INFILE '%s' REPLACE
            INTO TABLE playbyplay_espn
            FIELDS TERMINATED BY ','
            LINES TERMINATED BY '\n'
            IGNORE 1 LINES
            (%s)
        """ % (constants.LOGDIR_CLEAN + f, tables['playbyplay_espn'], str_fields)
        self.db.query(sql)


    def loadCbsSportsBoxScore(self, f):

        str_fields = open(constants.LOGDIR_CLEAN + f, 'r').readline()
        sql = """
            LOAD DATA LOCAL INFILE '%s' REPLACE
            INTO TABLE boxscore_cbssports
            FIELDS TERMINATED BY ','
            LINES TERMINATED BY '\n'
            IGNORE 1 LINES
            (%s)
        """ % (constants.LOGDIR_CLEAN + f, tables['boxscore_cbssports'], str_fields)
        self.db.query(sql)


    def loadShotChartNbaCom(self, f):
        shots = json.loads(open(LOGDIR_CLEAN + f,'r').readline())
        for shot in shots:
            sql = """
                INSERT INTO shotchart_nbacom
                (game_id, player_id, x, y, nbacom_play_type_id, nbacom_play_num, period, deciseconds_left, team_id,  is_shot_made) VALUES
                (%s, %s, "%s", "%s", %s, %s, %s, %s, %s, %s)
            """ % (
                shot['game_id'], shot['player_id'], shot['x'], shot['y'], shot['act'], shot['id'],
                shot['prd'], shot['time'], shot['tm'], shot['result']
            )

            self.db.query(sql)


    def loadBoxScoreNbaCom(self, f):
        data = json.loads(open(LOGDIR_CLEAN + f,'r').readline())
        for line in data:
            print line 
            sql = """
                INSERT INTO boxscore_nbacom
                (game_id, player_id, is_dnp, time_played, sec_played, fgm, fga, threeptm, threepta, ftm, fta,
                off_reb, def_reb, total_reb, assists, personal_fouls, steals, turnovers, blocks, blocks_against, 
                plusminus, total_points, unknown12)
                VALUES
                (%s, %s, %s, "%s", %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                "%s", %s, %s)
            """ % (
                line['game_id'], line['player_id'], line['is_dnp'], line['time_played'], line['sec_played'], 
                line['fgm'], line['fga'], line['threeptm'], line['threepta'], line['ftm'], line['fta'],
                line['off_reb'], line['def_reb'], line['total_reb'], line['assists'], line['pfouls'],
                line['steals'], line['turnovers'], line['blocks'], line['blocks_against'], line['plusminus'],
                line['total_points'], line['unknown12']
            )

            self.db.query(sql)


    def loadShotChartEspn(self, f):
        shots = json.loads(open(LOGDIR_CLEAN + f,'r').readline())
        for shot in shots:
            sql = """
                INSERT INTO shotchart_espn
                (game_id, player_id, x, y, shot_type, espn_play_num, period, deciseconds_left, team_id,  is_shot_made, distance)
                VALUES
                (%s, %s, "%s", "%s", "%s", %s, %s, %s, %s, %s, %s)
            """ % (
                shot['game_id'], shot['player_id'], shot['x'], shot['y'], shot['shot_type'], shot['id'],
                shot['qtr'], shot['time_left'], shot['t'], shot['result'], shot['distance']
            )

            self.db.query(sql)


def go(tuple_games_and_files, dbobj):
    for gamedata, filenames in tuple_games_and_files:
        obj = Load(dbobj)
        obj.loadCbsSportsShotData(filenames['shotchart_cbssports'])
        obj.loadEspnPlayByPlayData(filenames['playbyplay_espn'])
        obj.loadCbsSportsBoxScore(filenames['boxscore_cbssports'])
        obj.loadShotChartNbaCom(filenames['shotchart_nbacom'])
        obj.loadShotChartEspn(filenames['shotchart_espn'])
        obj.loadBoxScoreNbaCom(filenames['boxscore_nbacom'])
        

def test():
    f = '2011-12-25_LAC@GS_shotchart_espn'
    loadShotChartEspn(f)


if __name__ == '__main__':
    test()
