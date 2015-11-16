import unittest
import extract.playbyplay_espn
import copy


class TestPlayByPlayEspn(unittest.TestCase):
    def setUp(self):
        html = ''
        filename = ''
        self.gamedata = {
            'id': 1234
        }

        self.obj = extract.playbyplay_espn.Extract(html, filename, self.gamedata)


    def test1(self):
        self.assertEqual(1, 1)
