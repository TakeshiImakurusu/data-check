# PyInstaller実行ファイル作成方法

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
pyinstaller --noconsole --onefile --name=data_check \
    --add-data="app_settings.json:." \
    --add-data="check_definitions.json:." \
    --add-data="input_file:input_file" \
    --hidden-import=dekispart \
    --hidden-import=innosite \
    --hidden-import=dekispart_school \
    --hidden-import=cloud \
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
