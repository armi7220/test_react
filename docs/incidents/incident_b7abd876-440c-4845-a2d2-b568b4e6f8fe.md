## インシデントレポート: `NameError` による天気予報取得失敗

### 概要
本番環境のCI/CDパイプラインで実行されたテストジョブ `test` において、`TestApiMonitor.test_get_weather_forecast_tokyo` が `AssertionError` で失敗しました。根本原因は、`JmaApiService.get_weather_forecast` メソッド内で未定義の変数 `area_code` を参照しようとしたことによる `NameError` でした。

### 根本原因
`weather-forecast-app/services/jma_api.py` 内の `JmaApiService.get_weather_forecast(code)` メソッドにおいて、APIリクエストURLのフォーマットとログ出力の際に、引数として渡されるべき `code` 変数ではなく、誤って `area_code` という変数を参照していました。この `area_code` はメソッドスコープ内で定義されていなかったため、`NameError` が発生し、結果として `requests.get` が実行されず、`None` が返されていました。

### 影響
- `TestApiMonitor.test_get_weather_forecast_tokyo` テストが失敗。
- アプリケーションが天気予報を取得しようとした際に、同様の `NameError` が発生し、機能不全に陥る可能性。

### 修正内容
1.  **`weather-forecast-app/services/jma_api.py`**: `JmaApiService.get_weather_forecast` メソッド内の `FORECAST_URL.format()` および `print()` 文で、引数 `code` を正しく使用するように修正しました。
    - 変更前: `url = JmaApiService.FORECAST_URL.format(area_code = area_code)`
    - 変更後: `url = JmaApiService.FORECAST_URL.format(area_code = code)`
    - ログ出力も同様に修正。
2.  **`weather-forecast-app/tests/test_api_monitor.py`**: `test_get_weather_forecast_tokyo` テストにおいて、APIレスポンスが期待されるリスト形式であり、かつ `timeSeries` や `areas` といった主要なキーが存在し、それらが空でないことを確認するアサーションを追加し、テストの堅牢性を向上させました。

### 再発防止策
- **コードレビューの強化**: 変数名の不一致やスコープに関する基本的なエラーを見逃さないよう、コードレビュープロセスを強化します。
- **静的解析ツールの導入**: Pythonの静的解析ツール（例: Pylint, Flake8）をCI/CDパイプラインに組み込み、このようなコーディングミスを早期に検出できるようにします。
- **テストカバレッジの向上**: 今回の修正でテストを強化しましたが、主要なAPI呼び出しやデータ処理ロジックに対して、より詳細な単体テストを記述し、エッジケースやエラーハンドリングもカバーするようにします。

### 確認手順
1.  修正後のコードをデプロイ。
2.  CI/CDパイプラインを再実行し、`test` ジョブが正常に完了することを確認。
3.  アプリケーションを手動で起動し、地域選択から天気予報の詳細画面へ遷移し、天気予報が正常に表示されることを確認。