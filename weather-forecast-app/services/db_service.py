import sqlite3
import os


class DatabaseService:
    def __init__(self, db_path='../weather.db'):
        if db_path == ':memory:':
            self.db_path = db_path
        else:
            self.db_path = os.path.join(os.path.dirname(__file__), db_path)
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS area (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    area_name TEXT NOT NULL,
                    area_id TEXT NOT NULL UNIQUE
                )
            """)
            
            # weather_infoテーブルを作成
            cur.execute("""
                CREATE TABLE IF NOT EXISTS weather_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TEXT NOT NULL,
                    min_temperature REAL,
                    max_temperature REAL,
                    wind TEXT,
                    wave TEXT,
                    rain_proba INTEGER,
                    weather TEXT NOT NULL,
                    area_id INTEGER NOT NULL,
                    FOREIGN KEY (area_id) REFERENCES area(id)
                )
            """)
            
            conn.commit()
            print("データベースを初期化しました")
            
        except Exception as e:
            print(f"データベース初期化エラー: {e}")
        finally:
            conn.close()
    
    def insert_area(self, area_name, area_id):
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # 既に存在するか確認
            cur.execute("SELECT id FROM area WHERE area_id = ?", (area_id,))
            result = cur.fetchone()
            
            if result:
                return result[0]
            
            # 新規登録
            cur.execute(
                "INSERT INTO area (area_name, area_id) VALUES (?, ?)",
                (area_name, area_id)
            )
            conn.commit()
            return cur.lastrowid
            
        except sqlite3.Error as e:
            print(f"エリア登録エラー: {e}")
            return None
        finally:
            conn.close()
    
    def insert_or_update_weather_data(self, area_db_id, weather_json):
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # 天気予報データを解析
            time_series = weather_json[0]['timeSeries']
            
            # 天気・風・波のデータ（timeSeries[0]）
            weather_data = time_series[0]
            time_defines = weather_data['timeDefines']
            area_data = weather_data['areas'][0]
            
            # 降水確率データを辞書形式で保存（timeSeries[1]）
            rain_dict = {}
            if len(time_series) > 1 and 'pops' in time_series[1]['areas'][0]:
                rain_data = time_series[1]
                rain_time_defines = rain_data.get('timeDefines', [])
                rain_area = rain_data['areas'][0]
                
                for i, rain_time in enumerate(rain_time_defines):
                    if 'pops' in rain_area and i < len(rain_area['pops']):
                        rain_proba_str = rain_area['pops'][i]
                        if rain_proba_str and rain_proba_str != '':
                            rain_dict[rain_time] = int(rain_proba_str)
            
            # 気温データを日付ベースで辞書に保存（timeSeries[2]）
            temp_dict = {}
            if len(time_series) > 2 and 'temps' in time_series[2]['areas'][0]:
                temp_data = time_series[2]
                temp_time_defines = temp_data.get('timeDefines', [])
                temp_area = temp_data['areas'][0]
                
                for i, temp_time in enumerate(temp_time_defines):
                    # 日付部分を抽出
                    date_part = temp_time.split('T')[0]
                    
                    if 'temps' in temp_area and i < len(temp_area['temps']):
                        temp_str = temp_area['temps'][i]
                        if temp_str and temp_str != '':
                            if date_part not in temp_dict:
                                temp_dict[date_part] = []
                            temp_dict[date_part].append(float(temp_str))
            
            # 最低気温と最高気温を計算
            min_max_temp_dict = {}
            for date, temps in temp_dict.items():
                min_max_temp_dict[date] = {
                    'min': min(temps) if temps else None,
                    'max': max(temps) if temps else None
                }
            
            inserted_count = 0
            updated_count = 0
            
            # 各時間帯のデータを挿入または更新
            for i, time_define in enumerate(time_defines):
                # 天気
                weather = None
                if 'weathers' in area_data and i < len(area_data['weathers']):
                    weather = area_data['weathers'][i]
                
                # 風
                wind = None
                if 'winds' in area_data and i < len(area_data['winds']):
                    wind = area_data['winds'][i]
                
                # 波
                wave = None
                if 'waves' in area_data and i < len(area_data['waves']):
                    wave = area_data['waves'][i]
                
                # 降水確率を取得
                rain_proba = rain_dict.get(time_define)
                
                # 日付部分を抽出して気温を取得
                date_part = time_define.split('T')[0]
                min_temp = min_max_temp_dict.get(date_part, {}).get('min')
                max_temp = min_max_temp_dict.get(date_part, {}).get('max')
                
                # データベースに挿入または更新（天気情報がある場合のみ）
                if weather:
                    # 既存のデータを確認
                    cur.execute("""
                        SELECT id FROM weather_info 
                        WHERE area_id = ? AND time = ?
                    """, (area_db_id, time_define))
                    
                    existing = cur.fetchone()
                    
                    if existing:
                        # 更新
                        cur.execute("""
                            UPDATE weather_info 
                            SET min_temperature = ?, max_temperature = ?, wind = ?, wave = ?, rain_proba = ?, weather = ?
                            WHERE id = ?
                        """, (min_temp, max_temp, wind, wave, rain_proba, weather, existing[0]))
                        updated_count += 1
                    else:
                        # 新規挿入
                        cur.execute("""
                            INSERT INTO weather_info 
                            (time, min_temperature, max_temperature, wind, wave, rain_proba, weather, area_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (time_define, min_temp, max_temp, wind, wave, rain_proba, weather, area_db_id))
                        inserted_count += 1
            
            conn.commit()
            return inserted_count + updated_count
            
        except Exception as e:
            print(f"天気情報挿入エラー: {e}")
            return 0
        finally:
            conn.close()
    
    def get_weather_history(self, area_id=None, limit=100):
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            if area_id:
                cur.execute("""
                    SELECT w.id, a.area_name, w.time, w.weather, w.min_temperature, 
                           w.max_temperature, w.wind, w.wave, w.rain_proba
                    FROM weather_info w
                    JOIN area a ON w.area_id = a.id
                    WHERE a.area_id = ?
                    ORDER BY w.time DESC
                    LIMIT ?
                """, (area_id, limit))
            else:
                cur.execute("""
                    SELECT w.id, a.area_name, w.time, w.weather, w.min_temperature, 
                           w.max_temperature, w.wind, w.wave, w.rain_proba
                    FROM weather_info w
                    JOIN area a ON w.area_id = a.id
                    ORDER BY w.time DESC
                    LIMIT ?
                """, (limit,))
            
            return cur.fetchall()
            
        except Exception as e:
            print(f"天気情報取得エラー: {e}")
            return []
        finally:
            conn.close()
