#!/bin/bash

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
