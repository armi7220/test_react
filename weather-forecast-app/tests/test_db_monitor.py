import unittest
import sys
import os

# プロジェクトルートにパスを通す
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService

class TestDbMonitor(unittest.TestCase):
    def setUp(self):
        """テストごとに専用のDBでDatabaseServiceを初期化"""
        self.test_db_path = "test_weather.db"
        self.db = DatabaseService(db_path=self.test_db_path)
        self.db.init_database()

    def tearDown(self):
        """テスト終了後にテスト用DBを削除"""
        # SQLiteのコネクション解放待ちのため少し安全に消す
        import time
        time.sleep(0.1)
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services", self.test_db_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    def test_insert_and_get_area(self):
        """エリアの登録と取得が正常に行えるか"""
        area_id = self.db.insert_area("東京都", "130000")
        self.assertIsNotNone(area_id, "エリアの登録に失敗しました。")
        
        # 同じエリアを再度登録した場合は同じIDが返るか（重複登録ハンドリングの検証）
        area_id_dup = self.db.insert_area("東京都", "130000")
        self.assertEqual(area_id, area_id_dup, "重複エリアの登録で異なるIDが返されました。")

    def test_insert_weather_data(self):
        """天気データの挿入がエラーなく行えるか"""
        area_db_id = self.db.insert_area("東京都", "130000")
        
        # 気象庁APIのレスポンス形式を模倣したダミーデータ
        dummy_weather = [{
            "timeSeries": [
                {
                    "timeDefines": ["2026-07-10T00:00:00+09:00"],
                    "areas": [{"weathers": ["晴れ"], "winds": ["北の風"], "waves": ["波の高さ1メートル"]}]
                },
                {
                    "timeDefines": ["2026-07-10T00:00:00+09:00"],
                    "areas": [{"pops": ["10"]}]
                },
                {
                    "timeDefines": ["2026-07-10T00:00:00+09:00", "2026-07-10T09:00:00+09:00"],
                    "areas": [{"temps": ["25", "30"]}]
                }
            ]
        }]
        
        count = self.db.insert_or_update_weather_data(area_db_id, dummy_weather)
        self.assertGreater(count, 0, "天気データの保存に失敗しました。")
        
        # 保存したデータの取得
        history = self.db.get_weather_history(area_id="130000", limit=10)
        self.assertEqual(len(history), 1, "保存した履歴が取得できません。")
        self.assertEqual(history[0][1], "東京都")
        self.assertEqual(history[0][3], "晴れ")
