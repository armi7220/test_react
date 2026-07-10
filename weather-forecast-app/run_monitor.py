import unittest
import sys
import os

# プロジェクトルートにパスを通す
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("監視用テスト（ヘルスチェック・API外形監視）を開始します...")
    print("=" * 60)
    
    # testsディレクトリからテストを自動検出
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests"))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 60)
    if result.wasSuccessful():
        print("✅ 全ての監視用テストが正常に完了しました。システムは健全です。")
        sys.exit(0)
    else:
        print("❌ テストが失敗しました。システムに異常がある可能性があります。")
        sys.exit(1)
