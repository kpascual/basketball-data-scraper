def matchTeam(team_name, teams):
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

