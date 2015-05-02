from bs4 import BeautifulSoup
import urllib2
import re
import datetime
import time
import json

import db
from config import config
import configg
import league


# A script that scrapes ESPN.com's scoreboard to retrieve ESPN's game_id and store into MySQL db

# Going back to a singleton database object
dbobj = configg.dbobj

class FindGames:

    def __init__(self, league_season_id = False):
        self.league_season_id = league_season_id
        self.dbobj = configg.dbobj


    def run(self, dt):
        pass


    def parse(self):
        pass


    def _getRecentLeagueSeasonId(self, league_obj):
        if league_obj and not self.league_season_id:
            self.league_season_id = league_obj._getLeagueSeason()['id']


class FindGamesEspnNba(FindGames):

    def __init__(self, league_season_id = False):
        self.league_name = 'nba'
        self.league_abbrev = 'nba'
        self.league_obj = league.League(configg.dbobj, self.league_name)
        FindGames.__init__(self, league_season_id)
        self._getRecentLeagueSeasonId(self.league_obj)


    def parse(self, dt):
        html_espn = self._getScoreboardDoc(dt)
        data = self._getGameIds(html_espn, dt)
        return data


    def _getScoreboardDoc(self, dt): 
        url = 'http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?calendartype=blacklist&dates=<date>'
        response = urllib2.urlopen(url.replace('<date>', dt.isoformat().replace('-', '')))
        return response.read()


    def _getGameIds(self, text, dt):
        obj = json.loads(text)
        games = []
        for event in obj['events']:
            game = {}
            game['espn_game_id'] = event['id']
            game['date_played'] = dt
            away_team_code = ''
            home_team_code = ''

            teams = event['competitions'][0]['competitors']
            for team in teams:
                resolved_team = self._findTeamName(team['team']['shortDisplayName'])
                game['%s_team_id' % (team['homeAway'])] = resolved_team['id']
                if team['homeAway'] == 'home':
                    home_team_code = resolved_team['code']
                if team['homeAway'] == 'away':
                    away_team_code = resolved_team['code']

            game['abbrev'] = '%s_%s_%s@%s' % (dt, self.league_season_id, away_team_code, home_team_code)
            game['cbssports_game_id'] = '%s_%s@%s' % (dt, away_team_code, home_team_code)


            games.append(game)
        

        return games


    def _findTeamName(self, name):
        teams = self.league_obj.getTeams(self.league_season_id)
        
        for team in teams:
            if name == team['nickname'] or name == team['alternate_nickname']:
                return {
                    'id': team['id'], 
                    'code': team['code'],
                    'nbacom_code': team['nbacom_code'], 
                    'nickname': team['nickname']
                }
            else:
                pass

        return {
            'id': 0,
            'code': 'unk',
            'nbacom_code': 'unk',
            'nickname': 'unknown'
        }


class FindGamesEspnWnba(FindGamesEspnNba):

    def __init__(self, league_season_id = False):
        self.league_name = 'wnba'
        self.league_abbrev = 'wnba'
        self.league_obj = league.League(configg.dbobj, self.league_name)
        FindGames.__init__(self, league_season_id)
        self._getRecentLeagueSeasonId(self.league_obj)

    def _getScoreboardDoc(self, dt):
        url = 'http://espn.go.com/wnba/scoreboard?date=<date>'
        response = urllib2.urlopen(url.replace('<date>', dt.isoformat().replace('-', '')))
        return response.read()


