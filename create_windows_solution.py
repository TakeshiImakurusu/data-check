#!/usr/bin/env python3
"""
Windows .exe ファイル作成のための実用的ソリューション
ユーザーが実行できるWindows用実行ファイルを作成する方法
"""

import os
import shutil
from pathlib import Path

def create_windows_solution():
    """Windows .exe作成の実用的ソリューション"""
    
    print("🖥️ Windows用.exeファイル作成 - 実用的ソリューション")
    print("=" * 60)
    
    # Windows対応ディレクトリ作成
    windows_dir = Path("windows_exe_solution")
    if windows_dir.exists():
        shutil.rmtree(windows_dir)
    windows_dir.mkdir()
    
    print("🎯 ユーザーの要件:")
    print("  ✅ Windows環境で実行可能")
    print("  ✅ .exeファイル形式")
    print("  ✅ ダブルクリックで起動")
    print("  ✅ インストール不要")
    
    # 解決方法を作成
    
    # === 解決方法1: GitHub Actions自動ビルド（推奨）===
    print("\n🏆 解決方法1: GitHub Actions自動ビルド（推奨）")
    
    github_workflow = windows_dir / ".github_workflows_build-windows.yml"
    github_workflow.parent.mkdir(exist_ok=True)
    
    workflow_content = '''name: Build Windows EXE

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  workflow_dispatch:  # 手動実行可能

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
        pip install pyinstaller
        pip install pandas openpyxl pyodbc pymysql configparser
    
    - name: Create PyInstaller spec
      run: |
        echo "Creating optimized spec file..."
        python -c """
import sys
spec_content = '''# -*- mode: python ; coding: utf-8 -*-
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
        'dekispart',
        'innosite', 
        'dekispart_school',
        'cloud',
        'pandas._libs.tslibs.base',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.timestamps',
        'openpyxl.cell._writer',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'configparser',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DataCheck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    icon=None,
)'''

with open('data_check_windows.spec', 'w', encoding='utf-8') as f:
    f.write(spec_content)
        """
    
    - name: Modify data_check.py for static imports
      run: |
        python -c "
# data_check.pyを静的インポート版に変更
import re

with open('data_check.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 動的インポート部分を静的インポートに置換
old_pattern = r'SERIES_MODULE_NAMES = \\[.*?\\].*?for module_name in SERIES_MODULE_NAMES:.*?except ModuleNotFoundError as error:.*?else:'
new_code = '''# PyInstaller対応: 静的インポート
import dekispart
import innosite
import dekispart_school
import cloud

# 既存コードとの互換性のため
SERIES_MODULE_NAMES = ['dekispart', 'innosite', 'dekispart_school', 'cloud']
missing_series_modules = []
missing_dependencies = set()

