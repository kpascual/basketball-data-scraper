from config import constants
from bs4 import BeautifulSoup
import csv
import re
import logging
import json


LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT
LOGDIR_SOURCE = constants.LOGDIR_SOURCE

class Extract:

    def __init__(self, html, filename, gamedata):
        self.html = html
        self.gamedata = gamedata
        self.game_name = self.gamedata['abbrev']
        self.filename = filename

        self.home_team_city = self.gamedata['home_team_city']
        self.away_team_city = self.gamedata['away_team_city']


    def extractAndDump(self):
        stats = self.getPlayerData()
        self.dumpToFile(stats)
        game_stats = self.getGameStats()
        self.dumptoFileGameStats(game_stats)
        logging.info("EXTRACT - boxscore_espn - game_id: %s - player boxstats found: %s" % (self.gamedata['id'], len(stats)))



    def getPlayerData(self):
        soup = BeautifulSoup(self.html,'lxml')
        
        # 1. iterate through table, and determine current team
        # 2. parse out players
        data = []
        table = soup.find(class_='mod-data')
        team_count = 0
        current_team = ''
        current_team_id = 0
        if table:
            for child in table.children:
                if child.name == 'thead':
                    # Check for team name
                    team_class = child.find(class_ = 'team-color-strip')
                    if team_class:
                        for c in team_class.th.contents:
                            if c.string:
                                # Determine what team it is based on away team shows up first, then home team second
                                # Very brittle convention, assumes away team and home team are in the right order
                                team_count += 1
                                if team_count == 1:
                                    current_team_id = self.gamedata['away_team_id']
                                elif team_count == 2:
                                    current_team_id = self.gamedata['home_team_id']
                                else:
                                    current_team_id = 0


                elif child.name == 'tbody':
                    rows = child.find_all('tr')
                    for row in rows:
                        # Very strict limitation here:
                        tds = row.find_all('td')
                        if len(tds) == 14:
                            line = [current_team_id]
                            for td in tds:
                                if td.find('a'):
                                    line.append(td.a.string)
                                    match = re.search('.*/id/(?P<espn_id>\d+)/.*', td.a['href'])
                                    if match:
                                        line.append(match.groupdict()['espn_id'])
                                    else:
                                        line.append('')
                                else:
                                    line.append(td.string)

                            data.append(line)

        return data


    def getGameStats(self):
        soup = BeautifulSoup(self.html,'lxml')

        # Scores
        away_score = 0
        home_score = 0
        teams = soup.find_all(class_ = 'team-info')
        for i,team in enumerate(teams):
            if i == 0:
                spans = team.h3.find_all('span')
                for span in spans:
                    away_score = span.string
                
            elif i == 1:
                spans = team.h3.find_all('span')
                for span in spans:
                    home_score = span.string

        # Attendance
        match_attendance = soup.find_all(text = re.compile('Attendance:'))
        attendance = 'n/a'
        if match_attendance:
            for line in match_attendance:
                if line.parent.next_sibling:
                    attendance = line.parent.next_sibling.strip().replace(',','')
                    if attendance.isdigit():
                        attendance = int(attendance)
                    else:
                        attendance = 0


        return {
            'away_score': away_score,
            'home_score': home_score,
            'attendance': attendance,
            'game_id': self.gamedata['id']
        }



    def dumpToFile(self, list_data):
        f = open(LOGDIR_EXTRACT + self.filename,'wb')
        f.write(json.dumps(list_data))


    def dumptoFileGameStats(self, data):
        f = open(LOGDIR_EXTRACT + self.filename + '_game_stats','wb')
        f.write(json.dumps(data))



def run(game, filename):
    params = {
        'html': open(LOGDIR_SOURCE + filename,'r').read(),
        'filename':  filename,
        'gamedata':  game,
    }
    Extract(**params).extractAndDump()


