import pymysql
import pandas as pd
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox
import re
import os
import traceback
from typing import Callable
import configparser

# --- 設定値 ---
class Config:
    # データベース接続設定はconfig.iniに移行しました

    # ファイルパス (デフォルト値。GUIで選択される場合は上書きされる)
    TOTALNET_LIST_DEFAULT_PATH = "totalnet_list.csv" # 仮のパス
    # UNNECESSARY_DEALER_LIST_DEFAULT_PATH は削除されました（要望#005対応）

    # 出力ファイル名
    OUTPUT_EXCEL_FILENAME = "dekispart_school_validation_results.xlsx"

    # チェックID定数
    CHK_ID_PREFIX = "DEKISPART_SCHOOL_CHK_"
    CHK_ID_0002 = CHK_ID_PREFIX + "0002" # IDの桁数が8桁
    CHK_ID_0003 = CHK_ID_PREFIX + "0003" # IDの重複
    CHK_ID_0004 = CHK_ID_PREFIX + "0004" # stdDIDとstdDsupIDの最初の8桁が一致しない
    CHK_ID_0007 = CHK_ID_PREFIX + "0007" # 販店1マスタのコード形式不正
    CHK_ID_0008 = CHK_ID_PREFIX + "0008" # stdDsale1に"ksALL"が含まれる
    CHK_ID_0009 = CHK_ID_PREFIX + "0009" # stdDsale1が004359(リコー)の場合、stdDsale2が空白
    CHK_ID_0010 = CHK_ID_PREFIX + "0010" # stdDsale1が000286(建築資料)の場合、stdDsale2が空白
    CHK_ID_0011 = CHK_ID_PREFIX + "0011" # stdSale1が001275(キヤノン(新潟のみ）)の場合、stdSale2が空白
    CHK_ID_0012 = CHK_ID_PREFIX + "0012" # 登録販売店が倒産指定されている
    CHK_ID_0013 = CHK_ID_PREFIX + "0013" # stdisale1が000332(ITS三島)の場合、stdiNsyuが211でない
    CHK_ID_0014 = CHK_ID_PREFIX + "0014" # stdSale1がA30777(ITS札幌)の場合、stdDNsyuが211でない
    CHK_ID_0015 = CHK_ID_PREFIX + "0015" # stdDsale1が000583(富士)の場合、stdDNsyuが211でない
    CHK_ID_0016 = CHK_ID_PREFIX + "0016" # stdDsale1が000659(富士FBI秋田)の場合、stdDNsyuが211でない
    CHK_ID_0017 = CHK_ID_PREFIX + "0017" # stdSale1が000759(精密舎)の場合、stdNsyuが211でない
    CHK_ID_0018 = CHK_ID_PREFIX + "0018" # 退会(stdDKaiyaku)がTrueで処理中（stdDFlg1）がtrue
    CHK_ID_0019 = CHK_ID_PREFIX + "0019" # stdDNsyu(入金経路)が121でトータルネットに未登録
    CHK_ID_0020 = CHK_ID_PREFIX + "0020" # 更新案内不要(112)以外でstdDsale1が更新案内不要リストに存在
    CHK_ID_0021 = CHK_ID_PREFIX + "0021" # 更新案内不要(112)以外でstdDsale1が旭測器(B88299)
    CHK_ID_0022 = CHK_ID_PREFIX + "0022" # stdDKaiyakuがfalseでstdDtselnoが対象外営業リストに含まれる
    CHK_ID_0023 = CHK_ID_PREFIX + "0023" # stdDKaiyakuがfalseでstdDtselnoが空白
    CHK_ID_0024 = CHK_ID_PREFIX + "0024" # stdDKaiyakuがfalseでstdDReyear1が過去の日付
    CHK_ID_0025 = CHK_ID_PREFIX + "0025" # stdDKaiyakuがtrueでstdDReyear1が未来の日付
    CHK_ID_0026 = CHK_ID_PREFIX + "0026" # stdDKaiyakuがfalseでstdDAcdayが1年2か月以上前
    CHK_ID_0027 = CHK_ID_PREFIX + "0027" # stdDKaiyakuがtrueでstdDAcdayが未来の日付
    CHK_ID_0028 = CHK_ID_PREFIX + "0028" # stdDKaiyakuがfalseでstdDRemonが空白
    CHK_ID_0029 = CHK_ID_PREFIX + "0029" # stdDKaiyakuがfalseでstdDReyear1が空白
    CHK_ID_0030 = CHK_ID_PREFIX + "0030" # stdDKaiyakuがfalseでstdDReyear1が1年3か月以上先
    CHK_ID_0031 = CHK_ID_PREFIX + "0031" # stdDKaiyakuがfalseでstdDReyear2が空白
    CHK_ID_0032 = CHK_ID_PREFIX + "0032" # stdDKaiyakuがtrueでstdDKaiyakuOPがfalse
    
    # データ取得エラー時のチェックID
    DATA_FETCH_ERROR_ID = CHK_ID_PREFIX + "DATA_FETCH_ERROR"
    AUX_FILE_TOTALNET_MISSING_ID = CHK_ID_PREFIX + "AUX_FILE_TOTALNET_MISSING"
    AUX_FILE_UNNECESSARY_DEALER_MISSING_ID = CHK_ID_PREFIX + "AUX_FILE_UNNECESSARY_DEALER_MISSING"


