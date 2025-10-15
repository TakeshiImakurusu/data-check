# data-check
受注管理部が管理する基幹システムのデータをチェックするツール

## テスト実行手順
以下の手順でユニットテストを実行できます。

1. 仮想環境を作成して有効化します。
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows の場合は .venv\\Scripts\\activate
   ```
2. テストに必要な依存パッケージをインストールします。
   ```bash
   pip install -r requirements-test.txt
   ```
   - オフライン環境や社内プロキシ経由で PyPI へ直接接続できない環境では、事前に `pandas` と `python-dateutil`、`pytest` のホイールを取得してからインストールしてください。
   - 403 Forbidden などのエラーで取得できない場合は、社内のパッケージリポジトリを利用するか、インストーラーを別途持ち込んで `pip install <wheel ファイル>` を実行してください。
3. Pytest を使って対象のテストを実行します。
   ```bash
   python -m pytest tests/test_dekispart.py
   ```

テスト完了後は `deactivate` で仮想環境を終了できます。