globals()['dekispart'] = dekispart
globals()['innosite'] = innosite  
globals()['dekispart_school'] = dekispart_school
globals()['cloud'] = cloud'''

content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)

with open('data_check.py', 'w', encoding='utf-8') as f:
    f.write(content)
        "
    
    - name: Build Windows EXE
      run: |
        pyinstaller data_check_windows.spec --clean --noconfirm
    
    - name: Verify EXE creation
      run: |
        if (Test-Path "dist\\DataCheck.exe") {
          Write-Host "✅ DataCheck.exe created successfully"
          $size = (Get-Item "dist\\DataCheck.exe").Length / 1MB
          Write-Host "📦 File size: $($size.ToString('F1')) MB"
        } else {
          Write-Host "❌ DataCheck.exe not found"
          exit 1
        }
    
    - name: Upload Windows EXE
      uses: actions/upload-artifact@v4
      with:
        name: DataCheck-Windows-EXE
        path: dist/DataCheck.exe
        retention-days: 30
    
    - name: Create Release (on tag)
      if: startsWith(github.ref, 'refs/tags/')
      uses: softprops/action-gh-release@v1
      with:
        files: dist/DataCheck.exe
        name: DataCheck ${{ github.ref_name }}
        draft: false
        prerelease: false
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
'''
    
    github_workflow.write_text(workflow_content, encoding='utf-8')
    
    print(f"  ✅ GitHub Actions設定作成: {github_workflow}")
    print("  🔧 設定方法:")
    print("    1. .github/workflows/ フォルダを作成")
    print("    2. build-windows.yml として保存")
    print("    3. GitHubにプッシュ")
    print("    4. Actions タブで自動ビルド実行")
    print("    5. Artifacts から DataCheck.exe ダウンロード")
    
    # === 解決方法2: Windows環境手順書 ===
    print("\n🖥️ 解決方法2: Windows環境での手動ビルド")
    
    windows_manual = windows_dir / "Windows環境ビルド手順.md"
    windows_manual.write_text('''# Windows環境での.exeファイル作成手順

## 🎯 目標
- データチェックシステムのWindows用.exeファイル作成
- ユーザーがダブルクリックで実行可能

## 🔧 事前準備

### Step 1: Windows環境の準備
- Windows 10/11 PC または 仮想マシン
- インターネット接続

### Step 2: Python インストール
1. https://python.org にアクセス
2. Python 3.9以降をダウンロード
3. インストール時に "Add Python to PATH" をチェック
4. コマンドプロンプトで確認: `python --version`

### Step 3: PyInstaller インストール
```cmd
pip install pyinstaller
pip install pandas openpyxl pyodbc pymysql configparser
```

## 📦 ビルド手順

### Step 1: プロジェクトファイルをWindows環境に転送
以下のファイルを同じフォルダに配置:
```
data_check.py (静的インポート版)
dekispart.py
innosite.py
dekispart_school.py
cloud.py
app_settings.json
check_definitions.json
input_file/ (フォルダ)
data_check_windows.spec
```

### Step 2: data_check.py の修正
動的インポート部分を以下に置換:
```python
# PyInstaller対応: 静的インポート
import dekispart
import innosite
import dekispart_school
import cloud

# 既存コードとの互換性のため
SERIES_MODULE_NAMES = ['dekispart', 'innosite', 'dekispart_school', 'cloud']
missing_series_modules = []
missing_dependencies = set()

globals()['dekispart'] = dekispart
globals()['innosite'] = innosite  
globals()['dekispart_school'] = dekispart_school
globals()['cloud'] = cloud
```

### Step 3: .specファイル作成
`data_check_windows.spec` として保存:
```python
# -*- mode: python ; coding: utf-8 -*-
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
        'pandas._libs.tslibs.base', 'tkinter', 'tkinter.ttk',
        'tkinter.messagebox', 'tkinter.filedialog', 'configparser',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'IPython'],
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
    console=False,  # GUI application
    disable_windowed_traceback=False,
)
```

### Step 4: ビルド実行
```cmd
pyinstaller data_check_windows.spec --clean --noconfirm
```

### Step 5: 結果確認
```cmd
dir dist
# DataCheck.exe が生成されていることを確認
```

## ✅ 成功時の出力
- `dist/DataCheck.exe` (約50MB)
- Windows用実行ファイル
- ダブルクリックで起動可能

## 🎯 配布方法
1. `DataCheck.exe` をユーザーに配布
2. ユーザーはダブルクリックで実行
3. インストール不要
''', encoding='utf-8')
    
    print(f"  ✅ Windows手動ビルド手順: {windows_manual}")
    
    # === 解決方法3: VMware/VirtualBox案内 ===
    print("\n💻 解決方法3: 仮想マシン使用")
    
    vm_guide = windows_dir / "仮想マシン使用方法.md"
    vm_guide.write_text('''# 仮想マシンでWindows .exe作成

## 🎯 概要
Linux環境でWindows仮想マシンを使用して.exeファイルを作成

## 🔧 仮想マシンソフトウェア

### 無料オプション
1. **VirtualBox** (推奨)
2. **VMware Workstation Player** (個人利用無料)

### 商用オプション  
1. **VMware Workstation Pro**
2. **Parallels Desktop** (Mac)

## 📋 セットアップ手順

### Step 1: VirtualBox + Windows 10 セットアップ
1. VirtualBox をダウンロード・インストール
2. Windows 10 ISO をダウンロード
3. 新しい仮想マシン作成:
   - メモリ: 4GB以上
   - ストレージ: 50GB以上
4. Windows 10 をインストール

### Step 2: Python 環境構築
1. Windows仮想マシン内でPython 3.9インストール
2. PyInstaller等の依存関係インストール
3. プロジェクトファイル転送

### Step 3: .exe ビルド実行
前述のWindows環境手順に従ってビルド

## ⏱️ 所要時間
- 初回セットアップ: 2-3時間
- 2回目以降のビルド: 10-15分

## 💡 メリット・デメリット
**メリット:**
- 確実にWindows .exe を作成可能
- 一度セットアップすれば継続利用可能

**デメリット:**
- 初回セットアップが複雑
- システムリソースを消費
''', encoding='utf-8')
    
    print(f"  ✅ 仮想マシン使用ガイド: {vm_guide}")
    
    # === immediate解決策 ===
    print("\n⚡ immediate解決策（最も実用的）")
    
    immediate_solution = windows_dir / "immediate_solution.md"
    immediate_solution.write_text('''# immediate解決策: Windows .exe ファイル取得

## 🚀 最速解決方法

### オプション1: 開発環境でのビルド依頼
もし開発チームにWindows環境がある場合:
1. pyinstaller_solution フォルダを共有
2. Windows環境で `python build_exe_fixed.py` 実行
3. 生成された .exe ファイルを受け取り

### オプション2: クラウドビルドサービス
1. **GitHub Codespaces** (Windows環境)
2. **GitLab CI/CD** (Windows runner)
3. **Azure DevOps** (Windows agent)

### オプション3: 一時的Windows環境
1. **AWS EC2** Windows インスタンス (時間課金)
2. **Azure Virtual Machine** Windows
3. **Google Cloud** Windows VM

## 🎯 immediate配布戦略

### 現在すぐに配布可能
前回作成した `config_fixed_distribution` を使用:
- Windows/Linux 両対応
- Python環境があれば動作
- 3MB軽量パッケージ
- ユーザーフレンドリーな起動方式

### 配布メッセージ例
```
件名: データチェックシステム配布（Windows対応版）

現在、Windows用.exeファイルを準備中です。
その間、以下の暫定版をご利用ください。

【暫定版の特徴】
✅ Windows/Linux完全対応
✅ 軽量（3MB）
✅ 自動セットアップ機能
✅ ダブルクリック起動

【使用方法】
1. 添付ファイルを展開
2. start.py をダブルクリック
3. 自動で環境構築・起動

.exeファイル版は準備でき次第お送りします。
```

## ⏰ タイムライン
- immediate: クロスプラットフォーム版配布
- 1-2日後: GitHub Actionsセットアップで.exe自動生成
- 継続: 自動化されたWindows .exeファイル提供
''', encoding='utf-8')
    
    print(f"  ✅ immediate解決策: {immediate_solution}")
    
    # サマリー表示
    print("\n" + "=" * 60)
    print("✅ Windows .exe ファイル作成ソリューション完成！")
    print("=" * 60)
    print(f"📁 ソリューションディレクトリ: {windows_dir}")
    
    print("\n🎯 推奨実行順序:")
    print("  1. ⚡ immediate: クロスプラットフォーム版を配布")
    print("  2. 🤖 短期: GitHub Actionsセットアップ")
    print("  3. 🖥️ 中期: Windows環境での手動ビルド")
    print("  4. 💻 長期: 仮想マシン環境構築")
    
    print("\n🏆 最も現実的なアプローチ:")
    print("  📦 今すぐ: config_fixed_distribution を配布")
    print("  🤖 1-2日: GitHub Actions で .exe 自動生成")
    print("  🎉 結果: Windows ユーザーが確実に実行可能")
    
    return windows_dir