# --- 汎用関数 ---
def create_error_entry(user_id: str, check_id: str, maintenance_id: str = None) -> dict:
    """エラーエントリを作成するヘルパー関数。保守整理番号を含む。"""
    # 保守整理番号はstdID_Dフィールドから取得（要望に基づく）
    return {
        "シリーズ": "DEKISPART_SCHOOL",
        "ユーザID": user_id,
        "保守整理番号": maintenance_id if maintenance_id else "",  # 保守整理番号を追加
        "チェックID": check_id,
    }

def fetch_data_from_db(config_section: str, query: str) -> pd.DataFrame:
    """
    指定されたDB設定とクエリを使用してデータを取得し、DataFrameとして返す。
    """
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
        db_config = config[config_section]

        with pymysql.connect(
            host=db_config['host'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            charset=db_config['charset']
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
        return pd.DataFrame(data, columns=columns)
    except pymysql.Error as e:
        messagebox.showerror("データベースエラー", f"データベースからのデータ取得中にエラーが発生しました: {e}")
        print(f"Database error details: {traceback.format_exc()}")
        return pd.DataFrame() # 空のDataFrameを返す

def select_file_with_gui(title: str, filetypes: list) -> str:
    """GUIを使ってファイル選択ダイアログを表示し、選択されたファイルのパスを返す。"""
    root = tk.Tk()
    root.withdraw()  # ウィンドウを非表示にする
    file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy() # ウィンドウを破棄
    return file_path

def load_csv_to_dataframe(file_path: str, required_column: str) -> pd.DataFrame:
    """CSVファイルを読み込み、指定された必須カラムを含むDataFrameを返す。"""
    if not file_path or not os.path.exists(file_path):
        messagebox.showerror("ファイル読み込みエラー", f"ファイルが見つからないか、パスが無効です: {file_path}")
        return pd.DataFrame(columns=[required_column])

    encodings = ['cp932', 'shift_jis', 'utf-8', 'utf-8-sig']
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, engine='python', on_bad_lines='skip')
            if required_column in df.columns:
                return df[[required_column]]
            else:
                messagebox.showerror("ファイル読み込みエラー", f"ファイル '{file_path}' に '{required_column}' カラムが見つかりません。")
                return pd.DataFrame(columns=[required_column])
        except UnicodeDecodeError:
            continue
        except Exception as e:
            messagebox.showerror("ファイル読み込みエラー", f"ファイルの読み込み中にエラーが発生しました: {e}")
            print(f"File load error details: {traceback.format_exc()}")
            return pd.DataFrame(columns=[required_column])
    messagebox.showerror("ファイル読み込みエラー", f"ファイル '{file_path}' を適切なエンコーディングで読み込めませんでした。")
    return pd.DataFrame(columns=[required_column])

def load_excel_column_to_list(file_path: str, sheet_name: str, column_name: str, skiprows: int) -> list[str]:
    """Excelファイルから特定のシート、列、行スキップでデータを読み込み、リストとして返す。"""
    if not file_path or not os.path.exists(file_path):
        messagebox.showerror("ファイル読み込みエラー", f"ファイルが見つからないか、パスが無効です: {file_path}")
        return []

    try:
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            usecols=column_name,
            skiprows=skiprows
        )
        if df.empty:
            return []
        return df.dropna().values.flatten().astype(str).tolist()
    except KeyError:
        messagebox.showerror("ファイル読み込みエラー", f"ファイル '{file_path}' にシート '{sheet_name}' が見つからないか、予期せぬ形式です。")
        print(f"File load error details: {traceback.format_exc()}")
        return []
    except Exception as e:
        messagebox.showerror("ファイル読み込みエラー", f"ファイルの読み込み中にエラーが発生しました: {e}")
        print(f"File load error details: {traceback.format_exc()}")
        return []

