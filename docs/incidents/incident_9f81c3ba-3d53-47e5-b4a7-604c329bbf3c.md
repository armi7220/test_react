## インシデントレポート: `KeyError` による天気予報取得失敗

### 概要
本番環境のCI/CDパイプラインで実行されたテストジョブ `test` において、`TestApiMonitor.test_get_weather_forecast_tokyo` が `AssertionError` で失敗しました。根本原因は、`JmaApiService.get_weather_forecast` メソッド内でAPIリクエストURLのフォーマット文字列とキーワード引数の不一致による `KeyError` でした。これによりAPIリクエストが正しく構築されず、`None` が返されたため、テストの `assertIsNotNone` が失敗しました。

### 根本原因
`weather-forecast-app/services/jma_api.py` 内の `JmaApiService.get_weather_forecast(code)` メソッドにおいて、`JmaApiService.FORECAST_URL` に定義されているURLプレースホルダーが `{area_code}` であるにも関わらず、`str.format()` メソッドが `areacode = code` という誤ったキーワード引数で呼び出されていました。このキーワード引数の不一致により `KeyError: 'area_code'` が発生し、`requests.get` が実行される前に例外が捕捉され、結果として `None` が返されていました。

### 影響
- `TestApiMonitor.test_get_weather_forecast_tokyo` テストが失敗。
- アプリケーションが天気予報を取得しようとした際に、同様の `KeyError` が発生し、機能不全に陥る可能性。

### 修正内容
1.  **`weather-forecast-app/services/jma_api.py`**: `JmaApiService.get_weather_forecast` メソッド内のURL生成部分を修正しました。
    - 変更前: `url = JmaApiService.FORECAST_URL.format(areacode = code)`
    - 変更後: `url = JmaApiService.FORECAST_URL.format(area_code = code)`
    これにより、URLプレースホルダー `{area_code}` とキーワード引数 `area_code` が一致するようになり、URLが正しくフォーマットされるようになりました。

### 再発防止策
- **コードレビューの強化**: 特に文字列フォーマットやAPIエンドポイントの定義に関する部分で、プレースホルダーと引数名の整合性を確認するレビュープロセスを強化します。
- **静的解析ツールの活用**: Pythonの静的解析ツール（例: Pylint, Flake8）をCI/CDパイプラインに組み込み、このようなキーワード引数の不一致や潜在的な `KeyError` を早期に検出できるように検討します。
- **テストカバレッジの維持**: 今回の修正でテストコード自体の変更は不要でしたが、主要なAPI呼び出しやデータ処理ロジックに対して、引き続き詳細な単体テストを維持し、エッジケースやエラーハンドリングもカバーするようにします。

### 確認手順
1.  修正後のコードをデプロイ。
2.  CI/CDパイプラインを再実行し、`test` ジョブが正常に完了することを確認。
3.  アプリケーションを手動で起動し、地域選択から天気予報の詳細画面へ遷移し、天気予報が正常に表示されることを確認。