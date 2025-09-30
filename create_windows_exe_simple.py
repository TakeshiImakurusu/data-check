#!/usr/bin/env python3
"""
Windows用.exeファイル作成 - 実用的ソリューション
"""

import os
import shutil
from pathlib import Path

def create_windows_exe_solution():
    """Windows .exe作成の実用的ソリューション"""
    
    print("🖥️ Windows用.exeファイル作成ソリューション")
    print("=" * 50)
    
    # Windows対応ディレクトリ作成
    windows_dir = Path("windows_exe_solution")
    if windows_dir.exists():
        shutil.rmtree(windows_dir)
    windows_dir.mkdir()
    
    # GitHub Actionsワークフロー作成
    workflows_dir = windows_dir / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    
    workflow_file = workflows_dir / "build-windows.yml"
    workflow_content = """name: Build Windows EXE

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build-windows-exe:
    runs-on: windows-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyinstaller pandas openpyxl pyodbc pymysql configparser
    
    - name: Prepare files for PyInstaller
      run: |
        echo "Modifying data_check.py for static imports..."
        python -c "
import re
with open('data_check.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 静的インポート版に変更
static_imports = '''# PyInstaller対応: 静的インポート
import dekispart
import innosite
import dekispart_school
import cloud

SERIES_MODULE_NAMES = ['dekispart', 'innosite', 'dekispart_school', 'cloud']
missing_series_modules = []
missing_dependencies = set()

globals()[\\\"dekispart\\\"] = dekispart
globals()[\\\"innosite\\\"] = innosite  
globals()[\\\"dekispart_school\\\"] = dekispart_school
globals()[\\\"cloud\\\"] = cloud'''

# 動的インポート部分を置換
if 'importlib.import_module' in content:
    # 簡単な置換
    lines = content.split('\\n')
    new_lines = []
    skip_section = False
    
    for line in lines:
        if 'SERIES_MODULE_NAMES = [' in line:
            new_lines.append(static_imports)
            skip_section = True
        elif skip_section and ('missing_dependencies.add' in line or 'messagebox.showerror' in line):
            skip_section = False
            new_lines.append(line)
        elif not skip_section:
            new_lines.append(line)
    
    content = '\\n'.join(new_lines)

with open('data_check.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Static imports applied')
        "
    
    - name: Create PyInstaller spec
      run: |
        echo 'Creating spec file...'
        echo "# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['data_check.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app_settings.json', '.'),
        ('check_definitions.json', '.'),
        ('input_file', 'input_file'),
    ],
    hiddenimports=[
        'dekispart', 'innosite', 'dekispart_school', 'cloud',
        'pandas._libs.tslibs.base', 'pandas._libs.tslibs.timedeltas',
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
        'configparser', 'openpyxl.cell._writer'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'IPython', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='DataCheck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False, upx=True, upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
)" > data_check.spec
    
    - name: Build Windows EXE
      run: |
        pyinstaller data_check.spec --clean --noconfirm
    
    - name: Verify and upload EXE
      run: |
        if (Test-Path "dist\\DataCheck.exe") {
          Write-Host "✅ DataCheck.exe created successfully"
          $size = (Get-Item "dist\\DataCheck.exe").Length / 1MB
          Write-Host "📦 Size: $($size.ToString('F1')) MB"
        } else {
          Write-Host "❌ Build failed"
          exit 1
        }
    
    - name: Upload Windows EXE Artifact
      uses: actions/upload-artifact@v4
      with:
        name: DataCheck-Windows-EXE
        path: dist/DataCheck.exe
        retention-days: 30
"""
    
    workflow_file.write_text(workflow_content, encoding='utf-8')
    
    # セットアップスクリプト作成
    setup_script = windows_dir / "setup_github_actions.sh"
    setup_script.write_text("""#!/bin/bash

echo "🚀 GitHub Actions Windows .exe ビルドセットアップ"
echo "=============================================="

# .github/workflows ディレクトリ作成
mkdir -p .github/workflows

# ワークフローファイルをコピー
cp windows_exe_solution/.github/workflows/build-windows.yml .github/workflows/

echo "✅ GitHub Actions ワークフロー設定完了"
echo ""
echo "📋 次のステップ:"
echo "1. git add .github/workflows/build-windows.yml"
echo "2. git commit -m 'Add Windows EXE build workflow'"
echo "3. git push origin main"
echo "4. GitHub → Actions タブ → 'Build Windows EXE' → Run workflow"
echo "5. 完了後、Artifacts から DataCheck.exe をダウンロード"
echo ""
echo "🎯 これで Windows用 .exe ファイルが自動生成されます！"
""", encoding='utf-8')
    setup_script.chmod(0o755)
    
    # 使用方法ドキュメント作成
    usage_doc = windows_dir / "Windows_EXE_作成方法.md"
    usage_doc.write_text("""# Windows .exe ファイル作成方法

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

""", encoding='utf-8')
    
    print(f"✅ Windows .exe ソリューション作成完了: {windows_dir}")
    print("\n📦 作成されたファイル:")
    print(f"  🤖 GitHub Actions: {workflow_file}")
    print(f"  🔧 セットアップ: {setup_script}")
    print(f"  📖 使用方法: {usage_doc}")
    
    print("\n🚀 immediate実行方法:")
    print("  1. bash windows_exe_solution/setup_github_actions.sh")
    print("  2. git add .github/workflows/build-windows.yml")
    print("  3. git commit -m 'Add Windows EXE build'")
    print("  4. git push origin main")
    print("  5. GitHub Actions で自動ビルド → DataCheck.exe 完成！")
    
    return windows_dir

if __name__ == "__main__":
    create_windows_exe_solution()
    
    print("\n💡 GitHub Actions は無料で使用できます")
    print("🎯 5-10分後にユーザーが実行できる Windows .exe ファイルが完成します！")