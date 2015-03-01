# Defines where you want intermediate dump files to be stored

LOGDIR_EXTRACT = '/your_path_here/dump/extract/'
LOGDIR_SOURCE = '/your_path_here/dump/source/'
LOGDIR_CLEAN = '/your_path_here/dump/clean/'
LOGDIR_LOAD = '/your_path_here/dump/load/'
LOGDIR_AFTERCLEAN = '/your_path_here/dump/afterclean/'
LOGDIR_DOCS = '/your_path_here/dump/docs/'


URL = {
    'shotchart_cbssports': 'http://www.cbssports.com/nba/gametracker/shotchart/NBA_',
    'playbyplay_espn': 'http://espn.go.com/nba/playbyplay?gameId=<game_id>&period=0',
    'shotchart_espn': 'http://sports.espn.go.com/nba/gamepackage/data/shot?gameId=<game_id>',
    'playbyplay_nbacom': 'http://www.nba.com/games/game_component/dynamic/<game_id>/pbp_all.xml',
    'shotchart_nbacom': 'http://www.nba.com/games/game_component/dynamic/<game_id>/shotchart_all.xml',
    'boxscore_nbacom': 'http://www.nba.com/games/game_component/dynamic/<game_id>/boxscore.xml',
    'playbyplay_statsnbacom': 'http://stats.nba.com/stats/playbyplay?GameID=<game_id>&RangeType=0&StartPeriod=0&EndPeriod=0&StartRange=0&EndRange=0&playbyplay=undefined',
    'shotchart_statsnbacom': 'http://stats.nba.com/stats/shotchartdetail?Season=&SeasonType=Regular+Season&LeagueID=00&TeamID=0&PlayerID=0&GameID=<game_id>&Outcome=&Location=&Month=0&SeasonSegment=&DateFrom=&DateTo=&OpponentTeamID=0&VsConference=&VsDivision=&Position=&RookieYear=&GameSegment=&Period=0&LastNGames=0&ContextFilter=&ContextMeasure=FG_PCT&zone-mode=basic&viewShots=true',
    'boxscore_statsnbacom':'http://stats.nba.com/stats/boxscore?GameID=<game_id>&StartPeriod=0&EndPeriod=12&StartRange=0&EndRange=20000000&RangeType=0',
    
    'playbyplay_espn_wnba': 'http://espn.go.com/wnba/playbyplay?gameId=<game_id>&period=0',
    'shotchart_espn_wnba': 'http://sports.espn.go.com/wnba/gamepackage/data/shot?gameId=<game_id>',
    'playbyplay_wnbacom': 'http://www.wnba.com/games/game_component/dynamic/<game_id>/pbp_all.xml',
    'shotchart_wnbacom': 'http://www.wnba.com/games/game_component/dynamic/<game_id>/shotchart_all.xml',
    'boxscore_wnbacom': 'http://www.wnba.com/games/game_component/dynamic/<game_id>/boxscore.xml',
    'playbyplay_statswnbacom': '',
    'shotchart_statswnbacom': '',
}


SECONDS = {
    'nba': {
        'game_regulation': 2880,
        'in_quarter': 720,
        'in_overtime': 300
    },
    'wnba': {
        'game_regulation': 2400,
        'in_quarter': 600,
        'in_overtime': 300
    },
}

PERIODS = {
    '1 quarter': 1,
    '2 quarter': 2,
    '3 quarter': 3,
    '4 quarter': 4,
    '1 overtime': 5,
    '2 overtime': 6,
    '3 overtime': 7,
    '4 overtime': 8,
    '5 overtime': 9,
    '6 overtime': 10,
    '7 overtime': 11,
    '8 overtime': 12,
    '9 overtime': 13,
    '10 overtime': 14,
    '11 overtime': 15,
    '12 overtime': 16,
    '5 quarter': 5,
    '6 quarter': 6,
    '7 quarter': 7,
    '8 quarter': 8,
    '9 quarter': 9,
    '10 quarter': 10,
    '11 quarter': 11,
    '12 quarter': 12,
    '13 quarter': 13,
    '14 quarter': 14,
    '15 quarter': 15,
    '16 quarter': 16,
    '1 half': 1,
    '2 half': 2,
}

