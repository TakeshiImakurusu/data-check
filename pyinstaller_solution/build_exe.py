#!/usr/bin/env python3
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
        print("\n🎉 PyInstaller実行ファイル作成完了！")
        print("配布用ファイル: dist/data_check.exe")
    else:
        print("\n❌ ビルドに失敗しました")
        print("エラーログを確認してください")

if __name__ == "__main__":
    main()