# --- データ取得関数 ---
def fetch_innosite_data() -> pd.DataFrame:
    """INNOSiTEデータを取得する。"""
    query = "SELECT t_stdddata.* FROM t_stdddata ORDER BY payuserid ASC;"
    return fetch_data_from_db("KSMAIN2_MYSQL", query)

def fetch_excluded_sales_data() -> pd.DataFrame:
    """営業データを取得する。"""
    try:
        # 修正: 対象外営業データの取得クエリを修正
        # 元のクエリ: "SELECT salCode, salKName FROM t_salmst_k WHERE salKName LIKE '%×%' OR salKName LIKE '%・%';"
        # 修正後: 条件を緩和し、すべての営業データを取得
        query = "SELECT salCode, salKName FROM t_salmst_k;"
        df = fetch_data_from_db("KSMAIN_MYSQL", query)
        
        # 取得したデータから対象外営業を抽出（クライアント側でフィルタリング）
        if not df.empty:
            # 名前に「×」または「・」を含む営業コードをフィルタリング
            excluded_df = df[df['salKName'].str.contains('×|・', na=False)]
            if not excluded_df.empty:
                return excluded_df
            else:
                print("警告: 対象外営業データが見つかりませんでした。すべての営業データを返します。")
                return df
        return df
    except Exception as e:
        print(f"対象外営業データ取得エラー: {e}")
        # エラーが発生した場合は空のDataFrameを返す
        return pd.DataFrame(columns=["salCode", "salKName"])

def fetch_bankrupt_shop_data() -> pd.DataFrame:
    """倒産している販売店データを取得する。"""
    query = "SELECT maiCode FROM t_stdmain_h WHERE maiName1 LIKE '%★%' OR maiName1 LIKE '%×%' OR maiName1 LIKE '%▲%';"
    return fetch_data_from_db("KSMAIN_MYSQL", query)

def get_salKName2K_from_salCode(sal_code: str) -> str | None:
    """
    salCodeを元にt_salmst_kからsalKName2Kを取得する汎用関数。
    """
    if not sal_code:
        return None
    query = f"SELECT salKName2K FROM t_salmst_k WHERE salCode = '{sal_code}'"
    try:
        df = fetch_data_from_db("KSMAIN_MYSQL", query)
        if not df.empty:
            return str(df.iloc[0]['salKName2K']).strip()
        return None
    except Exception as e:
        print(f"Error fetching salKName2K for salCode '{sal_code}': {e}")
        return None

# --- 補助データ読み込み関数 ---
def load_totalnet_list(file_path: str | None) -> pd.DataFrame:
    """トータルネットリストをCSVから読み込む。"""
    return load_csv_to_dataframe(file_path, "顧客番号")

# 不要販売店リストを読み込む関数は削除されました（要望#005対応）

# --- 個別チェック関数 ---
def check_dekispart_school_0002(row: pd.Series, error_messages: list[dict]):
    """CHK_0002: IDの桁数が8桁かチェック。"""
    user_id = str(row["stdDID"])
    if not re.fullmatch(r'\d{8}', user_id):
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0002, row.get("stdID_D", "")))

