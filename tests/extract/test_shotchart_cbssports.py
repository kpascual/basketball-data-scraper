import unittest
import extract.shotchart_cbssports
import copy


class TestShotchartCbssports(unittest.TestCase):
    def setUp(self):
        html = ''
        filename = ''
        self.gamedata = {
            'id': 1234
        }

        self.obj = extract.shotchart_cbssports.ShotExtract(html, filename, self.gamedata)


    def test1(self):
        self.assertEqual(1, 1)
