#地域選択画面

import sys
from pathlib import Path

# このファイルを直接実行する場合、親ディレクトリをパスに追加
if __name__ == "__main__":
    # 現在のファイルの親の親ディレクトリ（weather-forecast-app）をパスに追加
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

import flet as ft
from services.jma_api import JmaApiService

class AreaListView(ft.Column):
    #地域選択画面のクラス
    
    def __init__(self, page: ft.Page, on_area_selected):
        
        #Columnの初期化（最初に呼ぶ）
        super().__init__(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        
        #ページとコールバックを保存
        self._page = page
        self.on_area_selected = on_area_selected
        
        #地域データ
        self.areas_data = None
        
        #検索用
        self.search_query = ""
        
        #UI要素
        self.search_field = None
        self.area_list_column = None
        
        #UIを構築
        self.build_ui()
        
        #地域データの読み込み
        self._load_areas()
        
    def build_ui(self):
        #uiの構築
        
        # タイトルバー（青のグラデーション背景）
        title_container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WB_SUNNY, color=ft.Colors.WHITE, size=32),
                    ft.Text(
                        "地域を選択してください",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.BLUE,
            padding=20,
            border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15),
        )
        
        #検索ボックス（角丸と影を追加）
        self.search_field = ft.TextField(
            label='地域名で検索',
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._on_search_changed,
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.BLUE_200,
            focused_border_color=ft.Colors.BLUE,
        )
        
        #地域名リストのカラム
        self.area_list_column = ft.Column(
            controls=[
                ft.ProgressRing(color=ft.Colors.BLUE)
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        
        #全てのコントロールをColumnに追加
        self.controls = [
            title_container,
            ft.Container(height=10),  # スペース
            self.search_field,
            ft.Container(height=10),  # スペース
            self.area_list_column,
        ]
        self.spacing = 0
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.padding = 0
        
    def _load_areas (self):
        #地域データの読み込み（FROM　API）
        self.areas_data = JmaApiService.get_area_list()
        
        if self.areas_data:
            
            self._display_areas()
        else:
            self.area_list_column.controls = [
                ft.Text(
                    "地域リストの取得に失敗しました",
                    color = ft.colors.RED,
                )
            ]
            self._safe_update()
            
    def _display_areas(self):
        #地域リストを表示（ExpansionTileでグループ化）
        
        self.area_list_column.controls.clear()
        
        # centersから地方情報を取得
        centers = self.areas_data.get('centers', {})
        
        # officesから地域を取得
        offices = self.areas_data.get('offices', {})
        
        # 地方ごとにExpansionTileを作成
        for center_code, center_info in centers.items():
            center_name = center_info.get('name', '不明な地方')
            children_codes = center_info.get('children', [])
            
            # この地方に属する地域のリストを作成
            region_tiles = []
            
            for area_code in children_codes:
                if area_code in offices:
                    area_info = offices[area_code]
                    area_name = area_info.get('name', '不明')
                    
                    # 検索フィルターを適用
                    if self.search_query and self.search_query.lower() not in area_name.lower():
                        continue
                    
                    
                    # 地域のListTile（白背景のカード風）
                    area_tile = ft.Container(
                        content=ft.ListTile(
                            title=ft.Text(area_name, size=14, weight=ft.FontWeight.W_500),
                            subtitle=ft.Text(f"コード: {area_code}", size=11, color=ft.Colors.GREY_700),
                            leading=ft.Icon(ft.Icons.LOCATION_ON, size=20, color=ft.Colors.BLUE),
                            on_click=lambda e, code=area_code: self._on_area_clicked(code),
                            dense=True,
                        ),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=8,
                        margin=ft.margin.only(bottom=5),
                        padding=ft.padding.all(5),
                    )
                    
                    region_tiles.append(area_tile)
            
            # 地域が見つからない場合はスキップ
            if not region_tiles:
                continue
            
            # ExpansionTile を作成（青のアクセント）
            expansion_tile = ft.Container(
                content=ft.ExpansionTile(
                    title=ft.Text(
                        center_name,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_900,
                    ),
                    subtitle=ft.Text(f"{len(region_tiles)}地域", size=12, color=ft.Colors.BLUE_700),
                    leading=ft.Icon(ft.Icons.MAP, color=ft.Colors.BLUE, size=28),
                    controls=region_tiles,
                ),
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                margin=ft.margin.only(bottom=10, left=10, right=10),
                padding=ft.padding.all(5),
            )
            
            self.area_list_column.controls.append(expansion_tile)
        
        # 地域が見つからないとき
        if not self.area_list_column.controls:
            self.area_list_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=ft.Colors.GREY),
                            ft.Text(
                                "該当する地域が見つかりません",
                                size=14,
                                color=ft.Colors.GREY,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=30,
                )
            )
        
        self._safe_update()
    
    
    def _on_area_clicked(self, area_code):
        #地域がクリックされた時 - すぐに天気予報を表示
        
        print(f"🌍 地域が選択されました: {area_code}")
        
        # すぐに天気予報を表示
        if self.on_area_selected:
            self.on_area_selected(area_code)
        
        
    def _on_search_changed(self,e):
        #検索ボックスの内容が変更されたとき
        
        self.search_query = e.control.value
        self._display_areas()
        
    def _safe_update(self):
        """安全にページを更新"""
        try:
            if self._page:
                self._page.update()
            else:
                self.update()
        except Exception as e:
            print(f"⚠️ 更新エラー: {e}")
            
#テストコード
if __name__ == "__main__":
    def test_area_selected(area_code):
        """テスト用のコールバック関数"""
        print(f"✅ 地域が選択されました: {area_code}")
    
    def main(page: ft.Page):
        """テスト用のメイン関数"""
        page.title = "地域選択画面テスト"
        page.window.width = 500
        page.window.height = 700
        
        # 地域選択画面を作成
        area_list_view = AreaListView(page, test_area_selected)
        
        # ページに追加
        page.views.append(area_list_view)
        page.update()
    
    # アプリを起動
    ft.run(target=main)