#!/bin/bash

echo "PyInstaller 手動ビルド"
echo "======================"

echo "方法1: .specファイル使用（推奨）"
pyinstaller data_check_optimized.spec --clean

echo "方法2: コマンドライン使用"  
pyinstaller --noconsole --onefile --name=data_check \
    --add-data="app_settings.json:." \
    --add-data="check_definitions.json:." \
    --add-data="input_file:input_file" \
    --hidden-import=dekispart \
    --hidden-import=innosite \
    --hidden-import=dekispart_school \
    --hidden-import=cloud \
    --hidden-import=pandas._libs.tslibs.base \
    --hidden-import=tkinter \
    --hidden-import=tkinter.ttk \
    data_check.py
