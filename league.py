import db
from config import config

class League:

    def __init__(self, dbobj, name = '', league_id = '', league_season_id = 0):
        self.dbobj = dbobj
        self.name = name
        if name:
            self.obj = self._getLeagueByName(name)
            self.name = self.obj['name']
        elif league_id:
            self.obj = self._getLeagueById(league_id)
            self.name = self.obj['name']

        if league_season_id:
            self.league_season = self._getLeagueSeason(league_season_id)
        elif self.obj:
            self.league_season = self._getCurrentLeagueSeason()
        else:
            self.league_season = False


    def getGames(self, dt, league_season_id = ''):
        if not league_season_id:
            league_season_id = self.league_season['id']
        return self.dbobj.query_dict("""
            SELECT 
                g.*, 
                home_team.city home_team_city, 
                away_team.city away_team_city,
                home_team.cbssports_code as home_team_cbssports_code,
                away_team.cbssports_code as away_team_cbssports_code,
                s.name as season_name
            FROM game g 
                INNER JOIN league_season ls ON ls.id = g.league_season_id
                INNER JOIN season s ON s.id = ls.season_id
                INNER JOIN team home_team on home_team.id = g.home_team_id
                INNER JOIN team away_team on away_team.id = g.away_team_id
            WHERE g.date_played = '%s'
                AND g.should_fetch_data = 1
                AND g.league_season_id = %s
        """ % (dt, league_season_id))


    def getSeason(self, dt):
        data = self.dbobj.query_dict("""
            SELECT *
            FROM dim_season
            WHERE start_date <= '%s'
                AND end_date >= '%s'
        """ % (dt, dt))
        return data[0] if data else {}


    def getTeams(self, season):
        return self.dbobj.query_dict("""
            SELECT *
            FROM team
            WHERE league_season_id = '%s'
        """ % (season))


    def getPlayerResolveStrategy(self):
        results = self.dbobj.query_dict("""
            SELECT
                *
            FROM
                league_scrape_player_resolution
            WHERE
                league_id = %s
            ORDER BY
                is_primary DESC
        """ % (self.obj['id']))
        
        # flatten into primary/secondary
        obj = {'primary': '', 'secondary': []}
        for line in results:
            if line['is_primary'] == 1:
                obj['primary'] = line['source']
            else:
                obj['secondary'].append(line['source'])

        return obj


    def matchTeam(self, team_name, teams):
        print team_name
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



    def _getLeagueByName(self, name):
        query = self.dbobj.query_dict("SELECT * FROM league WHERE slug = '%s'" % (name))
        if query:
            return query[0]
        else:
            return False


    def _getLeagueById(self, id):
        query = self.dbobj.query_dict("SELECT * FROM league WHERE id = '%s'" % (id))
        if query:
            return query[0]
        else:
            return False


    def _getCurrentLeagueSeason(self):
        query = self.dbobj.query_dict("SELECT ls.*, s.name as season_name FROM league_season ls INNER JOIN season s ON s.id = ls.season_id WHERE ls.league_id = %s AND ls.is_current = 1" % (self.obj['id']))
        if query:
            return query[0]
        else:
            return False


    def _getLeagueSeason(self, league_season_id):
        query = self.dbobj.query_dict("SELECT ls.*, s.name as season_name FROM league_season ls INNER JOIN season s ON s.id = ls.season_id WHERE ls.id = %s" % (league_season_id))
        if query:
            return query[0]
        else:
            return False


    def getModules(self):
        data = self.dbobj.query_dict("""
            SELECT * 
            FROM league_season_scrape_module 
            WHERE league_season_id = %s 
                AND is_active = 1
        """ % (self.league_season['id']))
        return data




def main():
    dbobj = db.Db(config.config['db'])
    lgobj = League(dbobj)
    season = lgobj.getSeason('2014-04-19')
    print season



if __name__ == '__main__':
    main()


