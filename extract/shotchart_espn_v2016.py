from config import constants
from bs4 import BeautifulSoup
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
        shots = self.extractAll()
        self.dumpToFile(shots)
        logging.info("EXTRACT - shotchart_espn_v2016 - game_id: %s - shots extracted: %s" % (self.gamedata['id'], len(shots)))

        players = self.extractEspnPlayerIds()
        self.dumpPlayersToFile(players)



    def extractAll(self):
        data = self._getData()
        return data


    def _getData(self):
        data = []
        self.soup = BeautifulSoup(self.html,'lxml')
        shot_groups = self.soup.find_all(class_ = "shots")


        for sg in shot_groups:
            li_shots = sg.find_all('li')
            for shot in li_shots:
                newshot = {}
                newshot['description'] = shot.text
                newshot['espn_player_id'] = shot['data-shooter']
                newshot['period'] = shot['data-period']
                newshot['team_shot_index'] = shot['id'].replace('shot', '')
                newshot['team_id'] = self.gamedata['home_team_id'] if shot['data-homeaway'] == 'home' else self.gamedata['away_team_id']

                # Pass through percentage values, interpret them in the clean step
                match_y = re.match('.*;left:(?P<value>[0-9.]+)%;.*', shot['style'])
                if match_y:
                    newshot['y'] = match_y.groupdict()['value']

                match_x = re.match('.*;top:(?P<value>[0-9.]+)%;.*', shot['style'])
                if match_x:
                    newshot['x'] = match_x.groupdict()['value']


                data.append(newshot)

        return data


    def extractEspnPlayerIds(self):
        data = []
        self.soup = BeautifulSoup(self.html,'lxml')
        player_groups = self.soup.find_all(class_ = "playerfilter")

        for pg in player_groups:
            players = pg.find_all('li')
            for player in players:
                newplayer = {}
                newplayer['espn_player_id'] = player['data-playerid']
                newplayer['full_name'] = player.text
                newplayer['team_id'] = self.gamedata['home_team_id'] if player['data-homeaway'] == 'home' else self.gamedata['away_team_id']

                if int(newplayer['espn_player_id']) != 0:
                    data.append(newplayer)

        return data


    def dumpToFile(self, data):
        f = open(LOGDIR_EXTRACT + self.filename,'wb')
        data_json = json.dumps(data)
        f.write(data_json)


    def dumpPlayersToFile(self, data):
        f = open(LOGDIR_EXTRACT + self.filename + '_players','wb')
        data_json = json.dumps(data)
        f.write(data_json)


def run(game, filename):
    params = {
        'html': open(LOGDIR_SOURCE + filename,'r').read(),
        'filename':  filename,
        'gamedata':  game
    }
    Extract(**params).extractAndDump()


