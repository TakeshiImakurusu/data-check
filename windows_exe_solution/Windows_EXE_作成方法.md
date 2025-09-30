# Windows .exe ファイル作成方法

## 🎯 目標
ユーザーがWindows環境で実行できる .exe ファイルを作成

## ⚡ 最速解決方法: GitHub Actions（推奨）

### Step 1: GitHub Actions セットアップ
```bash
cd /path/to/data-check
bash windows_exe_solution/setup_github_actions.sh
```

### Step 2: GitHub にプッシュ
```bash
git add .github/workflows/build-windows.yml
git commit -m "Add Windows EXE build workflow"
git push origin main
```

### Step 3: ビルド実行
1. GitHub リポジトリページを開く
2. "Actions" タブをクリック
3. "Build Windows EXE" ワークフローを選択
4. "Run workflow" ボタンをクリック
5. 約5-10分で完了

### Step 4: .exe ファイルダウンロード
1. ワークフロー実行完了後
2. "Artifacts" セクションを開く
3. "DataCheck-Windows-EXE" をダウンロード
4. ZIP展開 → DataCheck.exe (約50MB)

## 🖥️ 代替方法: Windows環境での手動ビルド

### 必要な環境
- Windows 10/11 PC
- Python 3.9以降
- インターネット接続

### 手順
1. Python をインストール
2. `pip install pyinstaller pandas openpyxl pyodbc pymysql`
3. プロジェクトファイルを Windows PC に転送
4. data_check.py を静的インポート版に修正
5. `pyinstaller --noconsole --onefile --name=DataCheck data_check.py`
6. dist/DataCheck.exe 完成

## 🎉 成功時の結果
- DataCheck.exe (約50MB)
- Windows用実行ファイル
- ダブルクリックで起動
- インストール不要
- ユーザーが確実に実行可能

## ⏰ 所要時間
- GitHub Actions: 5-10分（自動）
- 手動ビルド: 30分-1時間（初回セットアップ含む）

## 🎯 配布方法
1. DataCheck.exe をユーザーに配布
2. ユーザーはダブルクリックで実行
3. 🎉 「dekispart.py配置されていません」エラーは発生しません