def check_dekispart_school_0003_duplicate(df: pd.DataFrame, error_messages: list[dict]):
    """CHK_0003: IDの重複をチェック。データフレーム全体に対して一度実行。"""
    duplicate_ids = df[df.duplicated(subset=['stdDID'], keep=False)]['stdDID'].unique().tolist()
    for dup_id in duplicate_ids:
        error_messages.append(create_error_entry(dup_id, Config.CHK_ID_0003, ""))

def check_dekispart_school_0004(row: pd.Series, error_messages: list[dict]):
    """CHK_0004: stdDIDとstdDsupIDの最初の8桁が一致しないかチェック。"""
    if pd.notna(row["stdDsupID"]) and str(row["stdDID"])[:8] != str(row["stdDsupID"])[:8]:
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0004, row.get("stdID_D", "")))

def check_dekispart_school_0007(row: pd.Series, error_messages: list[dict]):
    """CHK_0007: 販店1マスタのコード形式をチェック。"""
    std_dsale1 = str(row["stdDsale1"]).strip() if pd.notna(row["stdDsale1"]) else ""
    if std_dsale1:
        if not (
            (std_dsale1.isdigit() and len(std_dsale1) == 6) or
            (std_dsale1.startswith("kshh") and len(std_dsale1) == 4) or
            std_dsale1.startswith("A")
        ):
            error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0007, row.get("stdID_D", "")))

def check_dekispart_school_0008(row: pd.Series, error_messages: list[dict]):
    """CHK_0008: stdDsale1が"ksALL"を含んでいるかチェック。"""
    if "ksALL" in str(row["stdDsale1"]):
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0008, row.get("stdID_D", "")))

def check_dekispart_school_0009(row: pd.Series, error_messages: list[dict]):
    """CHK_0009: stdDsale1が004359(リコー)の場合、stdDsale2が空白だとNG。"""
    if row.get("stdDsale1") == "004359" and not str(row.get("stdDsale2", "")).strip():
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0009, row.get("stdID_D", "")))

def check_dekispart_school_0010(row: pd.Series, error_messages: list[dict]):
    """CHK_0010: stdDsale1が000286(建築資料)の場合、stdDsale2が空白だとNG。"""
    if row.get("stdDsale1") == "000286" and not str(row.get("stdDsale2", "")).strip():
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0010, row.get("stdID_D", "")))

def check_dekispart_school_0011(row: pd.Series, error_messages: list[dict]):
    """CHK_0011: stdSale1が001275(キヤノン(新潟のみ）)の場合、stdSale2が空白だとNG。"""
    if row.get("stdDsale1") == "001275" and not str(row.get("stdDsale2", "")).strip():
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0011, row.get("stdID_D", "")))

def check_dekispart_school_0012(row: pd.Series, bankrupt_shop_data: list[str], error_messages: list[dict]):
    """CHK_0012: 登録販売店が倒産指定されているかチェック。"""
    if not row["stdDKaiyaku"] and row["stdDsale1"] in bankrupt_shop_data:
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0012, row.get("stdID_D", "")))

def check_dekispart_school_0013(row: pd.Series, error_messages: list[dict]):
    """CHK_0013: stdisale1が000332(ITS三島)の場合、stdiNsyu(入金経路)が211でないとNG。"""
    if row.get("stdDsale1") == "000332" and str(row.get("stdDNsyu")) != "211":
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0013, row.get("stdID_D", "")))

def check_dekispart_school_0014(row: pd.Series, error_messages: list[dict]):
    """CHK_0014: stdSale1がA30777(ITS札幌)の場合、stdDNsyuが211でないとNG。"""
    if row.get("stdDsale1") == "A30777" and str(row.get("stdDnkeiro")) != "211": # stdDnkeiroは typo ではないか？ stdDNsyu ではないか？
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0014, row.get("stdID_D", "")))

