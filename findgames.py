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
        self.league_obj = league.League(dbobj, self.league_name)
        FindGames.__init__(self, league_season_id)
        self._getRecentLeagueSeasonId(self.league_obj)


    def parse(self, dt):
        html_espn = self._getScoreboardDoc(dt)
        data_espn = self._getData(html_espn)
        data = self._translateEspnGameData(data_espn, dt)
        return data


    def _getScoreboardDoc(self, dt): 
        url = 'http://espn.go.com/nba/scoreboard?date=<date>'
        response = urllib2.urlopen(url.replace('<date>', dt.isoformat().replace('-', '')))
        return response.read()


    def _getData(self, html):
        soup = BeautifulSoup(html, 'lxml')
        links = soup.findAll(href=re.compile("/%s/conversation.*" % (self.league_name)))
        
        game_ids = []
        for l in links:
            match = re.search("/%s/conversation\?gameId=(?P<game_id>[0-9]+)$" % (self.league_name),l['href'])
            
            if match:
                found = match.groupdict()
                game_ids.append(found['game_id'])

        game_info = []
        for game_id in game_ids:
            
            try:
                away_team_id = 0
                team_div = soup.select('#%s-aNameOffset' % game_id)
                if team_div and hasattr(team_div[0], 'a'):
                    away_team_id, away_team, away_team_nbacom, away_team_nickname = self._findTeamName(team_div[0].a.contents[0])

                home_team_id = 0
                team_div = soup.select('#%s-hNameOffset' % game_id)
                if team_div and hasattr(team_div[0], 'a'):
                    home_team_id, home_team, home_team_nbacom, home_team_nickname = self._findTeamName(team_div[0].a.contents[0])


                game_info.append(
                    {'espn_game_id':game_id, 'away_team': away_team, 
                    'home_team': home_team, 'away_team_nbacom': away_team_nbacom, 'home_team_nbacom': home_team_nbacom,
                    'away_team_id': away_team_id, 'home_team_id': home_team_id, 
                    'away_team_nickname': away_team_nickname, 'home_team_nickname': home_team_nickname
                    }
                )
            except Exception as e:
                print "Team not found. Skipping."
                print e

        return game_info


    def _translateEspnGameData(self, game_data, dt):

        final = []
        for g in game_data:
            g['date_played'] = dt
            g['abbrev'] = '%s_%s@%s' % (dt, g['away_team'], g['home_team'])
            g['away_team_code'] = g['away_team']
            g['home_team_code'] = g['home_team']
            g['nbacom_game_id'] = '%s/%s%s' % (dt.isoformat().replace('-',''), g['away_team_nbacom'], g['home_team_nbacom'])
            g['cbssports_game_id'] = g['abbrev'].replace('-','')
            g['permalink'] = g['away_team_nickname'] + '-at-' + g['home_team_nickname'] + '-' + dt.strftime("%B-%d-%Y")
            g['permalink'] = g['permalink'].replace('-0','-').lower()
            g['league_season_id'] = self.league_season_id
            final.append(g)

            del g['away_team_nickname']
            del g['home_team_nickname']
            del g['away_team_nbacom']
            del g['home_team_nbacom']

        return final


    def _findTeamName(self, name):
        teams = self.league_obj.getTeams(self.league_season_id)
        
        for team in teams:
            if name == team['nickname'] or name == team['alternate_nickname']:
                return (team['id'], team['code'],team['nbacom_code'], team['nickname'])
            else:
                pass

        return (0,'unk','unk','unknown') 


class FindGamesEspnWnba(FindGamesEspnNba):

    def __init__(self, league_season_id = False):
        self.league_name = 'wnba'
        self.league_obj = league.League(dbobj, self.league_name)
        FindGames.__init__(self, league_season_id)
        self._getRecentLeagueSeasonId(self.league_obj)

    def _getScoreboardDoc(self, dt):
        url = 'http://espn.go.com/wnba/scoreboard?date=<date>'
        response = urllib2.urlopen(url.replace('<date>', dt.isoformat().replace('-', '')))
        return response.read()



class FindGamesStatsNbaCom(FindGames):

    def __init__(self, league_season_id = False):
        self.league_name = 'nba'
        self.league_obj = league.League(dbobj, self.league_name)
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
    }


    game_items = []
    for l in league_map[league_id]:
        obj = l(league_season_id)
        data = obj.parse(date)
        game_items.extend(data)


    games = merge(game_items)
    games_list = [g for key, g in games.items()]
    dbobj.insert_or_update('game', games_list)
    print "%s GAMES FOUND:" % (len(games))
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