class FindGamesEspnNcaaM(FindGamesEspnNba):

    def __init__(self, league_season_id = False):
        self.league_name = 'ncaam'
        self.league_abbrev = 'ncb'
        self.league_obj = league.League(configg.dbobj, self.league_name)
        FindGames.__init__(self, league_season_id)
        self._getRecentLeagueSeasonId(self.league_obj)

    def _getScoreboardDoc(self, dt):
        url = 'http://espn.go.com/ncb/scoreboard?date=<date>&confId=50'
        response = urllib2.urlopen(url.replace('<date>', dt.isoformat().replace('-', '')))
        return response.read()


    def _matchTeams(self, game_ids, soup):
        game_info = []
        for game_id in game_ids:
            
            try:
                away_team_id = 0
                team_div = soup.find(id='%s-aNameOffset' % game_id)
                if team_div and hasattr(team_div, 'a'):
                    url = team_div.a['href']
                    espn_team_id = 0
                    match = re.match('http://espn.go.com/mens-college-basketball/team/_/id/(?P<espn_team_id>\d+)/.*', url)
                    if match:
                        espn_team_id = match.groupdict()['espn_team_id']
                    away_team_id, away_team_name, away_team_nickname = self._findTeamByEspnId(espn_team_id)

                home_team_id = 0
                team_div = soup.find(id='%s-hNameOffset' % game_id)
                if team_div and hasattr(team_div, 'a'):
                    url = team_div.a['href']
                    espn_team_id = 0
                    match = re.match('http://espn.go.com/mens-college-basketball/team/_/id/(?P<espn_team_id>\d+)/.*', url)
                    if match:
                        espn_team_id = match.groupdict()['espn_team_id']
                    home_team_id, home_team_name, home_team_nickname = self._findTeamByEspnId(espn_team_id)


                game_info.append(
                    {
                        'espn_game_id':game_id, 
                        'away_team_name': away_team_name, 
                        'home_team_name': home_team_name, 
                        'away_team_id': away_team_id, 
                        'home_team_id': home_team_id, 
                        'away_team_nickname': away_team_nickname, 
                        'home_team_nickname': home_team_nickname
                    }
                )
            except Exception as e:
                print "Team not found. Skipping."
                print e

        return game_info


    def _findTeamByEspnId(self, espn_team_id):
        data = self.dbobj.query_dict("SELECT * FROM team WHERE espn_team_id = %s AND league_season_id = %s" % (espn_team_id, self.league_season_id))
        if data:
            return (data[0]['id'], data[0]['name'], data[0]['nickname'])

        return (0,'unk','unknown') 


    def _translateEspnGameData(self, game_data, dt):
        # Removing special characters for abbrev
        pattern = re.compile("[^\w\s]")

        final = []
        for g in game_data:
            g['date_played'] = dt
            g['abbrev'] = '%s_%s_%s@%s' % (dt, self.league_season_id, g['away_team_name'].replace(' ','-'), g['home_team_name'].replace(' ','-'))
            g['permalink'] = pattern.sub("", g['away_team_name']) + '-at-' + pattern.sub("", g['home_team_name']) + '-' + dt.strftime("%B-%d-%Y")
            g['permalink'] = g['permalink'].replace('-0','-').replace(' ','-').lower()
            g['league_season_id'] = self.league_season_id
            final.append(g)

            del g['away_team_nickname']
            del g['home_team_nickname']
            del g['away_team_name']
            del g['home_team_name']

        return final