def check_dekispart_school_0015(row: pd.Series, error_messages: list[dict]):
    """CHK_0015: stdDsale1が000583(富士)の場合、stdDNsyuが211でないとNG。"""
    if row.get("stdDsale1") == "000583" and str(row.get("stdDNsyu")) != "211":
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0015, row.get("stdID_D", "")))

def check_dekispart_school_0016(row: pd.Series, error_messages: list[dict]):
    """CHK_0016: stdDsale1が000659(富士FBI秋田)の場合、stdDNsyuが211でないとNG。"""
    if row.get("stdDsale1") == "000659" and str(row.get("stdDNsyu")) != "211":
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0016, row.get("stdID_D", "")))

def check_dekispart_school_0017(row: pd.Series, error_messages: list[dict]):
    """CHK_0017: stdSale1が000759(精密舎)の場合、stdNsyuが211でないとNG。"""
    if row.get("stdDsale1") == "000759" and str(row.get("stdDNsyu")) != "211": # stdNsyuは typo ではないか？ stdDNsyu ではないか？
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0017, row.get("stdID_D", "")))

def check_dekispart_school_0018(row: pd.Series, error_messages: list[dict]):
    """CHK_0018: 退会(stdDKaiyaku)がTrueで処理中（stdDFlg1）がtrueの場合NG。"""
    if row["stdDKaiyaku"] and row["stdDFlg1"]:
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0018, row.get("stdID_D", "")))

def check_dekispart_school_0019(row: pd.Series, totalnet_list: list[str], error_messages: list[dict]):
    """CHK_0019: stdDNsyu(入金経路)が121の場合にトータルネットに登録がなければNG。"""
    if str(row["stdDNsyu"]) == "121" and str(row["stdDID"]) not in totalnet_list: # stdID_D は typo ? stdDIDが正しいか？
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0019, row.get("stdID_D", "")))

def check_dekispart_school_0020(row: pd.Series, error_messages: list[dict]):
    """CHK_0020: 備考(userbikou1)に更新案内不要という文字列があれば、更新案内が不要(112)となっていない場合にエラー。"""
    # 備考(userbikou1)に「更新案内不要」という文字列がある場合のチェック
    userbikou1 = str(row.get("userbikou1", "")).strip()
    if "更新案内不要" in userbikou1 and str(row["stdDNsyu"]) != "112":
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0020, row.get("stdID_D", "")))

def check_dekispart_school_0021(row: pd.Series, error_messages: list[dict]):
    """CHK_0021: 更新案内不要(112)以外でstdDsale1が旭測器(B88299)の場合はNG。"""
    if str(row["stdDNsyu"]) != "112" and row["stdDsale1"] == "B88299":
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0021, row.get("stdID_D", "")))

def check_dekispart_school_0022(row: pd.Series, excluded_sales_list: list[str], error_messages: list[dict]):
    """CHK_0022: stdDKaiyakuがfalseの場合、stdDtselnoが対象外営業リストに含まれている場合NG。"""
    if not row["stdDKaiyaku"] and row.get("stdDtselno") in excluded_sales_list:
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0022, row.get("stdID_D", "")))

def check_dekispart_school_0023(row: pd.Series, error_messages: list[dict]):
    """CHK_0023: stdDKaiyakuがfalseの場合、stdDtselnoが空白の場合はNG。"""
    if not row["stdDKaiyaku"] and (pd.isna(row.get("stdDtselno")) or str(row.get("stdDtselno", "")).strip() == ""):
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0023, row.get("stdID_D", "")))

def check_dekispart_school_0024(row: pd.Series, error_messages: list[dict]):
    """CHK_0024: stdDKaiyakuがfalseの場合、stdDReyear1が過去の日付になっていたらNG。"""
    if not row["stdDKaiyaku"] and pd.notna(row["stdDReyear1"]):
        try:
            if pd.to_datetime(row["stdDReyear1"]).date() < datetime.now().date():
                error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0024, row.get("stdID_D", "")))
        except ValueError:
            # 日付変換エラーもエラーとして扱うか、別のチェック項目とする
            pass

