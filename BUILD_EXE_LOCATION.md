# 📍 build_exe.py の場所と使用方法

## 🗂️ **ファイルの場所**

**`build_exe.py` は以下にあります：**

```
/home/ta-imakurusu/data-check/pyinstaller_solution/build_exe.py
```

## 🚀 **使用方法**

### **方法1: フルパス指定**
```bash
cd /home/ta-imakurusu/data-check
python pyinstaller_solution/build_exe.py
```

### **方法2: ディレクトリ移動（推奨）**
```bash
cd /home/ta-imakurusu/data-check/pyinstaller_solution
python build_exe.py
```

### **方法3: 絶対パス**
```bash
python /home/ta-imakurusu/data-check/pyinstaller_solution/build_exe.py
```

## 📁 **pyinstaller_solution ディレクトリ構成**

```
pyinstaller_solution/
├── 🔨 build_exe.py                    # ← これです！
├── 📋 data_check_optimized.spec       # PyInstaller設定
├── 🐍 data_check.py                   # 修正版メインファイル
├── 🐍 dekispart.py                    # モジュール1
├── 🐍 innosite.py                     # モジュール2
├── 🐍 dekispart_school.py             # モジュール3
├── 🐍 cloud.py                        # モジュール4
├── 📄 app_settings.json               # 設定ファイル
├── 📄 check_definitions.json          # チェック定義
├── 📁 input_file/                     # サンプルデータ
├── 📋 PyInstaller使用方法.md          # 詳細手順書
└── 📁 dist/                          # ビルド結果（data_check実行ファイル）
```

## ⚡ **クイック実行手順**

```bash
# Step 1: ディレクトリ移動
cd /home/ta-imakurusu/data-check/pyinstaller_solution

# Step 2: 仮想環境有効化
source ../.venv/bin/activate

# Step 3: ビルド実行
python build_exe.py

# Step 4: 結果確認
ls -lh dist/
```

## 🎯 **実行結果の確認**

成功時の出力：
```
🔨 PyInstaller実行ファイル作成中...
✅ 必要ファイル確認完了
📋 .specファイルを使用してビルド...
✅ ビルド成功！
📦 実行ファイル: dist/data_check (45MB)
🎉 PyInstaller実行ファイル作成完了！
```

## 🔧 **代替手段**

`build_exe.py`が見つからない、または動作しない場合：

### **手動ビルド**
```bash
cd /home/ta-imakurusu/data-check/pyinstaller_solution
pyinstaller data_check_optimized.spec --clean
```

### **コマンドライン直接**
```bash
pyinstaller --noconsole --onefile --name=data_check \
    --hidden-import=dekispart \
    --hidden-import=innosite \
    --hidden-import=dekispart_school \
    --hidden-import=cloud \
    data_check.py
```

## 📝 **現在の状況**

✅ `build_exe.py` は `/home/ta-imakurusu/data-check/pyinstaller_solution/` に存在  
✅ 既に1回ビルドが成功し、`dist/data_check` (45MB) が生成済み  
✅ すぐに使用可能な状態

**次のコマンドを実行してください：**
```bash
cd /home/ta-imakurusu/data-check/pyinstaller_solution
python build_exe.py
```