def create_github_setup_script():
    """GitHub Actionsセットアップスクリプト"""
    
    script_content = '''#!/bin/bash
# GitHub Actions for Windows EXE - Setup Script

echo "🚀 GitHub Actions Windows .exe ビルド設定"
echo "========================================"

# .github/workflows ディレクトリ作成
mkdir -p .github/workflows

# workflow ファイルをコピー
cp windows_exe_solution/.github_workflows_build-windows.yml .github/workflows/build-windows.yml

# data_check.py を静的インポート版に修正
python3 -c """
import re

with open('data_check.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 動的インポート部分を検索・置換
if 'importlib.import_module' in content:
    print('🔧 data_check.py を静的インポート版に修正中...')
    
    # 置換パターン
    old_pattern = r'for module_name in SERIES_MODULE_NAMES:.*?except.*?error.*?else:'
    new_code = '''# PyInstaller対応: 静的インポート
import dekispart
import innosite
import dekispart_school
import cloud

# 既存コードとの互換性のため
globals()['dekispart'] = dekispart
globals()['innosite'] = innosite  
globals()['dekispart_school'] = dekispart_school
globals()['cloud'] = cloud

# エラーハンドリング（既存コードとの互換性）
try:
    pass
except ImportError as error:'''
    
    content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)
    
    with open('data_check.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✅ data_check.py 修正完了')
else:
    print('ℹ️  data_check.py は既に静的インポート版です')
"""

# Git に追加
git add .github/workflows/build-windows.yml
git add data_check.py

echo "✅ GitHub Actions セットアップ完了"
echo ""
echo "📋 次のステップ:"
echo "1. git commit -m 'Add Windows EXE build workflow'"
echo "2. git push origin main"
echo "3. GitHub の Actions タブで自動ビルド確認"
echo "4. Artifacts から DataCheck.exe をダウンロード"
echo ""
echo "🎯 以降は自動でWindows .exeファイルが生成されます！"
'''
    
    with open("setup_github_actions.sh", "w") as f:
        f.write(script_content)
    
    os.chmod("setup_github_actions.sh", 0o755)
    
    print(f"  ✅ GitHub Actions セットアップスクリプト: setup_github_actions.sh")
    
    return script_content

if __name__ == "__main__":
    windows_dir = create_windows_solution()
    print("\n" + "🤖 GitHub Actions自動セットアップ:")
    print("=" * 40)
    create_github_setup_script()
    
    print("\n💡 immediate実行:")
    print("  bash setup_github_actions.sh")
    print("  # → GitHub Actions で Windows .exe 自動生成開始")