def check_dekispart_school_0025(row: pd.Series, error_messages: list[dict]):
    """CHK_0025: stdDKaiyakuがtrueの場合、stdDReyear1が未来の日付になっていたらNG。"""
    if row["stdDKaiyaku"] and pd.notna(row["stdDReyear1"]):
        try:
            if pd.to_datetime(row["stdDReyear1"]).date() > datetime.now().date():
                error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0025, row.get("stdID_D", "")))
        except ValueError:
            pass

def check_dekispart_school_0026(row: pd.Series, error_messages: list[dict]):
    """CHK_0026: stdDKaiyakuがfalseの場合、stdDAcdayが1年2か月以上前ならNG。"""
    if not row["stdDKaiyaku"] and pd.notna(row["stdDAcday"]):
        try:
            # 1年2か月 = 14か月
            if pd.to_datetime(row["stdDAcday"]).date() < (datetime.now().date() - timedelta(days=14*30)): # 近似値
                error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0026, row.get("stdID_D", "")))
        except ValueError:
            pass

def check_dekispart_school_0027(row: pd.Series, error_messages: list[dict]):
    """CHK_0027: stdDKaiyakuがtrueの場合、stdDAcdayが未来の日付になっていたらNG。"""
    if row["stdDKaiyaku"] and pd.notna(row["stdDAcday"]):
        try:
            if pd.to_datetime(row["stdDAcday"]).date() > datetime.now().date():
                error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0027, row.get("stdID_D", "")))
        except ValueError:
            pass

def check_dekispart_school_0028(row: pd.Series, error_messages: list[dict]):
    """CHK_0028: stdDKaiyakuがfalseの場合、stdDRemonが空白の場合はNG。"""
    if not row["stdDKaiyaku"] and (pd.isna(row.get("stdDRemon")) or str(row.get("stdDRemon", "")).strip() == ""):
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0028, row.get("stdID_D", "")))

def check_dekispart_school_0029(row: pd.Series, error_messages: list[dict]):
    """CHK_0029: stdDKaiyakuがfalseの場合、stdDReyear1が空白の場合はNG。"""
    if not row["stdDKaiyaku"] and pd.isna(row.get("stdDReyear1")):
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0029, row.get("stdID_D", "")))

def check_dekispart_school_0030(row: pd.Series, error_messages: list[dict]):
    """CHK_0030: stdDKaiyakuがfalseの場合、stdDReyear1が1年3か月以上先の場合チェック。"""
    if not row["stdDKaiyaku"] and pd.notna(row["stdDReyear1"]):
        try:
            # 1年3か月 = 15か月
            if pd.to_datetime(row["stdDReyear1"]).date() > (datetime.now().date() + timedelta(days=15*30)): # 近似値
                error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0030, row.get("stdID_D", "")))
        except ValueError:
            pass

def check_dekispart_school_0031(row: pd.Series, error_messages: list[dict]):
    """CHK_0031: stdDKaiyakuがfalseの場合、stdDReyear2が空白の場合はNG。"""
    if not row["stdDKaiyaku"] and (pd.isna(row.get("stdDReyear2")) or str(row.get("stdDReyear2", "")).strip() == ""):
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0031, row.get("stdID_D", "")))

def check_dekispart_school_0032(row: pd.Series, error_messages: list[dict]):
    """CHK_0032: stdDKaiyakuがtrueの場合、stdDKaiyakuOPがfalseだとNG。"""
    if row["stdDKaiyaku"] and not row["stdDKaiyakuOP"]:
        error_messages.append(create_error_entry(row["stdDID"], Config.CHK_ID_0032, row.get("stdID_D", "")))

