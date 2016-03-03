import re
import datetime
import time
import csv
import difflib
import json
import logging

import player_resolution.find_player as find_player
from config import config
from config import constants 


LOGDIR_CLEAN = constants.LOGDIR_CLEAN
LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT




class Clean:

    def __init__(self, filename, gamedata, dbobj):
        self.filename = filename
        self.gamedata = gamedata
        self.db = dbobj
        self.find_player = find_player.FindPlayer(dbobj)

        # Save the players for each team in this variable -- speed is slow when relying solely on find_player module
        self.players_home = []
        self.players_away = []
        self.players = []
        self.known_plays = []
        self.home_team = {}
        self.away_team = {}

        self.plays = ''


    def _clean(self):
        self.plays = self._getPlays()
        self._getTeams()

        cleaning_functions = [
            self.guessUnknownQuarters,
            self.replaceBlankScores,
            self.replaceWithConformedTime,
            self.addGameId,
            self.identifyPlays,
            self.fillInEmptyFields
        ]

        all_plays = self.plays
        for function_name in cleaning_functions:
            all_plays = function_name(all_plays)

        for play in all_plays:
            print play


    def cleanAll(self):
        self.plays = self._getPlays()
        self._getTeams()

        cleaning_functions = [
            self.guessUnknownQuarters,
            self.replaceBlankScores,
            self.replaceWithConformedTime,
            self.addGameId,
            self.identifyPlays,
            self.fillInEmptyFields
        ]

        all_plays = self.plays
        for function_name in cleaning_functions:
            all_plays = function_name(all_plays)

        logging.info("CLEAN - playbyplay_espn - game_id: %s - play count: %s" % (self.gamedata['id'], len(all_plays)))
        self.dumpIntoFile(all_plays) 


    def _getPlays(self):
        data = json.loads(open(LOGDIR_EXTRACT + self.filename,'r').read())

        return data


    def guessUnknownQuarters(self, plays):
        newdata = []
        for i, line in enumerate(plays):
            if line['period'] == 'check quarter':
                line['period'] = plays[i-1]['period']
            
            newdata.append(line)

        return newdata
    

    def replaceWithConformedTime(self, plays):
        cleaned = []
        for line in plays:
            line['deciseconds_left'] = (int(line['time_left'].split(':')[0]) * 60 + int(line['time_left'].split(':')[1])) * 10
            del line['time_left']

            cleaned.append(line)
    
        return cleaned


    def replaceBlankScores(self, data):
        new = []

        # Check if first play has no scores
        if data:
            if data[0]['away_score'] == '':
                data[0]['away_score'] = 0
            if data[0]['home_score'] == '':
                data[0]['home_score'] = 0

            for i, line in enumerate(data):
                if line['away_score'] == '':
                    line['away_score'] = data[i-1]['away_score']
                if line['home_score'] == '':
                    line['home_score'] = data[i-1]['home_score']
               
                new.append(line) 

        return new


    def addGameId(self, data):
        new = []
        for i, line in enumerate(data):
            line['game_id'] = self.gamedata['id']
            new.append(line) 

        return new


    def identifyPlays(self, plays):

        cleaned = []
        for line in plays:
            # Define the team_id based on whether away or home table cell was filled in
            line['play_desc'] = line['play_description']
            del line['play_description']

            line['play_espn_id'], othervars = self._findPlay(line['play_desc'])

            # Check if team_id from description is different than the away/home alignment from the text file
            if 'team_id' in othervars.keys() and othervars['team_id'] != line['team_id']:
                logging.warning("CLEAN - playbyplay_espn - game_id: %s - team_ids found different in play description: play_index: %s" % (self.gamedata['id'], line['play_index']))

            line.update(othervars)
            cleaned.append(line)

        return cleaned 

    
    def fillInEmptyFields(self, data):
        newdata = []
        for line in data:
            if 'player_id' not in line.keys():
                line['player_id'] = -1
            if 'assist_player_id' not in line.keys():
                line['assist_player_id'] = -1
            if 'player1_id' not in line.keys():
                line['player1_id'] = -1
            if 'player2_id' not in line.keys():
                line['player2_id'] = -1
            

            newdata.append(line)

        return newdata


    def _getPlayDescriptionPatterns(self):
        return self.db.query("SELECT id, re, name FROM play_espn ORDER BY priority ASC, id ASC")


    def _findPlay(self, play):
        if not self.known_plays:
            self.known_plays = self._getPlayDescriptionPatterns()

        for (play_id, play_re, play_name) in self.known_plays:
            
            match = re.match(play_re, play)
            if match:
                othervars = {}
                for key,val in match.groupdict().items():
                    
                    if 'player' in key:
                        player_id = self._identifyPlayer(val.strip())
                        othervars[key + '_id'] = player_id

                    elif 'team' == key:
                        othervars['team_id'] = self._identifyTeam(val.strip())
                    else:
                        othervars[key] = val

                if 'player_id' in othervars and othervars['player_id']  == 0:
                    logging.warning("CLEAN - playbyplay_espn - game_id: %s - player not found in play_name: '%s'" % (self.gamedata['id'], play_name))

                return (play_id, othervars)

        print "No play found: %s" % play
        logging.warning("CLEAN - playbyplay_espn - game_id: %s - no play found: '%s'" % (self.gamedata['id'], play))

        return 0


    def _identifyTeam(self, team_name):
        team = self._matchTeam(team_name, [self.away_team, self.home_team])

        if team:
            return team['id']
        else:
            return -1



    def _matchTeam(self, team_name, teams):
        for team in teams:
            if team_name == team['name']:
                return team
            elif team_name == team['nickname']:
                return team
            elif team_name == team['alternate_nickname']:
                return team
            elif team_name == team['alternate_nickname2']:
                return team
            elif team_name == team['city']:
                return team
            elif team_name == team['alternate_city'] + ' ' + team['nickname']:
                return team
            elif team_name == team['alternate_city'] + ' ' + team['alternate_nickname']:
                return team
            elif team_name == team['alternate_city'] + ' ' + team['alternate_nickname2']:
                return team

        return False


    def _identifyPlayer(self, player_name):
        if not self.players:
            self.players = self.find_player._getPlayersInGame(self.gamedata['id'])

        player_id = self.find_player.matchPlayerByNameApproximate(player_name,self.players)

        return player_id


    def _getPlayerIdsInGame(self):
        players = self.db.query_dict("""
            SELECT p.*
            FROM player p
                INNER JOIN player_nbacom_by_game g ON g.nbacom_player_id = p.nbacom_player_id
            WHERE g.game_id = %s
        """ % (self.gamedata['id']))
        # Index by nbacom_player_id
    
        players_indexed = {}
        for player in players:
            players_indexed[player['id']] = player['first_name'] + " " + player['last_name']

        return players_indexed


    def _getTeams(self):
        self.home_team = self.db.query_dict("SELECT * FROM team WHERE id = %s" % (self.gamedata['home_team_id']))[0]
        self.away_team = self.db.query_dict("SELECT * FROM team WHERE id = %s" % (self.gamedata['away_team_id']))[0]


    def dumpIntoFile(self, data):
        f = open(LOGDIR_CLEAN + self.filename,'wb')
        f.write(json.dumps(data))


def run(game, filename, dbobj):
    pbpvars = {
        'filename':  filename,
        'gamedata':  game,
        'dbobj'   :  dbobj
    }
    Clean(**pbpvars).cleanAll()



