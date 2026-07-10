import time
from datetime import datetime
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'weather-forecast-app'))

from services.jma_api import JmaApiService
from services.db_service import DatabaseService


def update_all_areas():
    print(f"\n{'='*60}")
    print(f" 全地域の天気情報を更新")
    print(f" 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # データベースパスを絶対パスで指定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'weather-forecast-app', 'weather.db')
    
    # データベースサービスを初期化
    db_service = DatabaseService(db_path=db_path)
    
    # 全地域リストを取得
    areas_json = JmaApiService.get_area_list()
    
    if not areas_json:
        print(" 地域リストの取得に失敗しました")
        return
    
    offices = areas_json.get('offices', {})
    total = len(offices)
    success_count = 0
    error_count = 0
    
    print(f" 対象地域数: {total}件\n")
    
    # 各地域の天気情報を取得
    for idx, (area_code, area_info) in enumerate(offices.items(), 1):
        area_name = area_info['name']
        
        print(f"[{idx}/{total}] {area_name} (コード: {area_code})")
        
        try:
            # エリアを登録
            area_db_id = db_service.insert_area(area_name, area_code)
            
            if area_db_id:
                # 天気予報を取得
                weather_json = JmaApiService.get_weather_forecast(area_code)
                
                if weather_json:
                    # 天気情報をDBに保存
                    result = db_service.insert_or_update_weather_data(area_db_id, weather_json)
                    if result > 0:
                        print(f" {result}件保存")
                        success_count += 1
                    else:
                        print(f"保存失敗")
                        error_count += 1
                else:
                    print(f" 天気情報の取得に失敗")
                    error_count += 1
            else:
                print(f" エリアの登録に失敗")
                error_count += 1
                
        except Exception as e:
            print(f" エラー: {e}")
            error_count += 1
        
        time.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f" 更新結果")
    print(f" 成功: {success_count}件")
    print(f" 失敗: {error_count}件")
    print(f"{'='*60}\n")


def auto_update_loop(interval_hours=6):
    print(" 天気情報自動更新サービスを開始します")
    print(f" 更新間隔: {interval_hours}時間ごと")
    print(f"停止するには Ctrl+C を押してください\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n{'#'*60}")
            print(f"# 第{iteration}回 更新")
            print(f"{'#'*60}")
            
            # 全地域を更新
            update_all_areas()
            
            # 次回更新まで待機
            next_update = datetime.fromtimestamp(time.time() + interval_hours * 3600)
            print(f"次回更新予定: {next_update.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f" {interval_hours}時間待機中...\n")
            
            time.sleep(interval_hours * 3600)
            
    except KeyboardInterrupt:
        print("\n\n 自動更新サービスを停止しました")
        print(f" 合計 {iteration}回の更新を実行しました")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='天気情報自動更新サービス')
    parser.add_argument(
        '--interval',
        type=int,
        default=6,
        help='更新間隔（時間）デフォルト: 6時間'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='1回だけ更新して終了'
    )
    
    args = parser.parse_args()
    
    if args.once:
        # 1回だけ更新
        update_all_areas()
    else:
        # 定期的に更新
        auto_update_loop(interval_hours=args.interval)
