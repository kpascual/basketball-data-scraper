import db
import sqlite3
from config import config

class League:

    def __init__(self, name = '', league_id = ''):
        self.sqlite_obj = db.DbLite()
        self.name = name

        if name:
            self.obj = self._getLeagueByName(name)
            self.name = self.obj['name']
        elif league_id:
            self.obj = self._getLeagueById(league_id)
            self.name = self.obj['name']
        else:
            self.obj = None


    def getGames(self, dt, league_season_id):
        return self.sqlite_obj.query_dict("""
            SELECT 
                g.*, 
                g.date_played || '_' || away_team.code || '@' || home_team.code || '_' || g.id abbrev,
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
            WHERE g.date_played = ?
                AND g.should_fetch_data = 1
                AND g.league_season_id = ?
        """, (dt, league_season_id))


    def getTeams(self, league_season_id):
        self.sqlite_obj['curs'].execute("""
            SELECT *
            FROM team
            WHERE league_season_id = ? 
        """, (league_season_id,))
        return  self.sqlite_obj['curs'].fetchall()


    def matchTeam(self, team_name, teams):
        print team_name
        for team in teams:
            if team_name == team['name']:
                return team
            elif team_name == team['nickname']:
                return team
            elif team_name == team['alternate_nickname']:
                return team
            elif team_name == team['city']:
                return team

        return False


    def getLeagueSeasons(self):
        if self.obj:
            data = self.sqlite_obj.query_dict("""
                SELECT ls.*, s.name as season_name
                FROM 
                    league_season ls
                    INNER JOIN season s ON s.id = ls.season_id
                WHERE 
                    ls.league_id = ?
            """, (self.obj['id'], ))
            if data:
                return data
            else:
                return False

        return False


    def _getLeagueSeason(self, league_season_id):
        if self.obj:
            self.sqlite_obj['curs'].execute("""
                SELECT ls.*, s.name as season_name
                FROM 
                    league_season ls
                    INNER JOIN season s ON s.id = ls.season_id
                WHERE 
                    WHERE id = ?
            """, (league_season_id, ))
            data = self.sqlite_obj['curs'].fetchone()
            if data:
                return data
            else:
                return False

        return False


    def _getLeagueByName(self, name):
        data = self.sqlite_obj.query("SELECT * FROM league WHERE slug = ?", (name, ))
        if data:
            return data
        else:
            return False


    def _getLeagueById(self, id):
        data = self.sqlite_obj.query_dict("SELECT * FROM league WHERE id = ?", (id, ))
        print data
        if data:
            return data[0]
        else:
            return False


    def getModules(self, league_season_id):
        data = self.sqlite_obj.query_dict("""
            SELECT * 
            FROM league_season_scrape_module 
            WHERE league_season_id = ?
        """, (league_season_id, ))
        if data:
            return data
        else:
            return False




def main():
    lgobj = League('nba')
    data = lgobj.getGames('2015-04-01', 5)
    for row in data:
        print dict(zip(row.keys(), row))



if __name__ == '__main__':
    main()


