from config import constants
from bs4 import BeautifulSoup
#from BeautifulSoup import BeautifulSoup
import json
import re
import logging


LOGDIR_EXTRACT = constants.LOGDIR_EXTRACT
LOGDIR_SOURCE = constants.LOGDIR_SOURCE

class Extract:

    def __init__(self, html, filename, gamedata):
        self.html = html
        self.gamedata = gamedata
        self.filename = filename


    def extractAndDump(self):
        plays = self.extractAll()
        self.dumpToFile(plays)
        logging.info("EXTRACT - playbyplay_espn - game_id: %s - plays extracted: %s" % (self.gamedata['id'], len(plays)))


    def extractAll(self):
        data = self._getData()
        data = self._splitScores(data)

        return data


    def _getData(self):
        data = []
        self.soup = BeautifulSoup(self.html,'lxml')
        pbp = self.soup.find(class_ = "play-by-play")

        # Logos identify the teams. Match logos
        away_team_logo = ''
        away_team = self.soup.find(class_ = "team away")
        for item in away_team:
            found_logo = item.find(class_ = "team-logo")
            if found_logo:
                match = re.match('^(.*).png', found_logo["src"])
                away_team_logo = match.group(0)

        home_team_logo = ''
        home_team = self.soup.find(class_ = "team home")
        for item in home_team:
            found_logo = item.find(class_ = "team-logo")
            if found_logo:
                match = re.match('^(.*).png', found_logo["src"])
                home_team_logo = match.group(0)

        print (away_team_logo, home_team_logo)

        
        sections = pbp.find_all(class_='accordion-item')
        for section in sections:
            header = section.find("h3")
            period = self._parsePeriod(header.text)

            rows = section.find_all("tr")
            for row in rows:
                has_timestamp = row.find(class_ = "time-stamp")
                if has_timestamp:

                    event = {}
                    event['period'] = period
                    event['time_left'] = has_timestamp.text
                    event['play_description'] = row.find(class_ = "game-details").text
                    event['score'] = row.find(class_ = "combined-score").text

                    # Match team based on logo
                    team_temp = row.find(class_ = "team-logo")['src']
                    match = re.match('^(.*).png', team_temp)
                    team_in_row = match.group(0)
                    if team_in_row == away_team_logo:
                        event['team_id'] = self.gamedata['away_team_id']
                    elif team_in_row == home_team_logo:
                        event['team_id'] = self.gamedata['home_team_id']
                    else:
                        event['team_id'] = -1

                    data.append(event)

        return data


    def _parsePeriod(self, txt):

        # Check if a normal period
        match = re.search('(?P<period_index>[0-9])(st|nd|rd|th)\s+(?P<period_name>(Quarter|Overtime|Half|half))', txt)
        if match:
            period_name = '%s %s' % (match.group('period_index'), match.group('period_name'))
            period_number = constants.PERIODS[period_name.lower()]

            return period_number

        # Check if overtime
        if txt.lower() in constants.PERIODS.keys():
            return constants.PERIODS[txt.lower()]

        return False


    def _splitScores(self, data):
        newdata = []

        for row in data:
            away_score, home_score = row['score'].split('-')
            row['away_score'] = away_score.strip()
            row['home_score'] = home_score.strip()

            del row['score']
            newdata.append(row)

        return newdata




    def dumpToFile(self, data):
        f = open(LOGDIR_EXTRACT + self.filename,'wb')
        data_json = json.dumps(data)
        f.write(data_json)


def run(game, filename):
    params = {
        'html': open(LOGDIR_SOURCE + filename,'r').read(),
        'filename':  filename,
        'gamedata':  game
    }
    Extract(**params).extractAndDump()


