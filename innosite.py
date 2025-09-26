import pymysql
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import traceback # Import traceback for detailed error logging
import configparser
import re
import pyodbc


def _normalize_odbc_driver(value: str) -> str:
    driver = value.strip()
    if driver.startswith('{') and driver.endswith('}'):
        driver = driver[1:-1]
    return driver


def _enable_deprecated_tls_if_requested(db_config: configparser.SectionProxy) -> None:
    try:
        allow = db_config.getboolean('allow_deprecated_tls')
    except (ValueError, configparser.NoOptionError):
        allow = False
    if allow:
        os.environ['ODBCIGNOREDEPRECATEDTLS'] = '1'


def _build_sqlserver_conn_str(db_config: configparser.SectionProxy) -> str:
    _enable_deprecated_tls_if_requested(db_config)
    driver = _normalize_odbc_driver(db_config['driver'])
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={db_config['server']}",
        f"DATABASE={db_config['database']}",
        f"UID={db_config['uid']}",
        f"PWD={db_config['pwd']}"
    ]
    trust_flag = db_config.get('trust_server_certificate', '').strip()
    if trust_flag:
        parts.append(f"TrustServerCertificate={trust_flag}")
    encrypt_flag = db_config.get('encrypt', '').strip()
    if encrypt_flag:
        parts.append(f"Encrypt={encrypt_flag}")
    return ';'.join(parts) + ';'

