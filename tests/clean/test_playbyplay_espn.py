import unittest
import clean.playbyplay_espn
import copy


class TestPlayByPlayEspn(unittest.TestCase):
    def setUp(self):
        filename = ''
        self.gamedata = {
            'id': 1234
        }
        dbobj = {}

        self.obj = clean.playbyplay_espn.Clean(filename, self.gamedata, dbobj)

    def testUnknownQuarters(self):
        missing = [
            {'period': 1},
            {'period': 1},
            {'period': 1},
            {'period': 'check quarter'},
        ]
        expected = [
            {'period': 1},
            {'period': 1},
            {'period': 1},
            {'period': 1},
        ]
        self.assertEqual(self.obj.guessUnknownQuarters(missing), expected)

    def testUnknownQuartersWithChange(self):
        missing = [
            {'period': 1},
            {'period': 1},
            {'period': 2},
            {'period': 'check quarter'},
        ]
        expected = [
            {'period': 1},
            {'period': 1},
            {'period': 2},
            {'period': 2},
        ]
        self.assertEqual(self.obj.guessUnknownQuarters(missing), expected)

    def testBlankScoresConvertedToZero(self):
        data = [
            {'away_score': '', 'home_score': ''},
        ]
        expected = [
            {'away_score': 0, 'home_score': 0},
        ]
        self.assertEqual(self.obj.replaceBlankScores(data), expected)

    def testBlankScoresOneScoreMissing(self):
        data1 = [
            {'away_score': 0, 'home_score': ''},
        ]
        data2 = [
            {'away_score': '', 'home_score': 0},
        ]
        expected = [
            {'away_score': 0, 'home_score': 0},
        ]
        self.assertEqual(self.obj.replaceBlankScores(data1), expected)
        self.assertEqual(self.obj.replaceBlankScores(data2), expected)

    def testMissingScoresInheritFromPriorScore(self):
        data = [
            {'away_score': 2, 'home_score': 1},
            {'away_score': '', 'home_score': ''},
        ]
        expected = [
            {'away_score': 2, 'home_score': 1},
            {'away_score': 2, 'home_score': 1},
        ]
        self.assertEqual(self.obj.replaceBlankScores(data), expected)


    def testMissingScoresInAllData(self):
        data = [
            {'away_score': 2, 'home_score': ''},
            {'away_score': '', 'home_score': ''},
        ]
        expected = [
            {'away_score': 2, 'home_score': 0},
            {'away_score': 2, 'home_score': 0},
        ]
        self.assertEqual(self.obj.replaceBlankScores(data), expected)


    def testConformedTimeRemovesTimeLeft(self):
        data = [
            {'time_left': '1:00'}
        ]
        self.assertEqual(len(self.obj.replaceWithConformedTime(copy.deepcopy(data))), 1)
        self.assertTrue('time_left' not in self.obj.replaceWithConformedTime(copy.deepcopy(data))[0].keys())

    def testConformedTimeParsesDoubleDigitMinuteSeconds(self):
        data = [
            {'time_left': '12:45'}
        ]
        expected = [
                {'deciseconds_left': 7650}
        ]
        self.assertEqual(self.obj.replaceWithConformedTime(data), expected)


    def testConformedTimeParsesSecondsOnly(self):
        data = [
            {'time_left': '0:40'}
        ]
        expected = [
                {'deciseconds_left': 400}
        ]
        self.assertEqual(self.obj.replaceWithConformedTime(data), expected)


    def testGameIdAdded(self):
        data = [
            {}
        ]
        expected = [
            {'game_id': self.gamedata['id']}
        ]
        self.assertEqual(self.obj.addGameId(data), expected)


    def testRequiredFieldsNotEmpty(self):
        data = [
            {}
        ]
        expected = [
            {'player_id': -1, 'assist_player_id': -1, 'player1_id': -1, 'player2_id': -1}
        ]
        self.assertEqual(self.obj.fillInEmptyFields(data), expected)


    def testRequiredFieldsFillSome(self):
        data = [
            {'player_id': 567}
        ]
        expected = [
            {'player_id': 567, 'assist_player_id': -1, 'player1_id': -1, 'player2_id': -1}
        ]
        self.assertEqual(self.obj.fillInEmptyFields(data), expected)


    def testResolvePlayDescriptionReturnsAway(self):
        away = 'away description'
        home = ''
        self.assertEqual(self.obj._resolvePlayDescription(away, home), away)

    def testResolvePlayDescriptionReturnsHome(self):
        away = ''
        home = 'home description'
        self.assertEqual(self.obj._resolvePlayDescription(away, home), home)
