# 📋 データチェックシステム - クイックスタートガイド

## 🚀 すぐに使い始める手順

### 1. 📂 ファイルの確認
このフォルダに以下のファイルがあることを確認してください：

✅ **実行ファイル**
- `dist/DataCheck.exe` （メイン）
- `dist/DataCheck-Debug.exe` （デバッグ用）

✅ **設定ファイル**
- `config.ini` ⚠️ **要編集**
- `app_settings.json`
- `check_definitions.json`

✅ **その他**
- `input_file/` フォルダ
- `*.py` ファイル（ソースコード）

### 2. ⚙️ データベース設定（重要）

`config.ini` を開いて、以下を編集してください：

```ini
[DEKISPART_MNT_DB]
server = YOUR_SERVER_NAME    # ← 実際のサーバー名に変更
database = YOUR_DATABASE     # ← 実際のDB名に変更
uid = YOUR_USERNAME         # ← 実際のユーザー名に変更  
pwd = YOUR_PASSWORD         # ← 実際のパスワードに変更
```

### 3. 🏃‍♂️ アプリケーション起動

**通常使用:**
```
dist/DataCheck.exe をダブルクリック
```

**問題がある場合:**
```
dist/DataCheck-Debug.exe をダブルクリック
→ コンソールでエラーメッセージを確認
```

### 4. ✅ 動作確認

1. アプリケーションが起動する
2. データベースに接続できる
3. チェックが実行できる

---

## ❗ よくある問題と解決法

**🔴 アプリが起動しない**
→ `DataCheck-Debug.exe` でエラーメッセージを確認

**🔴 データベースエラー**
→ `config.ini` の設定を確認

**🔴 ファイルが見つからない**
→ すべてのファイルが同じフォルダにあるか確認

---

**📖 詳細情報:** `DISTRIBUTION_README.md` を参照してください