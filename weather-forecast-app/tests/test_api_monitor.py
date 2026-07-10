import unittest
import sys
import os

# プロジェクトルートにパスを通す
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.jma_api import JmaApiService

class TestApiMonitor(unittest.TestCase):
    def test_get_area_list(self):
        """気象庁APIから地域リストが正常に取得できるか"""
        areas = JmaApiService.get_area_list()
        self.assertIsNotNone(areas, "地域リストの取得に失敗しました。APIがダウンしている可能性があります。")
        self.assertIn("centers", areas, "レスポンスに 'centers' が含まれていません。")
        self.assertIn("offices", areas, "レスポンスに 'offices' が含まれていません。")

    def test_get_weather_forecast_tokyo(self):
        """東京の天気予報が正常に取得できるか"""
        tokyo_code = "130000"
        weather = JmaApiService.get_weather_forecast(tokyo_code)
        self.assertIsNotNone(weather, "天気予報の取得に失敗しました。")
        self.assertTrue(len(weather) > 0, "天気予報の配列が空です。")
        self.assertIn("timeSeries", weather[0], "予報データに 'timeSeries' が含まれていません。")
