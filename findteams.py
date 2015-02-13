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


class FindTeams:

    def __init__(self, league_season_id = False):
        self.league_season_id = league_season_id


    def run(self, dt):
        pass


    def parse(self):
        pass


    def _getRecentLeagueSeasonId(self, league_obj):
        if league_obj and not self.league_season_id:
            self.league_season_id = league_obj._getLeagueSeason()['id']


class FindTeamsEspn(FindTeams):

    def __init__(self, league_season_id = False):
        self.league_name = 'nba'
        self.league_abbrev = 'nba'
        self.league_obj = league.League(configg.dbobj, self.league_name)
        FindTeams.__init__(self, league_season_id)
        self._getRecentLeagueSeasonId(self.league_obj)


    def parse(self):
        html_espn = self._getHtml()
        data_espn = self._getData(html_espn)
        self._saveToDatabase(data_espn)


    def _getHtml(self): 
        url = 'http://espn.go.com/mens-college-basketball/teams'
        response = urllib2.urlopen(url)
        return response.read()


    def _getData(self, html):
        soup = BeautifulSoup(html, 'lxml')
        scraped_data = soup.find_all(class_='bi')
        teams = []
        for line in scraped_data:
            data = self._parseTeamData(line)
            if data:
                teams.append(data)

        return teams


    def _parseTeamData(self, txt):
        match = re.match('^http://espn.go.com/mens-college-basketball/team/_/id/(?P<espn_team_id>\d+)/(?P<name>[0-9a-zA-Z-\'\.&\(\)]+)$', txt['href'])
        if match:
            info = match.groupdict()
            info['city'] = txt.string
            info['nickname'] = info['name'].replace('-',' ').replace(txt.string.lower(), '').strip()
            return info
        else:
            print txt['href']
            return False
        

    def _saveToDatabase(self, teams):
        for team in teams:
            team['league_season_id'] = self.league_season_id
            configg.dbobj.insert_or_update('team', [team])


class FindTeamsCbsSports(FindTeams):

    def __init__(self, league_season_id = False):
        self.league_name = 'ncaam'
        self.league_abbrev = 'ncaam'
        self.dbobj = configg.dbobj
        self.league_obj = league.League(configg.dbobj, self.league_name)
        FindTeams.__init__(self, league_season_id)
        self._getRecentLeagueSeasonId(self.league_obj)


    def parse(self):
        html = self._getHtml()
        data = self._getData(html)
        self._resolveInDatabase(data)


    def _getHtml(self): 
        url = 'http://www.cbssports.com/collegebasketball/teams'
        response = urllib2.urlopen(url)
        return response.read()


    def _getData(self, html):
        soup = BeautifulSoup(html, 'lxml')
        links = soup.find_all('a')
        teams = []
        for link in links:
            match = re.match('/collegebasketball/teams/page/(?P<abbrev>\w+)/(?P<name>[a-zA-Z-]+)', link['href'])
            if match:
                print link['href']
                teams.append( {'abbrev':match.groupdict()['abbrev'], 'name': match.groupdict()['name'], 'text': link.string} )

        return teams



    def _parseTeamData(self, txt):
        match = re.match('^http://espn.go.com/mens-college-basketball/team/_/id/(?P<espn_team_id>\d+)/(?P<name>[0-9a-zA-Z-\'\.&\(\)]+)$', txt['href'])
        if match:
            info = match.groupdict()
            info['city'] = txt.string
            info['nickname'] = info['name'].replace('-',' ').replace(txt.string.lower(), '').strip()
            return info
        else:
            print txt['href']
            return False
        

    def _resolveInDatabase(self, teams):
        matches = []
        unmatched = []

        for team in teams:
            team['league_season_id'] = self.league_season_id
            match = self.dbobj.query_dict("""
                SELECT id 
                FROM team 
                WHERE 
                    name = '%s'
                    OR name = REPLACE('%s','-state-','-st-')
                    OR '%s' = REPLACE(name,'-state-','-st-')
                    OR '%s' = REPLACE(name,'\\'','')
                    OR '%s' = REPLACE(name,'\\&','')
                    OR '%s' = REPLACE(name,'\\.','')
            """ % (team['name'], team['name'], team['name'], team['name'], team['name'], team['name']))
            if match:
                print match[0]
                self.dbobj.query("UPDATE team SET cbssports_code = '%s' WHERE id = %s" % (team['abbrev'], match[0]['id']))
                matches.append(team)
            else:
                print "no match"
                unmatched.append(team)
            print team
            #configg.dbobj.insert_or_update('team', [team])

        print len(matches)
        for line in unmatched:
            print line


def main():
    obj = FindTeamsCbsSports(9)
    obj.parse()
    


if __name__ == '__main__':
    main()