# --- メインチェック関数 ---
def validate_data(
    df: pd.DataFrame,
    progress_callback: Callable | None,
    totalnet_list_df: pd.DataFrame,
    excluded_sales_list: list[str],
    bankrupt_shop_data: list[str]
) -> pd.DataFrame:
    """
    INNOSiTEデータを検証し、エラーをDataFrameとして返す。
    """
    errors: list[dict] = []
    total_ids = len(df)
    
    # 補助リストを必要な形式に変換（もし必要であれば）
    totalnet_list = totalnet_list_df["顧客番号"].astype(str).tolist() if not totalnet_list_df.empty else []
    
    # CHK_0003 のためのID重複チェック (一度だけ実行)
    check_dekispart_school_0003_duplicate(df, errors)

    for index, row in df.iterrows():
        row_errors: list[dict] = []
        current_id = row.get("stdDID", "N/A")
        maintenance_id = row.get("stdID_D", "")  # 保守整理番号を取得

        if progress_callback and (index % 10 == 0 or index == total_ids - 1):
            progress_callback(f"DEKISPART_SCHOOL: {current_id} をチェック中 ({index+1}/{total_ids})")

        # 個別のチェック関数を呼び出し (関数名をCHK_IDを含む形に修正)
        # 各チェック関数に保守整理番号を渡す
        check_dekispart_school_0002(row, row_errors)
        check_dekispart_school_0004(row, row_errors)
        check_dekispart_school_0007(row, row_errors)
        check_dekispart_school_0008(row, row_errors)
        check_dekispart_school_0009(row, row_errors)
        check_dekispart_school_0010(row, row_errors)
        check_dekispart_school_0011(row, row_errors)
        check_dekispart_school_0012(row, bankrupt_shop_data, row_errors)
        check_dekispart_school_0013(row, row_errors)
        check_dekispart_school_0014(row, row_errors)
        check_dekispart_school_0015(row, row_errors)
        check_dekispart_school_0016(row, row_errors)
        check_dekispart_school_0017(row, row_errors)
        check_dekispart_school_0018(row, row_errors)
        check_dekispart_school_0019(row, totalnet_list, row_errors)
        check_dekispart_school_0020(row, row_errors)
        check_dekispart_school_0021(row, row_errors)
        check_dekispart_school_0022(row, excluded_sales_list, row_errors)
        check_dekispart_school_0023(row, row_errors)
        check_dekispart_school_0024(row, row_errors)
        check_dekispart_school_0025(row, row_errors)
        check_dekispart_school_0026(row, row_errors)
        check_dekispart_school_0027(row, row_errors)
        check_dekispart_school_0028(row, row_errors)
        check_dekispart_school_0029(row, row_errors)
        check_dekispart_school_0030(row, row_errors)
        check_dekispart_school_0031(row, row_errors)
        check_dekispart_school_0032(row, row_errors)
        
        # 保守整理番号を追加
        for error in row_errors:
            if "保守整理番号" not in error or not error["保守整理番号"]:
                error["保守整理番号"] = maintenance_id
        
        errors.extend(row_errors)

    return pd.DataFrame(errors, columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"])

# --- 結果保存関数 ---
def save_results_to_excel(errors_df: pd.DataFrame):
    """結果をExcelファイルに保存する。"""
    if not errors_df.empty:
        try:
            errors_df.to_excel(Config.OUTPUT_EXCEL_FILENAME, index=False)
            messagebox.showinfo("完了", f"チェック結果を {Config.OUTPUT_EXCEL_FILENAME} に保存しました。")
        except Exception as e:
            messagebox.showerror("ファイル保存エラー", f"結果の保存中にエラーが発生しました: {e}")
            print(f"Save to Excel error details: {traceback.format_exc()}")
    else:
        messagebox.showinfo("完了", "エラーは見つかりませんでした。Excel ファイルは作成されません。")

# --- エントリポイント ---
def run_dekispart_school_check(progress_callback: Callable | None = None, aux_paths: dict | None = None) -> pd.DataFrame:
    """
    DEKISPART_SCHOOLのデータチェックを実行するメインエントリポイント。
    """
    all_errors: list[dict] = []

    try:
        if progress_callback:
            progress_callback("DEKISPART_SCHOOL: 補助ファイルを読み込み中...")

        # 補助ファイルのパスを取得
        totalnet_list_path = aux_paths.get("totalnet_list_path") if aux_paths else Config.TOTALNET_LIST_DEFAULT_PATH
        # 不要販売店リストのパス取得は削除されました（要望#005対応）

        totalnet_df = load_totalnet_list(totalnet_list_path)
        # 不要販売店リストの読み込みは削除されました（要望#005対応）
        excluded_sales_df = fetch_excluded_sales_data()
        bankrupt_shop_df = fetch_bankrupt_shop_data()

        if totalnet_df.empty:
            all_errors.append(create_error_entry("N/A", Config.AUX_FILE_TOTALNET_MISSING_ID))
        # 不要販売店リストのチェックは削除されました（要望#005対応）
        if excluded_sales_df.empty:
            messagebox.showwarning("データ取得警告", "対象外営業データが取得できませんでした。関連チェックはスキップされます。")
        if bankrupt_shop_df.empty:
            messagebox.showwarning("データ取得警告", "倒産販売店データが取得できませんでした。関連チェックはスキップされます。")
        
        # 必須補助ファイルがない場合、ここで処理を中断してエラーを返す
        if all_errors:
            return pd.DataFrame(all_errors, columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"])

        excluded_sales_list = excluded_sales_df["salCode"].tolist() if not excluded_sales_df.empty else []
        bankrupt_shop_data = bankrupt_shop_df["maiCode"].tolist() if not bankrupt_shop_df.empty else []

        if progress_callback:
            progress_callback("DEKISPART_SCHOOL: 基幹データを取得中...")

        df = fetch_innosite_data()

        if df.empty:
            all_errors.append(create_error_entry("N/A", Config.DATA_FETCH_ERROR_ID))
            return pd.DataFrame(all_errors, columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"])

        if progress_callback:
            progress_callback("DEKISPART_SCHOOL: データチェックを実行中...")

        validation_results_df = validate_data(
            df,
            progress_callback,
            totalnet_df,
            # unnecessary_dealer_list削除（要望#005対応）
            excluded_sales_list,
            bankrupt_shop_data
        )

        return validation_results_df.assign(シリーズ="DEKISPART_SCHOOL")[["シリーズ", "ユーザID", "保守整理番号", "チェックID"]]

    except Exception as e:
        error_detail = traceback.format_exc()
        messagebox.showerror("DEKISPART_SCHOOL エラー", f"DEKISPART_SCHOOLチェック中に予期せぬエラーが発生しました。\n詳細はログを確認してください。\nエラー: {e}")
        print(f"DEKISPART_SCHOOL エラー詳細:\n{error_detail}")
        return pd.DataFrame([{
            "シリーズ": "DEKISPART_SCHOOL",
            "ユーザID": "N/A",
            "チェックID": f"処理中にエラーが発生しました: {e}"
        }], columns=["シリーズ", "ユーザID", "チェックID"])

# --- GUI連携用関数 ---
def get_auxiliary_file_paths() -> dict:
    """補助ファイルのパスをGUIでユーザーから取得する。"""
    messagebox.showinfo("ファイル選択", "トータルネット登録ファイルを選択してください。")
    totalnet_path = select_file_with_gui("トータルネット登録ファイルを選択してください", [("CSV Files", "*.csv")])

    # 不要販売店リストファイルの選択は削除されました（要望#005対応）

    return {
        "totalnet_list_path": totalnet_path,
        # "unnecessary_dealer_list_path"は削除されました（要望#005対応）
    }

# --- メイン実行部分 ---
def main():
    """アプリケーションのエントリポイント。"""
    try:
        # 補助ファイルのパスをGUIで取得
        aux_paths = get_auxiliary_file_paths()
        
        # GUIコールバックのダミー（進捗表示がない場合はNoneでも良い）
        def dummy_progress_callback(message):
            print(f"進捗: {message}")

        errors_df = run_dekispart_school_check(progress_callback=dummy_progress_callback, aux_paths=aux_paths)
        save_results_to_excel(errors_df)
    except Exception as e:
        messagebox.showerror("アプリケーションエラー", f"アプリケーション実行中にエラーが発生しました: {e}")
        print(f"Application error details: {traceback.format_exc()}")

if __name__ == "__main__":
    main()