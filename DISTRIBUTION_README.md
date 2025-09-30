# データチェックシステム - Windows配布パッケージ

## 📦 配布パッケージ内容

このパッケージには**完全なセット一式**が含まれています：

```
DataCheck-Windows-Distribution/
├── dist/                      # 実行ファイル
│   ├── DataCheck.exe          # メインアプリ（ノーコンソール版）
│   └── DataCheck-Debug.exe    # デバッグ版（コンソール有り）
├── 
├── 設定ファイル
│   ├── app_settings.json      # アプリケーション設定
│   ├── check_definitions.json # チェック定義設定
│   └── config.ini            # データベース接続設定
├── 
├── ソースコード
│   ├── data_check.py         # メインアプリケーション
│   ├── dekispart.py          # でき太シリーズモジュール
│   ├── innosite.py           # イノサイトシリーズモジュール
│   ├── dekispart_school.py   # でき太スクールモジュール
│   └── cloud.py              # クラウドシリーズモジュール
├── 
├── サンプルデータ
│   └── input_file/           # テスト・サンプル用CSVファイル
│       ├── T_stdData.csv
│       ├── 得意先マスタ.csv
│       ├── 担当者マスタ.csv
│       └── その他のファイル
└── 
└── ドキュメント
    ├── DISTRIBUTION_README.md # このファイル
    └── README.md             # 開発者向け情報
```

## 🚀 使用方法

### 1. 初回セットアップ

1. **全ファイルをそのまま使用**
   - ZIPファイルを解凍したフォルダをそのまま使用
   - すべてのファイルが適切な場所に配置済み

2. **データベース接続設定**
   - `config.ini` ファイルを編集
   - 本番環境のデータベース情報に変更

3. **アプリケーション設定（オプション）**
   - `app_settings.json` でアプリの基本設定を調整
   - `check_definitions.json` でチェック項目をカスタマイズ

### 2. アプリケーションの実行

**🎯 通常使用（推奨）:**
```
dist/DataCheck.exe をダブルクリック
```
- コンソールウィンドウが表示されません
- 通常の業務使用に最適

**🔧 トラブルシューティング時:**
```
dist/DataCheck-Debug.exe をダブルクリック
```
- コンソールウィンドウでエラーメッセージを確認可能
- 問題発生時の原因調査に使用

### 3. ファイルの役割

#### ✅ **実行に必須**
- `dist/DataCheck.exe` - メインアプリケーション
- `app_settings.json` - アプリ設定
- `check_definitions.json` - チェック定義

#### ⚙️ **環境依存（要設定）**
- `config.ini` - データベース接続情報

#### 📂 **オプション**
- `input_file/` - サンプルデータ（参考用）
- `*.py` - ソースコード（開発・カスタマイズ用）

## 🔧 設定ファイルの詳細

### config.ini
```ini
[DEKISPART_MNT_DB]
driver = {ODBC Driver 18 for SQL Server}
server = YOUR_SERVER\INSTANCE
database = YOUR_DATABASE
uid = YOUR_USERNAME
pwd = YOUR_PASSWORD
```

### app_settings.json
アプリケーションの基本設定（ウィンドウサイズ、デフォルトパスなど）

### check_definitions.json
各チェック項目の定義と実行条件

## 🏗️ 開発者向け情報

### ソースコードの構成
- **data_check.py**: メインGUIアプリケーション
- **dekispart.py**: でき太シリーズのデータチェックロジック
- **innosite.py**: イノサイトシリーズのチェックロジック
- **dekispart_school.py**: でき太スクールのチェックロジック
- **cloud.py**: クラウドシリーズのチェックロジック

### カスタマイズ方法
1. Pythonファイルを編集
2. 仮想環境で動作テスト
3. PyInstallerで新しいEXEを生成

```bash
# 開発環境セットアップ
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install pandas openpyxl pyodbc pymysql chardet python-dateutil

# アプリケーション実行
python data_check.py
```

## 🔧 トラブルシューティング

### Q: アプリケーションが起動しない
1. **デバッグ版を使用**: `DataCheck-Debug.exe`
2. **ファイル配置確認**: すべてのファイルが同じフォルダにあるか
3. **セキュリティ設定**: Windowsでブロックされていないか確認

### Q: データベースに接続できない
1. **設定確認**: `config.ini`の接続情報
2. **ネットワーク**: データベースサーバーへの接続
3. **権限確認**: データベースアクセス権限

### Q: CSVファイルが読み込めない
1. **エンコーディング**: UTF-8またはShift-JIS
2. **ファイルパス**: 日本語や特殊文字を避ける
3. **ファイルロック**: 他のアプリで開いていないか確認

## 📋 システム要件

- **OS**: Windows 10/11 (64-bit)
- **メモリ**: 4GB以上推奨
- **ディスク**: 500MB以上の空き容量
- **ネットワーク**: データベースサーバーへの接続

## 📞 サポート

問題が発生した場合は、以下の情報とともにシステム管理者にお問い合わせください：

1. **エラーメッセージ**: デバッグ版で表示される詳細
2. **操作手順**: 問題が発生した具体的な操作
3. **環境情報**: Windows版、データベース種類など

---

**バージョン**: 1.0  
**ビルド日**: 自動生成  
**配布形式**: GitHub Actions自動ビルド  
**問い合わせ**: システム管理者