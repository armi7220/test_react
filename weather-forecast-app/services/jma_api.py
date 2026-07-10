# 気象庁APIとの通信

import requests

class JmaApiService:
    
    AREA_LIST_URL = 'http://www.jma.go.jp/bosai/common/const/area.json'
    FORECAST_URL = 'https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json' 
    
    @staticmethod
    def get_area_list():
        try:
            print("地域リストを取得中")
            response = requests.get(
                JmaApiService.AREA_LIST_URL,
                timeout = 10
            )
            
            response.raise_for_status()
            
            print('地域リスト取得成功')
            return response.json()
        
        except requests.exceptions.Timeout:
            print('エラー：タイムアウト（10秒以上応答なし）')
            return None
        
        except requests.exceptions.ConnectionError:
            print('エラー：ネットワーク接続に失敗')
            return None
        
        except requests.exceptions.HTTPError as e:
            print(f'HTTPエラー：{e}')
            return None
        
        except Exception as e:
            print(f'エラー：予期しないエラー:{e}')
            return None
        
    @staticmethod
    def get_weather_forecast(area_code):
        try:
            url = JmaApiService.FORECAST_URL.format(area_code = area_code)
            print(f"天気予報を取得中（地域コード:{area_code}）")
            
            response = requests.get(url,timeout = 10)
            response.raise_for_status()
            
            print("天気予報取得成功")
            return response.json()
        
        except requests.exceptions.Timeout:
            print('エラー：タイムアウト（10秒以上応答なし）')
            return None
        
        except requests.exceptions.ConnectionError:
            print('エラー：ネットワーク接続に失敗')
            return None
        
        except requests.exceptions.HTTPError as e:
            print(f'HTTPエラー：{e}')
            return None
        
        except Exception as e:
            print(f'エラー：予期しないエラー:{e}')
            return None
    
#テストコード1地域リスト取得
if __name__ == "__main__":
    print("=" * 60)
    print("気象庁API 動作確認テスト")
    print("=" * 60)
    print()
    
    #地域リスト取得
    print("地域リストを取得中")
    print("=" * 60)

    areas = JmaApiService.get_area_list()

    if areas:
        print(f"結果")
        print(f" - centers (地方){len(areas.get('centers',[]))}件")
        print(f"offices （地域）{len(areas.get('offices',{}))}件")
        print(f"  - class10s {len(areas.get('class10s', {}))}件")
        print(f"  - class15s: {len(areas.get('class15s', {}))}件")
        print(f"  - class20s {len(areas.get('class20s', {}))}件")
    
        print('地域の例（最初５件）')
        for i, (code,info) in enumerate(list(areas.get('offices',{}).items())[:5]):
            print(f"{i+1}.{info['name']:15}(コード：{code}")
        
    else:
        print("地域リストの取得に失敗しました")
        
    print("=" * 60)
    print()


    #テストコード２ 東京都の天気予報を取得
    print("東京都の天気予報を取得")
    print("-"*60)
    
    tokyo_code = "130000"
    weather = JmaApiService.get_weather_forecast(tokyo_code)
    
    if weather:
        print(f"\n📊 結果:")
        print(f"  - 発表官署 {weather[0].get('publishingOffice', 'N/A')}")
        print(f"  - 報告日時 {weather[0].get('reportDatetime', 'N/A')}")
        
        #詳細を取得
        try:
            time_series = weather[0]['timeSeries'][0]
            areas_data = time_series['areas'][0]
        
            print("天気予報")
            for i, time_define in enumerate(time_series['timeDefines'][:3]):
                weather_text = areas_data['weathers'][i] if i < len(areas_data['weathers']) else "情報なし"
                print(f"{i+1}. {time_define} {weather_text}")
        
        except Exception as e:
            print(f"天気予報取得エラー: {e}")
    
    else:
        print("天気予報の取得に失敗しました")
    
    print("=" * 60)
    print("テスト終了")
    print()
            
            
            