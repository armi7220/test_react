#天気予報の詳細画面

import sys
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
import flet as ft
from services.jma_api import JmaApiService
from services.db_service import DatabaseService
from datetime import datetime


class WeatherDetailView(ft.Column):
    #天気予報詳細画面のクラス
    
    def __init__(self, page: ft.Page,area_code : str, on_back):
        
        #Columnの初期化
        super().__init__(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        
        # ページとコールバックを保存
        self._page = page
        self.area_code = area_code
        self.on_back = on_back
        
        #天気予報データ
        self.weather_data = None
        
        # データベースサービス
        self.db_service = DatabaseService(db_path='../weather.db')
        
        # 現在のタブ（0: 現在の予報, 1: 過去の履歴）
        self.current_tab = 0
        
        #ui要素
        self.build_ui()
        
        #天気予報データを読み込み
        self._load_weather()
    
    def build_ui(self):
        #ui要素を構築

        #タイトルバー（青のグラデーション背景）
        title_bar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: self.on_back(),
                        tooltip="地域選択に戻る",
                        icon_color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_700,
                    ),
                    ft.Icon(ft.Icons.CLOUD, color=ft.Colors.WHITE, size=28),
                    ft.Text(
                        "天気予報",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            bgcolor=ft.Colors.BLUE,
            padding=20,
            border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15),
        )
        
        # タブボタン
        self.tab_buttons = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        "現在の予報",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    bgcolor=ft.Colors.BLUE,
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                    on_click=lambda e: self._switch_tab(0),
                    expand=True,
                ),
                ft.Container(
                    content=ft.Text(
                        "過去の履歴",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    bgcolor=ft.Colors.BLUE_100,
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                    on_click=lambda e: self._switch_tab(1),
                    expand=True,
                ),
            ],
            spacing=5,
        )
        
        #コンテンツエリア（ローディング表示）
        self.content_column = ft.Column(
            controls=[
                ft.ProgressRing(color=ft.Colors.BLUE),
                ft.Text("天気予報を読み込んでいます...", color=ft.Colors.BLUE_900),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            expand=True,
        )    
    
        # 全てのコントロールをColumnに追加
        self.controls = [
            title_bar,
            ft.Container(height=10),  # スペース
            ft.Container(
                content=self.tab_buttons,
                padding=ft.padding.symmetric(horizontal=10),
            ),
            self.content_column,
        ]
        self.spacing = 0
        self.padding = 0
    
    def _switch_tab(self, tab_index):
        """タブを切り替える"""
        self.current_tab = tab_index
        
        # タブボタンの見た目を更新
        for i, container in enumerate(self.tab_buttons.controls):
            if i == tab_index:
                # アクティブなタブ
                container.bgcolor = ft.Colors.BLUE
                container.content.color = ft.Colors.WHITE
            else:
                # 非アクティブなタブ
                container.bgcolor = ft.Colors.BLUE_100
                container.content.color = ft.Colors.BLUE_700
        
        # コンテンツを切り替え
        if tab_index == 0:
            # 現在の予報を表示
            if self.weather_data:
                self._display_weather()
            else:
                self._load_weather()
        else:
            # 過去の履歴を表示
            self._display_history()
        
        self._safe_update()
    
    def _display_history(self):
        """過去の天気情報を表示"""
        self.content_column.controls.clear()
        
        # ローディング表示
        self.content_column.controls.append(
            ft.ProgressRing(color=ft.Colors.BLUE)
        )
        self.content_column.controls.append(
            ft.Text("履歴を読み込んでいます...", color=ft.Colors.BLUE_900)
        )
        self._safe_update()
        
        # データベースから履歴を取得
        history = self.db_service.get_weather_history(area_id=self.area_code, limit=50)
        
        self.content_column.controls.clear()
        
        if not history or len(history) == 0:
            self.content_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.HISTORY, size=64, color=ft.Colors.GREY),
                            ft.Text(
                                "この地域の履歴データがありません",
                                size=16,
                                color=ft.Colors.GREY_700,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=50,
                )
            )
        else:
            # 履歴データを表示
            self.content_column.controls.append(
                ft.Text(
                    f"過去の天気情報 ({len(history)}件)",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900,
                )
            )
            self.content_column.controls.append(ft.Divider())
            
            # 各履歴データをカードで表示
            for record in history:
                # record: (id, area_name, time, weather, min_temperature, max_temperature, wind, wave, rain_proba)
                history_card = self._create_history_card(
                    time_str=record[2],
                    weather=record[3],
                    min_temperature=record[4],
                    max_temperature=record[5],
                    wind=record[6],
                    wave=record[7],
                    rain_proba=record[8],
                )
                self.content_column.controls.append(history_card)
        
        self._safe_update()
    
    def _create_history_card(self, time_str, weather, min_temperature, max_temperature, wind, wave, rain_proba):
        """履歴カードを作成"""
        # 日時をフォーマット
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y年%m月%d日 %H:%M')
        except:
            date_str = time_str
        
        # 天気アイコンと色を選択
        weather_icon = ft.Icons.WB_SUNNY
        icon_color = ft.Colors.ORANGE
        
        if "雨" in weather or "雷" in weather:
            weather_icon = ft.Icons.WATER_DROP
            icon_color = ft.Colors.BLUE
        elif "曇" in weather:
            weather_icon = ft.Icons.CLOUD
            icon_color = ft.Colors.GREY
        elif "雪" in weather:
            weather_icon = ft.Icons.AC_UNIT
            icon_color = ft.Colors.CYAN
        elif "晴" in weather:
            weather_icon = ft.Icons.WB_SUNNY
            icon_color = ft.Colors.ORANGE
        
        # 気温表示
        if min_temperature is not None and max_temperature is not None:
            if min_temperature == max_temperature:
                temp_text = f"{max_temperature}℃"
            else:
                temp_text = f"{min_temperature}℃ / {max_temperature}℃"
        elif max_temperature is not None:
            temp_text = f"最高 {max_temperature}℃"
        elif min_temperature is not None:
            temp_text = f"最低 {min_temperature}℃"
        else:
            temp_text = "データなし"
        
        # 降水確率表示
        rain_text = f"{rain_proba}%" if rain_proba else "-"
        
        # カード作成
        card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(weather_icon, size=40, color=icon_color),
                    ft.Column(
                        controls=[
                            ft.Text(
                                date_str,
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                            ft.Text(
                                weather,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.THERMOSTAT, size=16, color=ft.Colors.RED),
                                    ft.Text(temp_text, size=12),
                                    ft.Container(width=10),
                                    ft.Icon(ft.Icons.WATER_DROP, size=16, color=ft.Colors.BLUE),
                                    ft.Text(rain_text, size=12),
                                ],
                                spacing=5,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=15,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=15,
            margin=ft.margin.only(bottom=10, left=10, right=10),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                offset=ft.Offset(0, 2),
            ),
        )
        
        return card
        
    def _load_weather(self):
        #天気予報データを読み込む
        print(f"🌤️ 天気予報を取得中: {self.area_code}")
        self.weather_data = JmaApiService().get_weather_forecast(self.area_code)
        
        if self.weather_data:
            print(" 天気予報取得成功")
            
            # データベースに保存
            try:
                # エリア名を取得
                area_name = "不明な地域"
                if self.weather_data and len(self.weather_data) > 0:
                    time_series = self.weather_data[0].get('timeSeries', [])
                    if time_series and len(time_series) > 0:
                        areas = time_series[0].get('areas', [])
                        if areas and len(areas) > 0:
                            area_name = areas[0].get('area', {}).get('name', area_name)
                
                # エリアをDBに登録
                area_db_id = self.db_service.insert_area(area_name, self.area_code)
                
                if area_db_id:
                    # 天気情報をDBに保存
                    saved_count = self.db_service.insert_or_update_weather_data(
                        area_db_id, 
                        self.weather_data
                    )
                    print(f"💾 データベースに{saved_count}件保存しました")
                else:
                    print("⚠️ エリアの登録に失敗しました")
                    
            except Exception as e:
                print(f"⚠️ データベース保存エラー: {e}")
            
            # 画面に表示
            self._display_weather()
        else:
            print("❌ 天気予報取得失敗")
            self.content_column.controls = [
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED),
                ft.Text(
                    "天気予報の取得に失敗しました",
                    size=18,
                    color=ft.Colors.RED,
                ),
                ft.ElevatedButton(
                    text="地域選択に戻る",
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda e: self.on_back(),
                ),
            ]
            self._safe_update()
            
    def _display_weather(self):
        #天気予報を表示
        
        self.content_column.controls.clear()
        
        #地域名を取得
        area_name = "不明な地域"
        publishing_office = ""
        
        if self.weather_data and len(self.weather_data) > 0:
            first_forecast = self.weather_data[0]
            publishing_office = first_forecast.get('publishingOffice', '')
            
            # timeSeries[0]のareasから地域名を取得
            try:
                time_series = first_forecast.get('timeSeries', [])
                if time_series and len(time_series) > 0:
                    areas = time_series[0].get('areas', [])
                    if areas and len(areas) > 0:
                        area_name = areas[0].get('area', {}).get('name', area_name)
            except Exception as e:
                print(f"地域名取得エラー: {e}")
        
        # 地域名表示
        self.content_column.controls.append(
            ft.Text(
                f"{area_name}",
                size=20,
                weight=ft.FontWeight.BOLD,
            )
        )
        
        # 発表者情報
        if publishing_office:
            self.content_column.controls.append(
                ft.Text(
                    f"発表: {publishing_office}",
                    size=12,
                    color=ft.Colors.GREY_700,
                )
            )
        
        self.content_column.controls.append(ft.Divider())
        
        # 天気予報がない場合
        if not self.weather_data or len(self.weather_data) == 0:
            self.content_column.controls.append(
                ft.Text("この地域の天気予報は利用できません")
            )
            self._safe_update()
            return
        
        # timeSeriesから天気予報データを取得(気温降水量、天気、風、波)
        try:
            first_forecast = self.weather_data[0]
            time_series = first_forecast.get('timeSeries', [])
            
            # 降水確率のデータを取得
            pops = []
            
            # 降水確率（timeSeries[1]）
            if len(time_series) > 1:
                pop_data = time_series[1].get('areas', [])
                if pop_data and len(pop_data) > 0:
                    pops = pop_data[0].get('pops', [])
            
            # 気温データを取得（timeSeries[2]）
            temp_min_max = []  # 最低気温と最高気温のペア
            
            if len(time_series) > 2:
                temp_series = time_series[2]
                temp_time_defines = temp_series.get('timeDefines', [])
                temp_areas = temp_series.get('areas', [])
                
                if temp_areas and len(temp_areas) > 0:
                    temps = temp_areas[0].get('temps', [])
                    
                    # 気温データは通常、[最低, 最高, 最低, 最高, ...] の順
                    # 各日の最低気温と最高気温をペアにする
                    for i in range(0, len(temps), 2):
                        if i + 1 < len(temps):
                            min_temp = temps[i] if temps[i] != '' else None
                            max_temp = temps[i + 1] if temps[i + 1] != '' else None
                            
                            # 両方のデータがある場合
                            if min_temp and max_temp:
                                # 最低と最高が同じ場合（お昼以降など）
                                if min_temp == max_temp:
                                    temp_min_max.append(f"最高: {max_temp}℃")
                                else:
                                    temp_min_max.append(f"{min_temp}℃ / {max_temp}℃")
                            # 最高気温のみの場合
                            elif max_temp and not min_temp:
                                temp_min_max.append(f"最高: {max_temp}℃")
                            # 最低気温のみの場合
                            elif min_temp and not max_temp:
                                temp_min_max.append(f"最低: {min_temp}℃")
                            # 両方ともない場合
                            else:
                                temp_min_max.append("気温情報なし")
                        elif i < len(temps):
                            # 1つだけの場合
                            if temps[i] != '':
                                temp_min_max.append(f"{temps[i]}℃")
                            else:
                                temp_min_max.append("気温情報なし")
            
            if time_series and len(time_series) > 0:
                # 最初のtimeSeriesから天気情報を取得
                ts_data = time_series[0]
                time_defines = ts_data.get('timeDefines', [])
                areas = ts_data.get('areas', []) 
                
                if areas and len(areas) > 0:
                    area_data = areas[0]
                    weathers = area_data.get('weathers', [])
                    winds = area_data.get('winds', [])
                    waves = area_data.get('waves', [])
                    
                    # 各時間帯の予報を表示（最大3件）
                    for i in range(min(3, len(time_defines))):
                        forecast_card = self._create_forecast_card(
                            time_defines[i] if i < len(time_defines) else None,
                            weathers[i] if i < len(weathers) else '情報なし',
                            winds[i] if i < len(winds) else '情報なし',
                            waves[i] if i < len(waves) else '情報なし',
                            temp_min_max[i] if i < len(temp_min_max) else '情報なし',
                            pops[i] if i < len(pops) else '情報なし'
                        )
                        self.content_column.controls.append(forecast_card)
                
        except Exception as e:
            print(f"天気予報表示エラー: {e}")
            self.content_column.controls.append(
                ft.Text(f"天気予報の表示中にエラーが発生しました: {e}")
            )
        
        # 更新ボタン
        self.content_column.controls.append(
            ft.ElevatedButton(
                text="天気予報を更新",
                icon=ft.Icons.REFRESH,
                on_click=self._on_refresh_clicked, 
            )
        )
        
        self._safe_update()
        
    def _on_refresh_clicked(self, e):
        """更新ボタンがクリックされた時の処理"""
        print("🔄 更新ボタンがクリックされました")
    
        # ローディング表示に戻す
        self.content_column.controls = [
            ft.ProgressRing(),
            ft.Text("天気予報を更新中..."),
        ]
        self._safe_update()
    
        # 天気予報を再取得
        self._load_weather()
        
    def _create_forecast_card(self, time_define, weather_text, wind_text, wave_text, temp_text, pop_text):
        """予報カードを作成（ExpansionTileで詳細表示）"""
        
        # 期間情報
        date_str = "日時不明"
        if time_define:
            try:
                dt = datetime.fromisoformat(time_define.replace('Z', '+00:00'))
                date_str = dt.strftime('%m月%d日 %H:%M')
            except:
                date_str = time_define
        
        # 天気アイコンと色を選択
        weather_icon = ft.Icons.WB_SUNNY
        icon_color = ft.Colors.ORANGE  # デフォルトは晴れ（オレンジ）
        
        if "雨" in weather_text or "雷" in weather_text:
            weather_icon = ft.Icons.WATER_DROP
            icon_color = ft.Colors.BLUE  # 雨は青
        elif "曇" in weather_text:
            weather_icon = ft.Icons.CLOUD
            icon_color = ft.Colors.GREY  # 曇りはグレー
        elif "雪" in weather_text:
            weather_icon = ft.Icons.AC_UNIT
            icon_color = ft.Colors.CYAN  # 雪はシアン（水色）
        elif "晴" in weather_text:
            weather_icon = ft.Icons.WB_SUNNY
            icon_color = ft.Colors.ORANGE  # 晴れはオレンジ
        else:
            weather_icon = ft.Icons.HELP_OUTLINE
            icon_color = ft.Colors.GREY  # その他はグレー
        
        # 基本情報（常に表示）
        summary_row = ft.Row(
            controls=[
                ft.Icon(weather_icon, size=32, color=icon_color),
                ft.Column(
                    controls=[
                        ft.Text(
                            weather_text,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            f"気温: {temp_text} | 降水確率: {pop_text}%",
                            size=12,
                            color=ft.Colors.GREY_700,
                        ),
                    ],
                    spacing=2,
                ),
            ],
            spacing=15,
        )
        
        # 詳細情報（展開時に表示）
        detail_controls = [
            ft.Divider(height=1),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.THERMOSTAT, size=20, color=ft.Colors.RED),
                title=ft.Text("気温（最低 / 最高）"),
                subtitle=ft.Text(f"{temp_text}"),
                dense=True,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.WATER_DROP, size=20, color=ft.Colors.BLUE),
                title=ft.Text("降水確率"),
                subtitle=ft.Text(f"{pop_text}%"),
                dense=True,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.AIR, size=20, color=ft.Colors.GREEN),
                title=ft.Text("風"),
                subtitle=ft.Text(wind_text),
                dense=True,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.WAVES, size=20, color=ft.Colors.CYAN),
                title=ft.Text("波"),
                subtitle=ft.Text(wave_text),
                dense=True,
            ),
        ]
        
        # ExpansionTileを作成（青のアクセント）
        expansion_tile = ft.ExpansionTile(
            title=ft.Text(
                date_str,
                size=14,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_900,
            ),
            subtitle=summary_row,
            controls=detail_controls,
        )
        
        # カードでラップ（白背景、影付き）
        card = ft.Container(
            content=expansion_tile,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=10,
            margin=ft.margin.only(bottom=10, left=10, right=10),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                offset=ft.Offset(0, 2),
            ),
        )
        
        return card
    
    def _safe_update(self):
        """安全にページを更新"""
        try:
            if self._page:
                self._page.update()
            else:
                self.update()
        except Exception as e:
            print(f"⚠️ 更新エラー: {e}")

# テストコード
if __name__ == "__main__":
    def test_back():
        """テスト用の戻るボタン"""
        print("⬅️ 戻るボタンがクリックされました")
    
    def main(page: ft.Page):
        """テスト用のメイン関数"""
        page.title = "天気予報詳細画面テスト"
        page.window.width = 600
        page.window.height = 800
        
        # 天気予報画面を作成（東京を例に）
        weather_view = WeatherDetailView(page, "130000", test_back)
        
        # ページに追加
        page.views.append(weather_view)
        page.update()
    
    # アプリを起動
    ft.run(target=main)