class FindGamesStatsNbaCom(FindGames):

    def __init__(self, league_season_id = False):
        self.league_name = 'nba'
        self.league_obj = league.League(configg.dbobj, self.league_name)
        FindGames.__init__(self, league_season_id)
        self._getRecentLeagueSeasonId(self.league_obj)

    def run(self):
        pass


    def parse(self, dt):
        data = self._getData(dt)
        data = self._resolve(data)
        return data


    def _getData(self, dt):
        dt_formatted = dt.strftime("%m/%d/%Y")
        url = 'http://stats.nba.com/stats/scoreboard/?LeagueID=00&gameDate=%s&DayOffset=0' % (dt_formatted)
        response = urllib2.urlopen(url)
        raw = response.read()

        games = []
        data = json.loads(raw)
        for line in data['resultSets']:
            if line['name'] == 'GameHeader':
                for row in line['rowSet']:
                    games.append(dict(zip(line['headers'], row)))

        return games


    def _resolve(self, data):
        resolved_data = []
        for line in data:
            newline = {}
            home_team = dbobj.query_dict("SELECT * FROM team WHERE statsnbacom_team_id = %s AND league_season_id = %s" % (line['HOME_TEAM_ID'], self.league_season_id))
            if home_team:
                newline['home_team_id'] = home_team[0]['id']
            else:
                newline['home_team_id'] = line['HOME_TEAM_ID'] * -1
            away_team = dbobj.query_dict("SELECT * FROM team WHERE statsnbacom_team_id = %s AND league_season_id = %s" % (line['VISITOR_TEAM_ID'], self.league_season_id))
            if away_team:
                newline['away_team_id'] = away_team[0]['id']
            else:
                newline['away_team_id'] = line['VISITOR_TEAM_ID'] * -1
            newline['statsnbacom_game_id'] = line['GAME_ID']
            newline['nbacom_game_id'] = line['GAMECODE']
            newline['gametime'] = line['GAME_STATUS_TEXT']
            newline['national_tv'] = line['NATL_TV_BROADCASTER_ABBREVIATION']
            newline['league_season_id'] = self.league_season_id

            resolved_data.append(newline)

        return resolved_data



def merge(data):

    games = {}

    for line in data:
        if (line['away_team_id'], line['home_team_id']) not in games.keys():
            games[(line['away_team_id'], line['home_team_id'])] = {}

        games[(line['away_team_id'], line['home_team_id'])].update(line)


    return games


def getDay(league_id, league_season_id, date):
    print date.isoformat()
    league_map = {
        1: [FindGamesEspnNba, FindGamesStatsNbaCom], # NBA
        2: [FindGamesEspnWnba], # WNBA
        4: [FindGamesEspnNcaaM], # NCAA Men
    }


    game_items = []
    for l in league_map[league_id]:
        obj = l(league_season_id)
        data = obj.parse(date)
        game_items.extend(data)
        print data


    games = merge(game_items)
    print games
    games_list = [g for key, g in games.items()]
    dbobj.insert_or_update('game', games_list)
    print "%s GAMES FOUND:" % (len(games))
    print dbobj.getCredentials()
    for key, g in games.items():
        print key
        print g
        print '\n'


def getInputs():
    start_date_input = raw_input('Choose START date (yyyy-mm-dd or blank for today\'s date of %s): ' % (datetime.date.today()))
    if not start_date_input:
        start_date_input = datetime.date.today()
        end_date_input = start_date_input
    else:
        start_date_input = datetime.datetime.strptime(start_date_input, '%Y-%m-%d').date()
        end_date_input = raw_input('Choose END date (yyyy-mm-dd or blank for START date): ')
        if not end_date_input:
            end_date_input = start_date_input
        else:
            end_date_input = datetime.datetime.strptime(end_date_input, '%Y-%m-%d').date()


    leagues = dbobj.query_dict("SELECT * FROM league")
    for l in leagues:
        print '%s:   %s' % (l['id'], l['name'])
    league_input = raw_input('Choose league: ')
    league_input = int(league_input)

    league_seasons = dbobj.query_dict("SELECT ls.id, s.name as season_name FROM league_season ls INNER JOIN league l ON l.id = ls.league_id INNER JOIN season s ON s.id = ls.season_id WHERE l.id = %s" % (league_input))
    for ls in league_seasons:
        print '%s:   %s' % (ls['id'], ls['season_name'])
    league_season_input = raw_input('Choose season: ')

    dt = start_date_input
    i = 1
    while dt <= end_date_input:
        getDay(league_input, league_season_input, dt)
        dt = dt + datetime.timedelta(days=1)

        i = i + 1
        if i % 3 == 0:
            time.sleep(5)






    


if __name__ == '__main__':
    getInputs()
