# 天気予報アプリケーション・改良版

気象庁APIを利用した天気予報アプリケーションに、SQLiteデータベース機能を追加

## 実装機能

- **天気情報のDB格納**: 気象庁APIから取得したデータをSQLiteに保存（JSON→DBへ移行）
- **過去の天気予報の閲覧**: タブ切り替えで過去に取得した天気情報を表示
- **データの自動更新**: 更新ボタンで最新情報を取得し、DBに反映

## DB設計

### テーブル構造

**areaテーブル**
- `id`: プライマリーキー（AUTOINCREMENT）
- `area_name`: 地域名
- `area_id`: 地域コード（UNIQUE制約）

**weather_infoテーブル**
- `id`: プライマリーキー（AUTOINCREMENT）
- `time`: 予報日時
- `min_temperature`: 最低気温
- `max_temperature`: 最高気温
- `wind`: 風の情報
- `wave`: 波の情報
- `rain_proba`: 降水確率
- `weather`: 天気
- `area_id`: 外部キー（area.idを参照）

## ファイル構造

```
lecture6_task3/
├── weather-forecast-app/
│   ├── main.py                    # アプリケーションのエントリーポイント
│   ├── services/
│   │   ├── jma_api.py            # 気象庁API通信
│   │   └── db_service.py         # データベース操作
│   ├── views/
│   │   ├── area_list.py          # 地域選択画面
│   │   └── weather_detail.py     # 天気詳細画面
│   └── weather.db                # SQLiteDB
├── auto_update.py                # 全地域自動更新スクリプト
└── README.md
```                     

### 操作方法
1. 地域リストから見たい地域をクリック
2. 「現在の予報」タブで最新の天気予報を表示
3. 「過去の履歴」タブで過去の天気情報を閲覧
4. 「天気予報を更新」ボタンで最新情報を取得

