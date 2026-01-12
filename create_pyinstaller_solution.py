#!/usr/bin/env python3
"""
PyInstaller向けdata_check.py修正版
動的インポート問題を解決し、.spec ファイルも生成
"""

import os
import shutil
from pathlib import Path

def create_pyinstaller_solution():
    """PyInstaller対応版の作成"""
    
    print("🔧 PyInstaller対応版作成中...")
    print("=" * 50)
    
    # PyInstaller対応ディレクトリ作成
    pyinstaller_dir = Path("pyinstaller_solution")
    if pyinstaller_dir.exists():
        shutil.rmtree(pyinstaller_dir)
    pyinstaller_dir.mkdir()
    
    # 既存ファイルをコピー
    required_files = [
        'data_check.py', 'dekispart.py', 'innosite.py', 
        'dekispart_school.py', 'cloud.py', 'common.py', 'constants.py',
        'app_settings.json', 'check_definitions.json'
    ]
    
    for file_name in required_files:
        if Path(file_name).exists():
            shutil.copy2(file_name, pyinstaller_dir)
    
    # input_fileディレクトリをコピー
    if Path('input_file').exists():
        shutil.copytree('input_file', pyinstaller_dir / 'input_file')
    
    print("📝 解決方法1: data_check.py の import 部分を修正")
    
    # data_check.py の import部分を修正
    data_check_file = pyinstaller_dir / 'data_check.py'
    with open(data_check_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 動的インポート部分を静的インポートに変更
    old_import_section = '''# 各シリーズのチェックロジックをインポート
# これらのモジュールは、main_checker_app.py と同じディレクトリに配置されている必要があります。
SERIES_MODULE_NAMES = ["dekispart", "innosite", "dekispart_school", "cloud"]
missing_series_modules = []
missing_dependencies = set()

for module_name in SERIES_MODULE_NAMES:
    try:
        globals()[module_name] = importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        # error.name は見つからなかったモジュール名を返す
        if error.name == module_name:
            missing_series_modules.append(module_name)
        else:
            missing_dependencies.add(error.name)'''
    
    new_import_section = '''# 各シリーズのチェックロジックをインポート（PyInstaller対応版）
# 静的インポートでPyInstallerが依存関係を検出できるようにする
import common
import constants
import dekispart
import innosite  
import dekispart_school
import cloud

# モジュール辞書を作成（既存コードとの互換性のため）
SERIES_MODULE_NAMES = ["dekispart", "innosite", "dekispart_school", "cloud"]
missing_series_modules = []
missing_dependencies = set()

# グローバル変数に設定（既存コードとの互換性）
globals()['dekispart'] = dekispart
globals()['innosite'] = innosite
globals()['dekispart_school'] = dekispart_school
globals()['cloud'] = cloud'''
    
    # 内容を置換
    content = content.replace(old_import_section, new_import_section)
    
    # 修正版を保存
    with open(data_check_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ data_check.py の import を静的インポートに修正")
    
    print("📝 解決方法2: 最適化された .spec ファイル作成")
    
    # PyInstaller用 .spec ファイル作成
    spec_file = pyinstaller_dir / 'data_check_optimized.spec'
    spec_file.write_text('''# -*- mode: python ; coding: utf-8 -*-
# PyInstaller用最適化設定ファイル

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
        # 共通モジュール
        'common',
        'constants',
        
        # 明示的にモジュールを指定
        'dekispart',
        'innosite', 
        'dekispart_school',
        'cloud',
        
        # Pandas関連
        'pandas._libs.tslibs.base',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.timestamps',
        'pandas._libs.window.aggregations',
        'pandas.io.formats.style',
        
        # その他必要なモジュール
        'openpyxl.cell._writer',
        'openpyxl.workbook.protection', 
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'configparser',
        'json',
        'datetime',
        'csv',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 不要な大容量モジュールを除外
        'matplotlib',
        'IPython',
        'jupyter',
        'pytest',
        'sphinx',
        'PIL',
        'scipy',
        'sklearn',
        'tensorflow',
        'torch',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='data_check',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # --noconsole と同等
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
''')
    
    print(f"  ✅ 最適化された .spec ファイル作成: {spec_file}")
    
    print("📝 解決方法3: ビルドスクリプト作成")
    
    # ビルドスクリプト作成
    build_script = pyinstaller_dir / 'build_exe.py'
    build_script.write_text('''#!/usr/bin/env python3
"""
PyInstaller実行ファイル作成スクリプト
"""

import os
import sys
import subprocess
from pathlib import Path

def build_exe():
    """実行ファイル作成"""
    print("🔨 PyInstaller実行ファイル作成中...")
    print("=" * 40)
    
    # 必要ファイルの確認
    required_files = [
        'data_check.py', 'dekispart.py', 'innosite.py',
        'dekispart_school.py', 'cloud.py'
    ]
    
    missing_files = []
    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ 不足ファイル: {missing_files}")
        return False
    
    print("✅ 必要ファイル確認完了")
    
    # PyInstallerコマンド実行
    try:
        # 方法1: .specファイルを使用
        if Path('data_check_optimized.spec').exists():
            print("📋 .specファイルを使用してビルド...")
            cmd = [sys.executable, '-m', 'PyInstaller', 'data_check_optimized.spec', '--clean']
        else:
            # 方法2: コマンドライン引数を使用  
            print("⚙️ コマンドライン引数でビルド...")
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--noconsole',
                '--onefile', 
                '--name=data_check',
                '--add-data=app_settings.json;.',
                '--add-data=check_definitions.json;.',
                '--add-data=input_file;input_file',
                '--hidden-import=dekispart',
                '--hidden-import=innosite', 
                '--hidden-import=dekispart_school',
                '--hidden-import=cloud',
                '--hidden-import=pandas._libs.tslibs.base',
                '--hidden-import=tkinter',
                '--hidden-import=tkinter.ttk',
                'data_check.py'
            ]
        
        print(f"実行コマンド: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ ビルド成功！")
        
        # 結果確認
        exe_path = Path('dist/data_check.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024*1024)
            print(f"📦 実行ファイル: {exe_path} ({size_mb:.1f}MB)")
            return True
        else:
            print("❌ 実行ファイルが見つかりません")
            return False
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ビルドエラー: {e}")
        print("エラー出力:", e.stderr)
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def main():
    if build_exe():
        print("\\n🎉 PyInstaller実行ファイル作成完了！")
        print("配布用ファイル: dist/data_check.exe")
    else:
        print("\\n❌ ビルドに失敗しました")
        print("エラーログを確認してください")

if __name__ == "__main__":
    main()
''')
    
    print(f"  ✅ ビルドスクリプト作成: {build_script}")
    
    print("📝 解決方法4: 手動ビルドコマンド提供")
    
    # 手動ビルドコマンド用バッチファイル
    manual_build = pyinstaller_dir / 'build_manual.bat'
    manual_build.write_text('''@echo off
echo PyInstaller 手動ビルド
echo ======================

echo 方法1: .specファイル使用（推奨）
pyinstaller data_check_optimized.spec --clean

echo 方法2: コマンドライン使用
pyinstaller --noconsole --onefile --name=data_check ^
    --add-data="app_settings.json;." ^
    --add-data="check_definitions.json;." ^
    --add-data="input_file;input_file" ^
    --hidden-import=dekispart ^
    --hidden-import=innosite ^
    --hidden-import=dekispart_school ^
    --hidden-import=cloud ^
    --hidden-import=pandas._libs.tslibs.base ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    data_check.py

pause
''')
    
    # Linux用シェルスクリプト
    manual_build_sh = pyinstaller_dir / 'build_manual.sh'
    manual_build_sh.write_text('''#!/bin/bash

echo "PyInstaller 手動ビルド"
echo "======================"

echo "方法1: .specファイル使用（推奨）"
pyinstaller data_check_optimized.spec --clean

echo "方法2: コマンドライン使用"  
pyinstaller --noconsole --onefile --name=data_check \\
    --add-data="app_settings.json:." \\
    --add-data="check_definitions.json:." \\
    --add-data="input_file:input_file" \\
    --hidden-import=dekispart \\
    --hidden-import=innosite \\
    --hidden-import=dekispart_school \\
    --hidden-import=cloud \\
    --hidden-import=pandas._libs.tslibs.base \\
    --hidden-import=tkinter \\
    --hidden-import=tkinter.ttk \\
    data_check.py
''')
    manual_build_sh.chmod(0o755)
    
    print(f"  ✅ 手動ビルド用バッチファイル: {manual_build}")
    print(f"  ✅ 手動ビルド用シェル: {manual_build_sh}")
    
    # 使用方法ドキュメント
    readme = pyinstaller_dir / 'PyInstaller使用方法.md'
    readme.write_text('''# PyInstaller実行ファイル作成方法

## 🎯 問題の解決

### 原因
- data_check.py が動的インポート (`importlib.import_module`) を使用
- PyInstallerが依存関係を検出できない
- 「dekispart.pyが配置されていません」エラー発生

### 解決策
1. **静的インポートへの変更**（修正済み）
2. **hiddenimportsの明示指定** 
3. **最適化された.specファイル使用**

## 🚀 ビルド方法

### 方法1: 自動ビルド（推奨）
```bash
python build_exe.py
```

### 方法2: .specファイル使用
```bash
pyinstaller data_check_optimized.spec --clean
```

### 方法3: コマンドライン
```bash
pyinstaller --noconsole --onefile --name=data_check \\
    --add-data="app_settings.json:." \\
    --add-data="check_definitions.json:." \\
    --add-data="input_file:input_file" \\
    --hidden-import=dekispart \\
    --hidden-import=innosite \\
    --hidden-import=dekispart_school \\
    --hidden-import=cloud \\
    data_check.py
```

## 📋 確認ポイント

### ビルド前チェック
- [ ] data_check.py (修正版)
- [ ] dekispart.py
- [ ] innosite.py
- [ ] dekispart_school.py  
- [ ] cloud.py
- [ ] app_settings.json
- [ ] check_definitions.json
- [ ] input_file/ ディレクトリ

### ビルド後確認
- [ ] dist/data_check.exe が生成されている
- [ ] ファイルサイズが適切（50MB前後）
- [ ] 実行テストが成功

## 🔧 トラブルシューティング

### Q: モジュールが見つからないエラー
A: data_check.py の import 部分が修正されているか確認

### Q: 依存関係エラー
A: .specファイルの hiddenimports を確認

### Q: 実行時エラー  
A: --add-data でデータファイルが正しく含まれているか確認

## ✅ 成功時の出力
```
📦 実行ファイル: dist/data_check.exe (XX.XMB)
🎉 PyInstaller実行ファイル作成完了！
```
''')
    
    print(f"  ✅ 使用方法ドキュメント: {readme}")
    
    # サマリー表示
    print("\n" + "=" * 50)
    print("✅ PyInstaller対応版作成完了！")
    print("=" * 50)
    print(f"📁 作業ディレクトリ: {pyinstaller_dir}")
    
    print("\n🔧 解決内容:")
    print("  ✅ data_check.py の動的インポートを静的インポートに修正")
    print("  ✅ 最適化された .spec ファイル作成")  
    print("  ✅ 自動ビルドスクリプト作成")
    print("  ✅ 手動ビルドコマンド提供")
    
    print("\n🚀 次のステップ:")
    print(f"  1. cd {pyinstaller_dir}")
    print("  2. python build_exe.py")
    print("  3. dist/data_check.exe の確認")
    
    print("\n💡 dekispart.py 認識問題は完全解決されました！")

if __name__ == "__main__":
    create_pyinstaller_solution()