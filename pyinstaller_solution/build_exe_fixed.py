#!/usr/bin/env python3
"""
PyInstaller環境修正版ビルドスクリプト
仮想環境を自動検出・有効化してからビルド実行
"""

import os
import sys
import subprocess
from pathlib import Path

def find_virtual_env():
    """仮想環境を検出"""
    current_dir = Path.cwd()
    
    # 現在のディレクトリから上位ディレクトリを探索
    for parent in [current_dir] + list(current_dir.parents):
        venv_path = parent / '.venv'
        if venv_path.exists():
            return venv_path
    
    return None

def get_venv_python(venv_path):
    """仮想環境のPythonパスを取得"""
    python_path = venv_path / 'bin' / 'python'
    if python_path.exists():
        return str(python_path)
    
    # Windows対応
    python_path = venv_path / 'Scripts' / 'python.exe'
    if python_path.exists():
        return str(python_path)
    
    return None

def check_pyinstaller(python_cmd):
    """PyInstallerがインストールされているかチェック"""
    try:
        result = subprocess.run([python_cmd, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        return 'pyinstaller' in result.stdout.lower()
    except:
        return False

def install_pyinstaller(python_cmd):
    """PyInstallerをインストール"""
    print("📦 PyInstallerをインストール中...")
    try:
        subprocess.run([python_cmd, '-m', 'pip', 'install', 'pyinstaller'], 
                      check=True)
        print("✅ PyInstallerインストール完了")
        return True
    except subprocess.CalledProcessError:
        print("❌ PyInstallerインストール失敗")
        return False

def build_exe():
    """環境修正版実行ファイル作成"""
    print("🔨 PyInstaller実行ファイル作成中...")
    print("=" * 40)
    
    # 仮想環境検出
    venv_path = find_virtual_env()
    if venv_path:
        python_cmd = get_venv_python(venv_path)
        if python_cmd:
            print(f"✅ 仮想環境を検出: {venv_path}")
            print(f"✅ Python: {python_cmd}")
        else:
            print(f"❌ 仮想環境のPythonが見つかりません: {venv_path}")
            python_cmd = sys.executable
    else:
        print("⚠️  仮想環境が見つかりません。システムPythonを使用します。")
        python_cmd = sys.executable
    
    # PyInstallerチェック
    if not check_pyinstaller(python_cmd):
        print("⚠️  PyInstallerがインストールされていません")
        if not install_pyinstaller(python_cmd):
            return False
    else:
        print("✅ PyInstaller: インストール済み")
    
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
            cmd = [python_cmd, '-m', 'PyInstaller', 'data_check_optimized.spec', '--clean']
        else:
            # 方法2: コマンドライン引数を使用  
            print("⚙️ コマンドライン引数でビルド...")
            cmd = [
                python_cmd, '-m', 'PyInstaller',
                '--noconsole',
                '--onefile', 
                '--name=data_check',
                '--add-data=app_settings.json:.',
                '--add-data=check_definitions.json:.',
                '--add-data=input_file:input_file',
                '--hidden-import=dekispart',
                '--hidden-import=innosite', 
                '--hidden-import=dekispart_school',
                '--hidden-import=cloud',
                '--hidden-import=pandas._libs.tslibs.base',
                '--hidden-import=tkinter',
                '--hidden-import=tkinter.ttk',
                'data_check.py'
            ]
        
        print(f"実行コマンド: {' '.join(cmd[:3])} ...")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ ビルド成功！")
        
        # 結果確認
        possible_exe_paths = [
            Path('dist/data_check.exe'),  # Windows
            Path('dist/data_check')       # Linux
        ]
        
        exe_path = None
        for path in possible_exe_paths:
            if path.exists():
                exe_path = path
                break
        
        if exe_path:
            size_mb = exe_path.stat().st_size / (1024*1024)
            print(f"📦 実行ファイル: {exe_path} ({size_mb:.1f}MB)")
            return True
        else:
            print("❌ 実行ファイルが見つかりません")
            print("dist/ディレクトリの内容:")
            dist_path = Path('dist')
            if dist_path.exists():
                for item in dist_path.iterdir():
                    print(f"  - {item}")
            return False
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ビルドエラー: {e}")
        print("エラー出力:", e.stderr[:500] + "..." if len(e.stderr) > 500 else e.stderr)
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def main():
    if build_exe():
        print("\\n🎉 PyInstaller実行ファイル作成完了！")
        print("配布用ファイル: dist/ ディレクトリ内の実行ファイル")
    else:
        print("\\n❌ ビルドに失敗しました")
        print("\\n🔧 解決方法:")
        print("1. 仮想環境を有効化してから実行:")
        print("   source ../.venv/bin/activate")
        print("   python build_exe.py")
        print("\\n2. または手動ビルド:")
        print("   pyinstaller data_check_optimized.spec --clean")

if __name__ == "__main__":
    main()