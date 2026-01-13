@echo off
setlocal enabledelayedexpansion

REM ======================================
REM DataCheck ランチャースクリプト
REM ファイルサーバーからローカルにコピーして高速起動
REM ======================================

REM 設定
set "APP_NAME=DataCheck"
set "LOCAL_DIR=%TEMP%\%APP_NAME%"
set "SOURCE_DIR=%~dp0"
set "EXE_NAME=DataCheck.exe"
set "VERSION_FILE=.version"

REM バージョンチェック用のタイムスタンプファイル
set "SOURCE_VERSION=%SOURCE_DIR%%VERSION_FILE%"
set "LOCAL_VERSION=%LOCAL_DIR%\%VERSION_FILE%"

echo ======================================
echo %APP_NAME% を起動しています...
echo ======================================

REM ローカルディレクトリが存在しない場合は作成
if not exist "%LOCAL_DIR%" (
    echo 初回起動: ローカルにコピー中...
    goto :copy_files
)

REM バージョンファイルの比較（更新チェック）
if exist "%SOURCE_VERSION%" (
    if exist "%LOCAL_VERSION%" (
        fc /b "%SOURCE_VERSION%" "%LOCAL_VERSION%" >nul 2>&1
        if errorlevel 1 (
            echo 更新が検出されました。ファイルをコピー中...
            goto :copy_files
        ) else (
            echo キャッシュを使用して起動します...
            goto :run_app
        )
    ) else (
        echo バージョンファイルが見つかりません。コピー中...
        goto :copy_files
    )
) else (
    REM バージョンファイルがない場合は毎回コピー
    echo コピー中...
    goto :copy_files
)

:copy_files
REM 既存のローカルディレクトリを削除
if exist "%LOCAL_DIR%" (
    rmdir /s /q "%LOCAL_DIR%" >nul 2>&1
)

REM ファイルをコピー（robocopyで高速コピー）
echo ファイルをローカルにコピー中...
robocopy "%SOURCE_DIR%" "%LOCAL_DIR%" /E /NFL /NDL /NJH /NJS /NP >nul 2>&1

REM robocopyは成功時も0以外を返すことがあるのでエラーチェックは緩く
if errorlevel 8 (
    echo エラー: ファイルのコピーに失敗しました。
    pause
    exit /b 1
)

echo コピー完了！
goto :run_app

:run_app
REM アプリケーションを実行
echo 起動中...
start "" "%LOCAL_DIR%\%EXE_NAME%"
exit /b 0