# INNOSiTEデータを取得
def fetch_data():

    # MySQLへの接続
    config = configparser.ConfigParser()
    config.read('config.ini')
    db_config = config['KSMAIN2_MYSQL']

    conn = pymysql.connect(
        host=db_config['host'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password'],
        charset=db_config['charset'],
    )
    cursor = conn.cursor()
    cursor.execute("SELECT t_stdidata.*, t_stdiproid.* FROM t_stdidata INNER JOIN t_stdiproid ON t_stdidata.stdiid = t_stdiproid.id_stdiid ORDER BY stdid_i ASC;")  # 任意のクエリ
    
    # カラム名を取得
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    conn.close()

    # DataFrameに変換
    df = pd.DataFrame(data, columns=columns)

    return df

# 営業データを取得
def fetch_excluded_sales_data():
    # MySQLへの接続
    config = configparser.ConfigParser()
    config.read('config.ini')
    db_config = config['KSMAIN_MYSQL']

    conn = pymysql.connect(
        host=db_config['host'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password'],
        charset=db_config['charset'],
    )
    cursor = conn.cursor()
    cursor.execute("SELECT salCode, salKName FROM t_salmst_k WHERE salKName LIKE '%×%' OR salKName LIKE '%・%';")
    
    # カラム名を取得
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    conn.close()

    # DataFrameに変換
    df = pd.DataFrame(data, columns=columns)

    return df

# 倒産している販売店データ取得
def fetch_bankrupt_shop_data():
    # MySQLへの接続
    config = configparser.ConfigParser()
    config.read('config.ini')
    db_config = config['KSMAIN_MYSQL']

    conn = pymysql.connect(
        host=db_config['host'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password'],
        charset=db_config['charset'],
    )
    cursor = conn.cursor()
    cursor.execute("SELECT maiCode FROM t_stdmain_h WHERE maiName1 LIKE '%★%' OR maiName1 LIKE '%×%' OR maiName1 LIKE '%▲%';")
    
    # カラム名を取得
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    conn.close()

    # DataFrameに変換
    df = pd.DataFrame(data, columns=columns)

    return df

# 保守DBからデータを取得
def fetch_hosyu_data():
    config = configparser.ConfigParser()
    config.read('config.ini')
    db_config = config['DEKISPART_MNT_DB']

    conn_str = _build_sqlserver_conn_str(db_config)
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM T_stdData")  # 任意のクエリ
    #cursor.execute("SELECT TOP 1 * FROM T_stdData")  # 任意のクエリ
    columns = [column[0] for column in cursor.description]  # カラム名を取得
    data = cursor.fetchall()
    conn.close()

    # データが1列の場合、各行をリストに変換
    data = [list(row) for row in data]  # 必要に応じて形状を修正

    # DataFrameに変換
    df = pd.DataFrame(data, columns=columns)
    return df

def get_sales_master_data():
    config = configparser.ConfigParser()
    config.read('config.ini')
    db_config = config['DEKISPART_MNT_DB']

    conn_str = _build_sqlserver_conn_str(db_config)
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM T_salMst")  # 任意のクエリ
    columns = [column[0] for column in cursor.description]  # カラム名を取得
    data = cursor.fetchall()
    conn.close()

    # データが1列の場合、各行をリストに変換
    data = [list(row) for row in data]  # 必要に応じて形状を修正

    # DataFrameに変換
    df = pd.DataFrame(data, columns=columns)
    return df

# 保守DB情報から整理番号、住所リストのマッピングリスト取得
def get_maintenance_id_address_map():
    """
    保守DBから整理番号(stdID)と住所(stdAdd)のマップを取得します。
    キーはstdID、値は整形済みのstdAddです。
    """
    hosyu_data_map = {}
    # fetch_hosyu_dataの結果がDataFrameであることを前提としています。
    for index, row_hosyu in fetch_hosyu_data().iterrows():
        hosyu_data_map[str(row_hosyu["stdID"]).strip()] = str(row_hosyu["stdAdd"]).strip()
        return hosyu_data_map
    
# 保守DB情報から整理番号、営業担当のマッピングリスト取得
def get_maintenance_id_salses_representative_map():
    """
    保守DBから整理番号(stdID)営業担当()のマップを取得します。
    キーはstdID、値は整形済みの()です。
    """
    hosyu_data_map = {}
    # fetch_hosyu_dataの結果がDataFrameであることを前提としています。
    for index, row_hosyu in fetch_hosyu_data().iterrows():
        hosyu_data_map[str(row_hosyu["stdID"]).strip()] = str(row_hosyu["stdTselNo"]).strip()
        return hosyu_data_map

def get_maintenance_id_sale1_map():
    """
    保守DBから整理番号(stdID)と販店1マスタ(stdSale1)のマップを取得します。
    キーはstdID、値は整形済みのstdSale1です。
    """
    hosyu_data_map = {}
    # fetch_hosyu_dataの結果がDataFrameであることを前提としています。
    for index, row_hosyu in fetch_hosyu_data().iterrows():
        hosyu_data_map[str(row_hosyu["stdID"]).strip()] = str(row_hosyu["stdSale1"]).strip()
    return hosyu_data_map

# 担当者マスタ（商魂）を読み込む
def load_sales_person_list_from_csv(file_path=None):
    if not file_path or not os.path.exists(file_path):
        # messagebox.showerror("エラー", f"担当者マスタファイルが見つからないか、パスが無効です: {file_path}")
        return [] # 空のリストを返す

    encodings = ['cp932', 'shift_jis', 'utf-8', 'utf-8-sig']
    required_columns = ["担当者コード", "担当者名", "部門コード"]
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, engine='python', on_bad_lines='skip')
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("ファイル読み込みエラー", f"担当者マスタファイル '{file_path}' に必要なカラム({', '.join(required_columns)})が不足しています。")
                return []
            sales_person_list = df[required_columns].to_dict(orient='records')
            return sales_person_list
        except UnicodeDecodeError:
            continue
        except Exception as e:
            messagebox.showerror("ファイル読み込みエラー", f"担当者マスタファイルの読み込み中にエラーが発生しました: {e}")
            return []
    messagebox.showerror("ファイル読み込みエラー", f"担当者マスタファイル '{file_path}' を適切なエンコーディングで読み込めませんでした。")
    return []

# 担当者マスタファイルを選択する
def get_sales_person_list_file_path():
    root = tk.Tk()
    root.withdraw()  # ウィンドウを非表示にする
    file_path = filedialog.askopenfilename(title="担当者マスタを選択してください", filetypes=[("CSV Files", "*.csv")])
    return file_path

# 得意先マスタ（商魂）を読み込む
def load_customers_list_from_csv(file_path=None):
    if not file_path or not os.path.exists(file_path):
        # messagebox.showerror("エラー", f"得意先マスタファイルが見つからないか、パスが無効です: {file_path}")
        return [] # 空のリストを返す

    encodings = ['cp932', 'shift_jis', 'utf-8', 'utf-8-sig']
    required_columns = ["得意先コード", "得意先名１", "使用区分"]
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, engine='python', on_bad_lines='skip')
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("ファイル読み込みエラー", f"得意先マスタファイル '{file_path}' に必要なカラム({', '.join(required_columns)})が不足しています。")
                return []
            customers_list = df[required_columns].to_dict(orient='records')
            return customers_list
        except UnicodeDecodeError:
            continue
        except Exception as e:
            messagebox.showerror("ファイル読み込みエラー", f"得意先マスタファイルの読み込み中にエラーが発生しました: {e}")
            return []
    messagebox.showerror("ファイル読み込みエラー", f"得意先マスタファイル '{file_path}' を適切なエンコーディングで読み込めませんでした。")
    return []

# 得意先マスタファイルを選択する
def get_customers_list_file_path():
    root = tk.Tk()
    root.withdraw()  # ウィンドウを非表示にする
    file_path = filedialog.askopenfilename(title="得意先マスタを選択してください", filetypes=[("CSV Files", "*.csv")])
    return file_path

def _add_error_message(error_messages, user_id, check_id, maintenance_id=None):
    """共通のエラーメッセージを追加するヘルパー関数（保守整理番号を含む）"""
    error_messages.append({
        "シリーズ": "INNOSiTE",
        "ユーザID": user_id,
        "保守整理番号": maintenance_id if maintenance_id else "",  # 保守整理番号を追加
        "チェックID": check_id
    })

# --- 各チェックロジックをカプセル化した関数群 ---
# これらの関数は、対象の行 (Pandas Series) とエラーリスト、
# そして必要に応じて事前ロードされたマスタデータを受け取ります。

def check_innosite_0001(row, errors_list):
    """INNOSITE_CHK_0001: stdUserIDが8桁でない場合NG"""
    user_id = str(row.get("stdiinnoid", "")).strip()
    if not re.fullmatch(r'\d{8}', user_id):
        _add_error_message(errors_list, user_id, "INNOSITE_CHK_0001", row.get("stdid_i", ""))

def check_innosite_0002(row, errors_list):
    """
    INNOSITE_CHK_0002: 価格計算チェック
    stdiinnoid、stdipccode、stdidiscountの組み合わせに基づいて
    stdipricetotalが正しい計算結果と一致するかをチェック
    """
    stdiinnoid = str(row.get("stdiinnoid", ""))
    stdipccode = str(row.get("stdipccode", ""))
    stdidiscount = row.get("stdidiscount", 0)
    stdipricetotal = row.get("stdipricetotal", 0)
    stdiKainsyu = row.get("stdiKainsyu", 0)
    
    # 数値型に変換
    try:
        stdidiscount = int(stdidiscount) if stdidiscount is not None else 0
        stdipricetotal = float(stdipricetotal) if stdipricetotal is not None else 0
        stdiKainsyu = int(stdiKainsyu) if stdiKainsyu is not None else 0
    except (ValueError, TypeError):
        return  # 数値変換できない場合はスキップ
    
    expected_price = None
    
    # 各条件に基づく価格計算
    if stdiinnoid.startswith("3110") and stdipccode == "1439":
        if stdidiscount == 0:
            expected_price = 60000 * stdiKainsyu
        elif stdidiscount == -1:
            expected_price = (60000 * 2) + ((60000 / 2) * (stdiKainsyu - 2))
    
    elif stdiinnoid.startswith("3510") and stdipccode == "1483":
        if stdidiscount == 0:
            expected_price = 60000 * stdiKainsyu
        elif stdidiscount == -1:
            expected_price = (60000 * 2) + ((60000 / 2) * (stdiKainsyu - 2))
    
    elif stdiinnoid.startswith("3210") and stdipccode == "1541":
        expected_price = 20000 * stdiKainsyu
    
    elif stdiinnoid.startswith("3310") and stdipccode == "1546":
        expected_price = 40000 * stdiKainsyu
    
    elif stdiinnoid.startswith("3610") and stdipccode == "1607":
        expected_price = 90000 * stdiKainsyu
    
    elif stdiinnoid.startswith("3410") and stdipccode == "1608":
        expected_price = 30000 * stdiKainsyu
    
    # 計算結果と実際の価格を比較
    if expected_price is not None and abs(stdipricetotal - expected_price) > 0.01:  # 浮動小数点の誤差を考慮
        _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0002", row.get("stdid_i", ""))

def check_innosite_0003(row, errors_list):
    """INNOSITE_CHK_0003: 保守整理番号(stdid_i)が空白の場合NG"""
    stdid_i = str(row.get("stdid_i", "")).strip()
    if not stdid_i: # 空文字列またはNoneの場合にTrue
        _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0003", row.get("stdid_i", ""))

def check_innosite_0004(row, errors_list):
    """INNOSITE_CHK_0004: stdSale1(販店1マスタ)のバリデーション"""
    if pd.notna(row["stdisale1"]) and str(row["stdisale1"]).strip() != "":
        if not (str(row["stdisale1"]).isdigit() and len(str(row["stdisale1"])) == 6) and \
            not (str(row["stdisale1"]).startswith("kshh") and len(str(row["stdisale1"])) == 4) and \
            not str(row["stdisale1"]).startswith("A"):
                _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0004", row.get("stdid_i", ""))

def check_innosite_0005(row, errors_list):
    """INNOSITE_CHK_0005: stdisale1が"ksALL"を含んでいる場合はNG"""
    if "ksALL" in str(row.get("stdisale1", "")):
        _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0005", row.get("stdid_i", ""))

def check_innosite_0006(row, errors_list):
    """INNOSITE_CHK_0006: stdisale1が004359の場合、stdisale2が空白だとNG"""
    if str(row.get("stdisale1")) == "004359" and not str(row.get("stdisale2", "")).strip():
        _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0006", row.get("stdid_i", ""))

def check_innosite_0007(row, errors_list):
    """INNOSITE_CHK_0007: stdSale1が000286の場合、stdSale2が空白だとNG"""
    if str(row.get("stdisale1")) == "000286" and not str(row.get("stdisale2", "")).strip():
        _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0007", row.get("stdid_i", ""))

def check_innosite_0008(row, errors_list, maintenance_id_address_map):
    """INNOSITE_CHK_0008: stdSale1が001275の場合、保守DBの住所が新潟県でstdisale2が空白だとNG"""
    stdid_i = str(row.get("stdid_i", "")).strip()
    if str(row.get("stdisale1")) == "001275":
        if stdid_i and stdid_i in maintenance_id_address_map:
            hosyu_std_add = maintenance_id_address_map[stdid_i]
            if hosyu_std_add.startswith("新潟県") and not str(row.get("stdisale2", "")).strip():
                _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0008", row.get("stdid_i", ""))

def check_innosite_0009(row, errors_list, bankrupt_shop_data):
    """INNOSITE_CHK_0009: 登録販売店が倒産している場合はNG"""
    if not row.get("stdikaiyaku", False) and str(row.get("stdisale1")) in bankrupt_shop_data:
        _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0009", row.get("stdid_i", ""))

def _check_sale1_nsyu_211(row, errors_list, sale_code, check_id):
    """stdisale1が特定のコードの場合、stdiNsyuが211でないとNGの汎用チェック"""
    if str(row.get("stdisale1")) == sale_code and str(row.get("stdiNsyu")) != "211":
        _add_error_message(errors_list, row["stdiinnoid"], check_id, row.get("stdid_i", ""))

def check_innosite_0010(row, errors_list):
    """INNOSITE_CHK_0010: stdisale1が"000332"の場合、stdiNsyuが"211"でないとNG"""
    _check_sale1_nsyu_211(row, errors_list, "000332", "INNOSITE_CHK_0010")

def check_innosite_0011(row, errors_list):
    """INNOSITE_CHK_0011: stdSale1がA30777の場合、stdiNsyuが211でないとNG"""
    _check_sale1_nsyu_211(row, errors_list, "A30777", "INNOSITE_CHK_0011")

def check_innosite_0012(row, errors_list):
    """INNOSITE_CHK_0012: stdisale1が000583の場合、stdNsyuが211でないとNG"""
    _check_sale1_nsyu_211(row, errors_list, "000583", "INNOSITE_CHK_0012")

def check_innosite_0013(row, errors_list):
    """INNOSITE_CHK_0013: stdSale1が000659の場合、stdNsyuが211でないとNG"""
    _check_sale1_nsyu_211(row, errors_list, "000659", "INNOSITE_CHK_0013")

def check_innosite_0014(row, errors_list):
    """INNOSITE_CHK_0014: stdSale1が000759の場合、stdNsyuが211でないとNG"""
    _check_sale1_nsyu_211(row, errors_list, "000759", "INNOSITE_CHK_0014")

def check_innosite_0016(row, errors_list):
    """INNOSITE_CHK_0016: stdibiko1、stdibiko2に「補助金」を含む場合はNG（退会ユーザーのみ）"""
    if row.get("stdikaiyaku", False):
        stdibiko1 = str(row.get("stdibiko1", "")).strip()
        stdibiko2 = str(row.get("stdibiko2", "")).strip()
        if "補助金" in stdibiko1 or "補助金" in stdibiko2:
            _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0016", row.get("stdid_i", ""))

def check_innosite_0017(row, errors_list):
    """INNOSITE_CHK_0017: 3本目半額レ点チェック(stdidicount)がTRUEで、本数(stdiKainsyu)は3本以上でないとNG"""
    stdidicount = row.get("stdidicount", False) # デフォルト値をFalseに
    try:
        stdiKainsyu = int(row.get("stdiKainsyu", 0)) # デフォルト値を0に
    except ValueError:
        # stdiKainsyuが数値に変換できない場合のハンドリング
        _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0017_INVALID_KAINSYU", row.get("stdid_i", ""))
        stdiKainsyu = 0 # エラーを記録し、後続のチェックで影響が出ないようにする

    if stdidicount and stdiKainsyu < 3:
        _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0017", row.get("stdid_i", ""))

# CHK_0018, CHK_0019 は元のコードでコメントアウトされているため含めません。

def check_innosite_0020(row, errors_list):
    """INNOSITE_CHK_0020: 退会(stdikaiyaku)がTrueで処理中（stdiflg1）がtrueの場合NG"""
    if row.get("stdikaiyaku", False) and row.get("stdiflg1", False):
        _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0020", row.get("stdid_i", ""))

def check_innosite_0022(row, errors_list):
    """INNOSITE_CHK_0022: stdikaiyakuがFalseかつstdireyear1が過去の日付になっている場合NG"""
    if not row.get("stdikaiyaku", False) and pd.notna(row.get("stdireyear1")):
        try:
            # PandasのTimestamp型かdatetimeオブジェクトか確認して処理
            ireyear1_date = row["stdireyear1"].date() if isinstance(row["stdireyear1"], pd.Timestamp) else datetime.strptime(str(row["stdireyear1"]), "%Y-%m-%d").date()
            if ireyear1_date < datetime.now().date():
                _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0022", row.get("stdid_i", ""))
        except (ValueError, TypeError):
            # 日付形式が不正な場合や型が異なる場合のハンドリング
            _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0022_DATE_ERROR", row.get("stdid_i", ""))

def check_innosite_0023(row, errors_list):
    """INNOSITE_CHK_0023: stdikaiyakuがtrueの場合、stdireyear1が未来の日付になっていたらNG。ただし、stdibiko2に退会の文字があればOKとする"""
    if row.get("stdikaiyaku", False):
        stdibiko2 = str(row.get("stdibiko2", "")).strip()
        if pd.notna(row.get("stdireyear1")):
            try:
                ireyear1_date = row["stdireyear1"].date() if isinstance(row["stdireyear1"], pd.Timestamp) else datetime.strptime(str(row["stdireyear1"]), "%Y-%m-%d").date()
                if ireyear1_date > datetime.now().date() and "退会" not in stdibiko2:
                    _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0023", row.get("stdid_i", ""))
            except (ValueError, TypeError):
                _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0023_DATE_ERROR", row.get("stdid_i", ""))

def check_innosite_0024(row, errors_list):
    """
    INNOSITE_CHK_0024: stdikaiyakuがfalseの場合、会員期間開始日(stdiReyear2)は、加入日(stdiAcday)の翌月から始まっているかチェック
    """
    if not row.get("stdikaiyaku", False):
        stdiacday_str = str(row.get("stdiacday", "")).strip()
        stdireyear2_str = str(row.get("stdireyear2", "")).strip()

        if not stdiacday_str or not stdireyear2_str:
            # 日付が空白の場合はチェックをスキップ、またはエラーとするか要検討
            # 今回はスキップする
            return

        try:
            # 加入日をパース
            stdiacday_date = datetime.strptime(stdiacday_str, "%Y-%m-%d").date()
            # 会員期間開始日をパース
            stdireyear2_date = datetime.strptime(stdireyear2_str, "%Y-%m-%d").date()

            # 加入日の翌月1日を計算
            # 加入日の月を1ヶ月進める
            if stdiacday_date.month == 12:
                expected_start_date = stdiacday_date.replace(year=stdiacday_date.year + 1, month=1, day=1)
            else:
                expected_start_date = stdiacday_date.replace(month=stdiacday_date.month + 1, day=1)

            # 会員期間開始日が期待される日付と一致しない場合NG
            if stdireyear2_date != expected_start_date:
                _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0024", row.get("stdid_i", ""))

        except (ValueError, TypeError):
            # 日付形式が不正な場合
            _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0024", row.get("stdid_i", ""))

def check_innosite_0025(row, errors_list):
    """INNOSITE_CHK_0025: stdikaiyakuがtrueの場合、stdiacdayが未来の日付になっていたらNG。ただし、stdibiko2に退会の文字があればOKとする"""
    if row.get("stdikaiyaku", False):
        stdibiko2 = str(row.get("stdibiko2", "")).strip()
        if pd.notna(row.get("stdiacday")):
            try:
                stdiacday_date = row["stdiacday"].date() if isinstance(row["stdiacday"], pd.Timestamp) else datetime.strptime(str(row["stdiacday"]), "%Y-%m-%d").date()
                if stdiacday_date > datetime.now().date() and "退会" not in stdibiko2:
                    _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0025", row.get("stdid_i", ""))
            except (ValueError, TypeError):
                _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0025_DATE_ERROR", row.get("stdid_i", ""))

# 空白チェックの汎用ヘルパー関数
def _check_innosite_not_blank(row, errors_list, column_name, check_id):
    """
    INNOSITE: 指定されたカラムが空白（NaN, None, 空文字列）でないことをチェックする。
    stdikaiyakuがFalseの場合に適用。
    """
    # row.get(column_name) で KeyError を防ぎ、str().strip() で空白文字を考慮
    # pd.isna() で NaN や None をチェック
    column_value = row.get(column_name)
    if not row.get("stdikaiyaku", False) and (pd.isna(column_value) or str(column_value).strip() == ""):
        _add_error_message(errors_list, row["stdiinnoid"], check_id, row.get("stdid_i", ""))

def check_innosite_0026(row, errors_list):
    """INNOSITE_CHK_0026: stdikaiyakuがfalseの場合、stdiremonが空白の場合NG"""
    _check_innosite_not_blank(row, errors_list, "stdiremon", "INNOSITE_CHK_0026")

def check_innosite_0027(row, errors_list):
    """INNOSITE_CHK_0027: stdikaiyakuがfalseの場合、stdiAcyearが空白の場合NG"""
    _check_innosite_not_blank(row, errors_list, "stdiAcyear", "INNOSITE_CHK_0027")

def check_innosite_0028(row, errors_list):
    """INNOSITE_CHK_0028: stdikaiyakuがfalseの場合、stdireyear1が空白の場合はNG"""
    _check_innosite_not_blank(row, errors_list, "stdireyear1", "INNOSITE_CHK_0028")

def check_innosite_0029(row, errors_list):
    """INNOSITE_CHK_0029: stdikaiyakuがfalseの場合、stdireyear2が空白の場合はNG"""
    _check_innosite_not_blank(row, errors_list, "stdireyear2", "INNOSITE_CHK_0029")

def check_innosite_0030(row, errors_list):
    """INNOSITE_CHK_0030: stdikaiyakuがfalseの場合、stdiKainsyuが空白の場合はNG"""
    _check_innosite_not_blank(row, errors_list, "stdiKainsyu", "INNOSITE_CHK_0030")

def check_innosite_0031(row, errors_list):
    """INNOSITE_CHK_0031: stdikaiyakuがfalseの場合、stdiremonが空白の場合はNG"""
    # CHK_0026 と重複している可能性がありますが、元のコードの通り維持します。
    _check_innosite_not_blank(row, errors_list, "stdiremon", "INNOSITE_CHK_0031")

# CHK_0032 は元のコードでコメントアウトされているため含めません。

def check_innosite_0033(row, errors_list, sales_person_dict):
    """INNOSITE_CHK_0033: stdikaiyakuがfalseの場合、stditselno紐づく担当名に「×」または「・」があるのでNG"""
    std_tsel_code = str(row.get("stditselno", "")).strip()
    if not row.get("stdikaiyaku", False) and std_tsel_code in sales_person_dict:
        person_name = sales_person_dict[std_tsel_code]
        if person_name.startswith("×") or person_name.startswith("・"):
            _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0033", row.get("stdid_i", ""))

def check_innosite_0034(row, errors_list, sales_master_dict):
    """
    INNOSITE_CHK_0034: 以下の共通条件とNGパターンが満たされる場合NG
    共通条件:
      - stdikaiyaku = False
      - stdibiko2 に「更新案内不要」の文字列が含まれていない
      - salNotifyRenewal = True (sales_master_dict から取得)
    NGパターン:
      - (stdiNsyu=121 かつ stdiNotifyRenewalType=1)
      - (stdiNsyu=121 かつ stdiNotifyRenewalType=2)
      - (stdiNsyu=122 かつ stdiNotifyRenewalType=1)
      - (stdiNsyu=122 かつ stdiNotifyRenewalType=2)
      - (stdiNsyu=211 かつ stdiNotifyRenewalType=1)
      - (stdiNsyu=211 かつ stdiNotifyRenewalType=2)
    """
    # -- 共通条件のチェック --
    is_active_contract = row.get("stdikaiyaku") is False # 解約されていない

    # stdibiko2 に「更新案内不要」の文字列が含まれていない
    # row.get("stdibiko2") が None または空文字列の場合も「含まない」と判断
    is_ibiko2_not_containing_renewal = not (row.get("stdibiko2") and "更新案内不要" in str(row["stdibiko2"]))

    # salNotifyRenewal が True であることを sales_master_dict から確認
    is_sal_notify_renewal_true = False
    std_isale1 = row.get("stdisale1") # stdSale1 に相当するキー
    if std_isale1 and std_isale1 in sales_master_dict: # stdisale1 が有効な値で、辞書に存在する場合
        store_flags = sales_master_dict[std_isale1]
        if store_flags.get('salNotifyRenewal') is True:
            is_sal_notify_renewal_true = True

    # 全ての共通条件が満たされているか
    common_conditions_met = (
        is_active_contract and
        is_ibiko2_not_containing_renewal and
        is_sal_notify_renewal_true
    )

    if not common_conditions_met:
        # 共通条件が満たされていない場合は、NGではないのでここで終了
        return

    # -- NGパターンのチェック --
    stdi_nsyu = row.get("stdiNsyu")
    stdi_notify_renewal_type = row.get("stdiNotifyRenewalType")

    # NGとなる stdiNsyu と stdiNotifyRenewalType の組み合わせを定義
    ng_combinations = {
        (121, 1), (121, 2),
        (122, 1), (122, 2),
        (211, 1), (211, 2)
    }

    # 現在の行の支払い・通知タイプがNGパターンに合致するかチェック
    current_combination = (stdi_nsyu, stdi_notify_renewal_type)
    is_ng_pattern_matched = current_combination in ng_combinations

    # 共通条件とNGパターンが両方満たされた場合にエラーを追加
    if is_ng_pattern_matched:
        # stdiinnoid が存在しない場合を考慮し .get() を使用
        _add_error_message(errors_list, row.get("stdiinnoid"), "INNOSITE_CHK_0034", row.get("stdid_i", ""))

def check_innosite_0035(row, errors_list, sales_master_dict):
    """
    INNOSITE_CHK_0035: 以下の共通条件とNGパターンが満たされる場合NG
    共通条件:
      - stdikaiyaku = False
      - stdibiko2 に「更新案内不要」の文字列が含まれている
    NGパターン:
      - salNotifyRenewal の値にかかわらず、stdiNsyu が (121, 122, 211) のいずれか
        かつ stdiNotifyRenewalType が (1, 2) のいずれか
    """

    # -- 共通条件のチェック --
    is_active_contract = row.get("stdikaiyaku") is False # 解約されていない

    # stdibiko2 に「更新案内不要」の文字列が含まれている
    is_ibiko2_containing_renewal = row.get("stdibiko2") and "更新案内不要" in str(row["stdibiko2"])

    # 全ての共通条件が満たされているか
    common_conditions_met = (
        is_active_contract and
        is_ibiko2_containing_renewal
    )

    if not common_conditions_met:
        # 共通条件が満たされていない場合は、NGではないのでここで終了
        return

    # -- NGパターンのチェック --
    # salNotifyRenewal の値はNG判定の直接的な分岐には使用されないが、要件にあるため取得は行う
    sal_notify_renewal_value = None
    std_isale1 = row.get("stdisale1") # stdSale1 に相当するキー
    if std_isale1 and std_isale1 in sales_master_dict:
        store_flags = sales_master_dict[std_isale1]
        sal_notify_renewal_value = store_flags.get('salNotifyRenewal')

    stdi_nsyu = row.get("stdiNsyu")
    stdi_notify_renewal_type = row.get("stdiNotifyRenewalType")

    # NGとなる stdiNsyu と stdiNotifyRenewalType の組み合わせの基準値を定義
    ng_nsyu_types = {121, 122, 211}
    ng_notify_renewal_types = {1, 2}

    # 現在の行の支払い・通知タイプがNGパターンに合致するかチェック
    # salNotifyRenewal の値に関わらず、stdiNsyuとstdiNotifyRenewalTypeの組み合わせで判定
    is_ng_pattern_matched = (
        stdi_nsyu in ng_nsyu_types and
        stdi_notify_renewal_type in ng_notify_renewal_types
    )

    # 共通条件が満たされ、かつNGパターンに合致した場合にエラーを追加
    if is_ng_pattern_matched:
        # stdiinnoid が存在しない場合を考慮し .get() を使用
        _add_error_message(errors_list, row.get("stdiinnoid"), "INNOSITE_CHK_0035", row.get("stdid_i", ""))

def check_innosite_0036(row, errors_list, sales_master_dict):
    """
    INNOSITE_CHK_0036: 以下の共通条件がすべて満たされ、かつNGパターンに合致する場合NG
    共通条件:
      - stdikaiyaku = False
      - salJifuriDM = TRUE (sales_master_dict より取得)
      - stdiNsyu = 122
      - stdiJifuriDM = TRUE
    NGパターン:
      - stdibiko2 に「自振DM不要」の文字列が含まれていない OR
      - stdibiko2 に「更新案内不要」の文字列が含まれていない
    """

    # -- 共通条件のチェック --
    is_active_contract = row.get("stdikaiyaku") is False

    # salJifuriDM が TRUE であることを sales_master_dict から確認
    is_sal_jifuri_dm_true_from_master = False
    std_isale1 = row.get("stdisale1") # stdSale1 に相当するキー
    if std_isale1 and std_isale1 in sales_master_dict:
        store_flags = sales_master_dict[std_isale1]
        if store_flags.get('salJifuriDM') is True: # sales_master_dict の中に salJifuriDM が True か
            is_sal_jifuri_dm_true_from_master = True

    is_stdi_nsyu_122 = row.get("stdiNsyu") == 122
    is_stdi_jifuri_dm_true = row.get("stdiJifuriDM") is True

    # 全ての共通条件が満たされているか
    common_conditions_met = (
        is_active_contract and
        is_sal_jifuri_dm_true_from_master and
        is_stdi_nsyu_122 and
        is_stdi_jifuri_dm_true
    )

    if not common_conditions_met:
        # 共通条件が満たされていない場合は、NGではないのでここで終了
        return

    # -- NGパターンのチェック --
    # stdibiko2 の内容を取得し、正規化
    stdibiko2_text = str(row.get("stdibiko2", "")).lower().replace(' ', '').replace('　', '')

    # stdibiko2 に「自振DM不要」の文字列が含まれていない
    is_ibiko2_not_containing_jifuri_dm = "自振dm不要" not in stdibiko2_text

    # stdibiko2 に「更新案内不要」の文字列が含まれていない
    is_ibiko2_not_containing_renewal = "更新案内不要" not in stdibiko2_text

    # どちらか一方のNGパターン条件が満たされた場合にNG (ここを修正)
    if is_ibiko2_not_containing_jifuri_dm or is_ibiko2_not_containing_renewal:
        _add_error_message(errors_list, row.get("stdiinnoid"), "INNOSITE_CHK_0036", row.get("stdid_i", ""))

def check_innosite_0037(row, errors_list, sales_master_dict):
    """
    INNOSITE_CHK_0037: 以下の共通条件がすべて満たされる場合NG
    共通条件:
      - stdikaiyaku = False
      - stdibiko2 に「自振DM不要」の文字列が含まれている
      - stdiNsyu = 122
      - stdiJifuriDM = TRUE
    NGパターン:
      - salJifuriDM の値にかかわらず、上記共通条件を満たせばNG
    """

    # -- 共通条件のチェック --
    is_active_contract = row.get("stdikaiyaku") is False

    # stdibiko2 に「自振DM不要」の文字列が含まれている
    is_ibiko2_containing_jifuri_dm = row.get("stdibiko2") and "自振DM不要" in str(row["stdibiko2"])

    is_stdi_nsyu_122 = row.get("stdiNsyu") == 122
    
    is_stdi_jifuri_dm_true = row.get("stdiJifuriDM") is True

    # sales_master_dict から salJifuriDM の値を取得 (NG判定には直接使わないが、要件にあるため取得)
    sal_jifuri_dm_value = None
    std_isale1 = row.get("stdisale1") # stdSale1 に相当するキー
    if std_isale1 and std_isale1 in sales_master_dict:
        store_flags = sales_master_dict[std_isale1]
        sal_jifuri_dm_value = store_flags.get('salJifuriDM')
    # is_sal_jifuri_dm_false = (sal_jifuri_dm_value is False) # 必要であればフラグ化
    # is_sal_jifuri_dm_true = (sal_jifuri_dm_value is True)   # 必要であればフラグ化


    # 全ての共通条件が満たされているか
    common_conditions_met = (
        is_active_contract and
        is_ibiko2_containing_jifuri_dm and
        is_stdi_nsyu_122 and
        is_stdi_jifuri_dm_true
    )

    if not common_conditions_met:
        # 共通条件が満たされていない場合は、NGではないのでここで終了
        return

    # -- NGパターンのチェック --
    # 要件のNGパターンを見ると、salJifuriDM の値によらず
    # 共通条件が満たされていればNGとなるため、ここでは追加の条件判定は不要。
    # 共通条件が満たされた時点でNG
    _add_error_message(errors_list, row.get("stdiinnoid"), "INNOSITE_CHK_0037", row.get("stdid_i", ""))

def check_innosite_0038(row, errors_list, sales_master_dict):
    """
    INNOSITE_CHK_0038: 以下の共通条件がすべて満たされる場合NG
    共通条件:
      - stdikaiyaku = False
      - stdibiko2 に「更新案内不要」の文字列が含まれている
      - stdiNsyu = 122
      - stdiJifuriDM = TRUE
    NGパターン:
      - salJifuriDM の値にかかわらず、上記共通条件を満たせばNG
    """

    # -- 共通条件のチェック --
    is_active_contract = row.get("stdikaiyaku") is False

    # stdibiko2 に「更新案内不要」の文字列が含まれている
    is_ibiko2_containing_renewal = row.get("stdibiko2") and "更新案内不要" in str(row["stdibiko2"])

    is_stdi_nsyu_122 = row.get("stdiNsyu") == 122
    
    is_stdi_jifuri_dm_true = row.get("stdiJifuriDM") is True

    # sales_master_dict から salJifuriDM の値を取得 (NG判定には直接使わないが、要件にあるため取得)
    sal_jifuri_dm_value = None
    std_isale1 = row.get("stdisale1") # stdSale1 に相当するキー
    if std_isale1 and std_isale1 in sales_master_dict:
        store_flags = sales_master_dict[std_isale1]
        sal_jifuri_dm_value = store_flags.get('salJifuriDM')
    # is_sal_jifuri_dm_false = (sal_jifuri_dm_value is False) # 必要であればフラグ化
    # is_sal_jifuri_dm_true = (sal_jifuri_dm_value is True)   # 必要であればフラグ化


    # 全ての共通条件が満たされているか
    common_conditions_met = (
        is_active_contract and
        is_ibiko2_containing_renewal and
        is_stdi_nsyu_122 and
        is_stdi_jifuri_dm_true
    )

    if not common_conditions_met:
        # 共通条件が満たされていない場合は、NGではないのでここで終了
        return

    # -- NGパターンのチェック --
    # 要件のNGパターンを見ると、salJifuriDM の値によらず
    # 共通条件が満たされていればNGとなるため、ここでは追加の条件判定は不要。
    # 共通条件が満たされた時点でNG
    _add_error_message(errors_list, row.get("stdiinnoid"), "INNOSITE_CHK_0038", row.get("stdid_i", ""))

def check_innosite_0039(row, errors_list, maintenance_id_sales_representative_map):
    """
    INNOSITE_CHK_0039: 営業担当コードがデキス保守とINNOSiTE保守と一致している場合NG
    """
    if not row.get("stdikaiyaku", False): # Add this condition
        innosite_maintenance_id = str(row.get("stdid_i", "")).strip()
        innosite_sales_rep_code = str(row.get("stditselno", "")).strip()

        if innosite_maintenance_id and innosite_maintenance_id in maintenance_id_sales_representative_map:
            dekisu_sales_rep_code = maintenance_id_sales_representative_map[innosite_maintenance_id]
            if innosite_sales_rep_code == dekisu_sales_rep_code:
                _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0039", row.get("stdid_i", ""))

def check_innosite_0040(row, errors_list, maintenance_id_sale1_map):
    """
    INNOSITE_CHK_0040: 販店1マスタがデキス保守とINNOSiTE保守と一致している場合NG
    """
    if not row.get("stdikaiyaku", False):
        innosite_maintenance_id = str(row.get("stdid_i", "")).strip()
        innosite_sale1 = str(row.get("stdisale1", "")).strip()

        if innosite_maintenance_id and innosite_maintenance_id in maintenance_id_sale1_map:
            dekisu_sale1 = maintenance_id_sale1_map[innosite_maintenance_id]
            if innosite_sale1 == dekisu_sale1:
                _add_error_message(errors_list, row["stdiinnoid"], "INNOSITE_CHK_0040", row.get("stdid_i", ""))

# --- メインのバリデーション実行関数 ---
def validate_data(df, progress_callback, totalnet_list, sales_person_list):
    """
    INNOSITEデータのバリデーションを実行します。

    Args:
        df (pd.DataFrame): チェック対象のDataFrame。
        progress_callback (callable, optional): 進捗を報告するためのコールバック関数。
                                                 引数として進捗メッセージを受け取ります。

    Returns:
        pd.DataFrame: エラーメッセージを含むDataFrame。エラーがない場合は空のDataFrame。
    """
    all_errors = []
    total_ids = len(df)

    print("--- マスタデータ/設定のロード ---")
    # マスタデータ/設定のロードはループの外で一度だけ行う
    totalnet_list = load_totalnet_list_from_csv()
    excluded_sales_list = fetch_excluded_sales_data()["salCode"].tolist() # CHK_0034のロジックから未使用の可能性？
    bankrupt_shop_data = fetch_bankrupt_shop_data()["maiCode"].tolist()
    maintenance_id_address_map = get_maintenance_id_address_map()
    maintenance_id_sales_representative_map = get_maintenance_id_salses_representative_map() # 未使用の可能性？
    maintenance_id_sale1_map = get_maintenance_id_sale1_map()
    sales_person_list = load_sales_person_list_from_csv()
    sales_person_dict = {
        str(person["担当者コード"]): person["担当者名"]
        for person in sales_person_list
        if "担当者コード" in person and "担当者名" in person
    }
    sales_master_df = get_sales_master_data()
    sales_master_dict = {
        item["salCode"]: {
            "salNotifyRenewal": item.get("salNotifyRenewal", False), # キーが存在しない場合を考慮
            "salJifuriDM": item.get("salJifuriDM", False),
        }
        for item in sales_master_df.to_dict(orient="records")
    }
    print("--- マスタデータ/設定のロード完了 ---")

    # 全てのチェック関数をリストにまとめる
    # 特定のマスタデータに依存するチェックは、引数として渡す
    check_functions = [
        check_innosite_0001,
        check_innosite_0002,
        check_innosite_0003,
        check_innosite_0004,
        check_innosite_0005,
        check_innosite_0006,
        check_innosite_0007,
        lambda row, errors: check_innosite_0008(row, errors, maintenance_id_address_map), # マップを渡す
        lambda row, errors: check_innosite_0009(row, errors, bankrupt_shop_data), # リストを渡す
        check_innosite_0010,
        check_innosite_0011,
        check_innosite_0012,
        check_innosite_0013,
        check_innosite_0014,
        check_innosite_0016,
        check_innosite_0017,
        # CHK_0018, CHK_0019 はコメントアウトされているため含めません
        check_innosite_0020,
        lambda row, errors: check_deposit_route_totalnet_for_ng(row, totalnet_list, errors), # totalnet_listを渡す
        check_innosite_0022,
        check_innosite_0023,
        check_innosite_0024,
        check_innosite_0025,
        check_innosite_0026,
        check_innosite_0027,
        check_innosite_0028,
        check_innosite_0029,
        check_innosite_0030,
        check_innosite_0031,
        # CHK_0032 はコメントアウトされているため含めません
        lambda row, errors: check_innosite_0033(row, errors, sales_person_dict), # sales_person_dictを渡す
        lambda row, errors: check_innosite_0034(row, errors, sales_master_dict), # sales_master_dictを渡す
        lambda row, errors: check_innosite_0039(row, errors, maintenance_id_sales_representative_map), # maintenance_id_sales_representative_mapを渡す
        lambda row, errors: check_innosite_0040(row, errors, maintenance_id_sale1_map), # maintenance_id_sale1_mapを渡す
    ]

    for index, row in df.iterrows():
        row_errors = [] # 各行のエラーを格納するリスト

        user_id = str(row.get("stdiinnoid")) # エラーメッセージに使用するユーザーID
        maintenance_id = str(row.get("stdid_i", "")) # 保守整理番号を取得（要望に基づく）

        # 進捗更新
        if progress_callback and (index % 10 == 0 or index == total_ids - 1):
            progress_callback(f"INNOSITE: {user_id} をチェック中 ({index+1}/{total_ids})")

        # 各チェック関数を実行
        for check_func in check_functions:
            try:
                check_func(row, row_errors)
            except KeyError as e:
                _add_error_message(row_errors, user_id, f"COLUMN_MISSING_ERROR_{check_func.__name__}: {e.args[0]}", maintenance_id)
            except Exception as e:
                _add_error_message(row_errors, user_id, f"UNEXPECTED_ERROR_{check_func.__name__}: {e}", maintenance_id)

        # 保守整理番号を追加
        for error in row_errors:
            if "保守整理番号" not in error or not error["保守整理番号"]:
                error["保守整理番号"] = maintenance_id

        # その行で検出された全てのエラーをメインのリストに追加
        all_errors.extend(row_errors)

    return pd.DataFrame(all_errors, columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"])

# Excelに出力
def save_to_excel(errors_df):
    if errors_df is not None:
        errors_df.to_excel("innosite_validation_results.xlsx", index=False)
        print("チェック結果を innosite_validation_results.xlsx に保存しました。")
    else:
        print("エラーなし。Excel ファイルは作成されません。")

# トータルネットリストを読み込む
def load_totalnet_list_from_csv(file_path=None):
    if not file_path or not os.path.exists(file_path):
        # messagebox.showerror("エラー", f"トータルネット登録ファイルが見つからないか、パスが無効です: {file_path}")
        return pd.DataFrame(columns=["顧客番号"]) # 空のDataFrameを返す

    encodings = ['cp932', 'shift_jis', 'utf-8', 'utf-8-sig']
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, engine='python', on_bad_lines='skip')
            # 必須カラムのチェック
            if "顧客番号" in df.columns:
                return df[["顧客番号"]] # DataFrameとして返す
            else:
                messagebox.showerror("ファイル読み込みエラー", f"トータルネット登録ファイル '{file_path}' に '顧客番号' カラムが見つかりません。")
                return pd.DataFrame(columns=["顧客番号"])
        except UnicodeDecodeError:
            continue # 次のエンコーディングを試す
        except Exception as e:
            messagebox.showerror("ファイル読み込みエラー", f"トータルネット登録ファイルの読み込み中にエラーが発生しました: {e}")
            return pd.DataFrame(columns=["顧客番号"])
    messagebox.showerror("ファイル読み込みエラー", f"トータルネット登録ファイル '{file_path}' を適切なエンコーディングで読み込めませんでした。")
    return pd.DataFrame(columns=["顧客番号"])

# トータルネットファイルを選択する
def get_totalnet_file_path():
    root = tk.Tk()
    root.withdraw()  # ウィンドウを非表示にする
    file_path = filedialog.askopenfilename(title="トータルネット登録ファイルを選択してください", filetypes=[("CSV Files", "*.csv")])
    return file_path

# CHK_0021 stdNsyu(入金経路)が121の場合にトータルネットに登録がなければNG
def check_deposit_route_totalnet_for_ng(row: dict, keywords: list, error_messages: list):
    if row["stdiNsyu"] == 121:
        if row["stdid_i"] not in keywords:
            error_messages.append({
                    "シリーズ": "INNOSITE",
                    "ユーザID": row["stdiinnoid"],
                    "チェックID": "INNOSITE_CHK_0021"
                })

# main_checker_app.py から呼び出されるエントリポイント
def run_innosite_check(progress_callback=None, aux_paths=None):
    try:
        errors = []
        if progress_callback:
            progress_callback("DEKISPART: 補助ファイルを読み込み中...")

        # 補助ファイルの読み込み
        totalnet_df = load_totalnet_list_from_csv(aux_paths.get("totalnet_list_path"))

        sales_person_list = load_sales_person_list_from_csv(aux_paths.get("sales_person_list_path"))

        customers_list = load_customers_list_from_csv(aux_paths.get("customers_list_path"))

        # 補助ファイルの読み込み結果をチェック
        # individual_names, unnecessary_dealer_list, sales_person_list, customers_list はリストなので `not list_name` でチェック
        # totalnet_df は DataFrame なので `totalnet_df.empty` でチェック
        if totalnet_df.empty:
            errors.append({"シリーズ": "INNOSITE", "ユーザID": "N/A", "エラー内容": "トータルネット登録ファイルが見つからないか、内容が空です。"})
        if not sales_person_list:
            errors.append({"シリーズ": "INNOSITE", "ユーザID": "N/A", "エラー内容": "担当者マスタファイルが見つからないか、内容が空です。"})
        if not customers_list:
            errors.append({"シリーズ": "INNOSITE", "ユーザID": "N/A", "エラー内容": "得意先マスタファイルが見つからないか、内容が空です。"})

        # 必須補助ファイルがない場合、ここで処理を中断してエラーを返す
        if errors:
            return pd.DataFrame(errors, columns=["シリーズ", "ユーザID", "保守整理番号", "エラー内容"])

        if progress_callback:
            progress_callback("INNOSITE: 基幹データを取得中...")

        df = fetch_data()

        if df.empty:
            errors.append({"シリーズ": "INNOSITE", "ユーザID": "N/A", "保守整理番号": "", "エラー内容": "基幹データが取得できませんでした。"})
            return pd.DataFrame(errors, columns=["シリーズ", "ユーザID", "保守整理番号", "エラー内容"])

        if progress_callback:
            progress_callback("INNOSITE: データチェックを実行中...")

        # validate_data関数に、読み込んだ補助リストを渡す
        validation_results_df = validate_data(df, progress_callback,
                                             totalnet_df, 
                                             sales_person_list)

        if validation_results_df.empty:
            return pd.DataFrame(columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"])
        else:
            validation_results_df["シリーズ"] = "INNSITE"
            return validation_results_df[["シリーズ", "ユーザID", "保守整理番号", "チェックID"]] # 順序を保証

    except Exception as e:
        # エラー発生時もDataFrameを返すことで、メインアプリでの処理を継続しやすくする
        # traceback を使用して詳細なエラー情報をログに記録
        error_detail = traceback.format_exc()
        messagebox.showerror("INNOSITE エラー", f"INNOSITEチェック中に予期せぬエラーが発生しました。\n詳細はログを確認してください。\nエラー: {e}")
        print(f"INNOSITE エラー詳細:\n{error_detail}")
        return pd.DataFrame([{
            "シリーズ": "INNOSITE",
            "ユーザID": "N/A",
            "保守整理番号": "",
            "エラー内容": f"処理中にエラーが発生しました: {e}"
        }], columns=["シリーズ", "ユーザID", "保守整理番号", "エラー内容"])

# メイン処理
def main():
    data = fetch_data()
    errors_df = validate_data(data)
    save_to_excel(errors_df)

if __name__ == "__main__":
    main()
