import pyodbc
import pymysql
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import traceback
import logging

# ログ設定
# 実行ファイルと同じディレクトリにログを出力する例
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'application.log')
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO, # INFO以上のレベルのログを出力
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# DBからデータを取得
def fetch_data():
    conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=kssql-sv1\\kssql;DATABASE=DEKISPART_MNT;UID=si-dbuser;PWD=6QEACDw3;TrustServerCertificate=yes"
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
    conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=kssql-sv1\\kssql;DATABASE=DEKISPART_MNT;UID=si-dbuser;PWD=6QEACDw3;TrustServerCertificate=yes"
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

def _add_error_message(error_messages, user_id, check_id, maintenance_id=None):
    """共通のエラーメッセージを追加するヘルパー関数（保守整理番号を含む）"""
    error_messages.append({
        "シリーズ": "DEKISPART",
        "ユーザID": user_id,
        "保守整理番号": maintenance_id if maintenance_id else "",  # 保守整理番号を追加
        "チェックID": check_id
    })

def get_mysql_connection():
    """
    MySQL（イノサイト）への接続を取得する関数
    innosite.pyのfetch_data関数を参考に実装
    """
    return pymysql.connect(
        host="ks-db",
        database="ksmain2",
        user="root",
        password="",
        charset='sjis',
    )

def get_sqlserver_connection():
    """
    SQL Server（デキスパート）への接続を取得する関数
    他のチェック関数でも使用可能
    """
    conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=kssql-sv1\\kssql;DATABASE=DEKISPART_MNT;UID=si-dbuser;PWD=6QEACDw3;TrustServerCertificate=yes"
    return pyodbc.connect(conn_str)

# --- 各チェックロジックをカプセル化した関数群 ---
# 各関数は、対象の行 (Pandas Series) とエラーリストを受け取り、
# エラーがあればエラーリストに追加します。

def check_0001(row, errors_list):
    """
    DEKISPART_CHK_0001: stdItmSが"LAN" かつ stdUserIDが "012" で始まる
    """
    std_user_id = str(row["stdUserID"])
    if (row["stdItmS"] == "ＬＡＮ" and not std_user_id.startswith("012")) or \
       (std_user_id.startswith("012") and row["stdItmS"] != "ＬＡＮ"):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0001", row.get("stdID", ""))

def check_0002(row, errors_list):
    """
    DEKISPART_CHK_0002: stdItmSが"単体" かつ stdUserIDが "8001" で始まる
    """
    std_user_id = str(row["stdUserID"])
    if (row["stdItmS"] == "単体" and not std_user_id.startswith("8001")) or \
       (std_user_id.startswith("8001") and row["stdItmS"] != "単体"):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0002", row.get("stdID", ""))

def check_0003(row, errors_list):
    """
    DEKISPART_CHK_0003: stdItmSが"レンタル" かつ stdUserIDが "629" で始まる
    """
    std_user_id = str(row["stdUserID"])
    if (row["stdItmS"] == "レンタル" and not std_user_id.startswith("629")) or \
       (std_user_id.startswith("629") and row["stdItmS"] != "レンタル"):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0003", row.get("stdID", ""))

def check_0004(row, errors_list):
    """
    DEKISPART_CHK_0004: stdItmSが"その他" かつ stdUserIDが "0000" で始まるまたは空白
    """
    if row["stdKaiyaku"] == False: # このチェックの前提条件として追加
        std_user_id_stripped = str(row["stdUserID"]).strip()
        std_itm_s_stripped = str(row["stdItmS"]).strip()

        # stdItmSが「その他」の場合にstdUserIDが空白でない -> NG
        if std_itm_s_stripped == "その他" and std_user_id_stripped != "":
            _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0004", row.get("stdID", ""))
        # stdItmSが空白の場合にstdUserIDが0000始まりでない -> NG
        elif std_itm_s_stripped == "" and not std_user_id_stripped.startswith("0000"):
            _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0004", row.get("stdID", ""))

def check_0005(row, errors_list):
    """
    DEKISPART_CHK_0005: stdUserIDの先頭8桁が半角であること
    """
    user_id = str(row["stdUserID"])
    if len(user_id) >= 8 and not user_id[:8].isalnum():
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0005", row.get("stdID", ""))

def check_0006(row, errors_list):
    """
    DEKISPART_CHK_0006: stdUserIDに全角カッコや全角ハイフンが含まれていないこと
    """
    if row["stdUserID"] and any(char in str(row["stdUserID"]) for char in ["（", "）", "－"]):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0006", row.get("stdID", ""))

def check_0007(row, errors_list):
    """
    DEKISPART_CHK_0007: stdUserIDの桁数が半角1～7桁であり、かつ"9", "13", "15"ではないこと
    """
    if row["stdUserID"] and len(row["stdUserID"]) >= 1 and len(row["stdUserID"]) <= 7 and row["stdUserID"].isdigit():
        if row["stdUserID"] not in ["9", "13", "15"]:
            _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0007", row.get("stdID", ""))

def check_0008(row, errors_list, user_id_list):
    """
    DEKISPART_CHK_0008: stdUserIDが重複していないこと
    """
    if not user_id_list:
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0008", row.get("stdID", ""))
        return
    
    # stdUserIDが重複しているかチェック
    if user_id_list.count(row["stdUserID"]) >= 2:
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0008", row.get("stdID", ""))

def check_0009(row, errors_list):
    """
    DEKISPART_CHK_0009: stdUserIDとstdSuppIDの最初の8桁が一致すること
    """
    if row["stdSuppID"] and str(row["stdUserID"])[:8] != str(row["stdSuppID"])[:8]:
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0009", row.get("stdID", ""))

def check_0010(row, errors_list, individual_list):
    """
    DEKISPART_CHK_0010: stdFlg4がTRUEかつstdNameに特定の文字が含まれている場合NG
    """
    if row["stdFlg4"] == True and row["stdName"]:
        for keyword in individual_list:
            if keyword in row["stdName"]:
                _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0010", row.get("stdID", ""))

def check_0011(row, errors_list):
    """
    DEKISPART_CHK_0011: stdFlg4がTRUE(敬称が様)かつstdTan1(担当者)が空白であること
    """
    if row["stdFlg4"] == True and (row["stdTan1"] is not None and str(row["stdTan1"]).strip() != ""):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0011", row.get("stdID", ""))

def check_0012(row, errors_list):
    """
    DEKISPART_CHK_0012: stdFlg4がFALSEかつstdTan1が空白でないこと
    """
    if row["stdFlg4"] == False and str(row["stdTan1"]).strip() == "":
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0012", row.get("stdID", ""))

def check_0013(row, errors_list):
    """
    DEKISPART_CHK_0013: stdNamCode(商魂コード)は半角6桁かつ数字もしくは数字以外ではアルファベット半角Bから始まる
    """
    std_nam_code = str(row["stdNamCode"])
    is_digit = std_nam_code.isdigit()

    if len(std_nam_code) != 6:
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0013", row.get("stdID", ""))
    elif not is_digit and not std_nam_code.startswith("B"):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0013", row.get("stdID", ""))

def check_0014(row, errors_list):
    """
    DEKISPART_CHK_0014: stdNamCode(商魂コード)が空白ではないこと
    """
    if str(row["stdNamCode"]).strip() == "":
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0014", row.get("stdID", ""))

def check_0015(row, errors_list):
    """
    DEKISPART_CHK_0015: stdSale1(販売店コード1)は半角数字6桁もしくは4桁の場合kshhもしくはAで始まる
    """
    std_sale1 = str(row["stdSale1"]).strip()
    if pd.notna(row["stdSale1"]) and std_sale1 != "":
        if not (
            (std_sale1.isdigit() and len(std_sale1) == 6) or
            (std_sale1.startswith("kshh") and len(std_sale1) == 4) or
            std_sale1.startswith("A")
        ):
            _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0015", row.get("stdID", ""))

def check_0016(row, errors_list):
    """
    DEKISPART_CHK_0016: stdSale1(販売店コード1)が"ksALL"を含んでいないこと
    """
    if "ksALL" in str(row["stdSale1"]):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0016", row.get("stdID", ""))

def check_0017(row, errors_list):
    """
    DEKISPART_CHK_0017: stdSale1(販売店コード1)が空白でないこと
    """
    if str(row["stdSale1"]).strip() == "":
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0017", row.get("stdID", ""))

def check_0018(row, errors_list):
    """
    DEKISPART_CHK_0018: stdSaleNam1(販売店名1)が空白でないこと
    """
    if str(row["stdSaleNam1"]).strip() == "":
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0018", row.get("stdID", ""))

def check_0019(row, errors_list):
    """
    DEKISPART_CHK_0019: stdSale1(販売店コード1)が004359かつstdSale2(販売店コード2)は00rで始まる
    """
    if str(row["stdSale1"]) == "004359" and not str(row["stdSale2"]).startswith("00r"):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0019", row.get("stdID", ""))

def check_0020(row, errors_list):
    """
    DEKISPART_CHK_0020: stdSale1(販売店コード1)が000286の場合、stdSale2(販売店コード2)がkeで始まる
    """
    if str(row["stdSale1"]) == "000286" and not str(row["stdSale2"]).startswith("ke"):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0020", row.get("stdID", ""))

def check_0021(row, errors_list):
    """
    DEKISPART_CHK_0021: stdSale1(販売店コード1)が001275かつstdAdd(住所)が新潟県で始まる場合、stdSale2(販売店コード2)がcanonである
    """
    if str(row["stdSale1"]) == "001275" and str(row["stdAdd"]).startswith("新潟県") and str(row["stdSale2"]).lower() != "canon":
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0021", row.get("stdID", ""))

# 以降のCHK_0022 から CHK_0026 は同じパターンなので、汎用化も可能です。
# 例: check_sales1_nsyu_211(row, errors_list, sale_code, check_id)
def _check_sale1_nsyu_211(row, errors_list, sale_code, check_id):
    if str(row["stdSale1"]) == sale_code and str(row["stdNsyu"]) != "211":
        _add_error_message(errors_list, row["stdUserID"], check_id, row.get("stdID", ""))

def check_0022(row, errors_list):
    """DEKISPART_CHK_0022: stdSale1が"000332"の場合、stdNsyuが"211"であること"""
    _check_sale1_nsyu_211(row, errors_list, "000332", "DEKISPART_CHK_0022")

def check_0023(row, errors_list):
    """DEKISPART_CHK_0023: stdSale1が"A30777"の場合、stdNsyuが"211"であること"""
    _check_sale1_nsyu_211(row, errors_list, "A30777", "DEKISPART_CHK_0023")

def check_0024(row, errors_list):
    """DEKISPART_CHK_0024: stdSale1が"000583"の場合、stdNsyuが"211"であること"""
    _check_sale1_nsyu_211(row, errors_list, "000583", "DEKISPART_CHK_0024")

def check_0025(row, errors_list):
    """DEKISPART_CHK_0025: stdSale1が"000659"の場合、stdNsyuが"211"であること"""
    _check_sale1_nsyu_211(row, errors_list, "000659", "DEKISPART_CHK_0025")

def check_0026(row, errors_list):
    """DEKISPART_CHK_0026: stdSale1が"000759"の場合、stdNsyuが"211"であること"""
    _check_sale1_nsyu_211(row, errors_list, "000759", "DEKISPART_CHK_0026")

def check_0027(row, errors_list):
    """
    DEKISPART_CHK_0027: stdKaiyakuがFALSEかつstdSaleNam1に不正な記号を含む場合NG
    """
    # チェック対象の先頭文字リスト
    forbidden_leading_symbols = ["：", "×", "▲", "★", "■"]
    #得意先マスタリスト取得する
    customers_list = load_customers_list_from_csv()
    # customers_list を得意先コードで検索しやすいように辞書に変換しておく
    customers_dict = {
        str(customer["得意先コード"]): customer["得意先名１"]
        for customer in customers_list
        if "得意先コード" in customer and "得意先名１" in customer
    }

    customer_code = str(row["stdSaleNam1"]).strip()
    if customer_code in customers_dict:
        customer_name1 = customers_dict[customer_code]
        if row["stdKaiyaku"] is False and (customer_name1 and any(customer_name1.startswith(symbol) for symbol in forbidden_leading_symbols)):
            _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0027", row.get("stdID", ""))

def check_0028(row, errors_list):
    """
    DEKISPART_CHK_0028: stdKaiyakuがFALSE かつ stdAcyear(加入年数)が1以外の場合、
                       stdSbikoが空白ではなく"年"が含まれていない場合NG
    """
    if row["stdSbiko"] and str(row["stdSbiko"]).strip() != "" and "年" not in str(row["stdSbiko"]):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0028", row.get("stdID", ""))

def check_0029(row, errors_list):
    """
    DEKISPART_CHK_0029: stdFlg3がTRUEになっている場合NG
    """
    if row["stdFlg3"] == True:
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0029", row.get("stdID", ""))

def check_0030(row, errors_list):
    """
    DEKISPART_CHK_0030: stdKaiyakuがTRUEかつstdbiko4に"特別計算"が含まれ、
                       契約満了日から2か月以上経過している場合NG
    """
    today = datetime.today()
    if (
        row["stdKaiyaku"] == True
        and "特別計算" in str(row["stdbiko4"])
        and pd.notna(row["stdReyear1"])
    ):
        try:
            reyear_date = row["stdReyear1"] if isinstance(row["stdReyear1"], pd.Timestamp) else datetime.strptime(str(row["stdReyear1"]), "%Y-%m-%d")
            if today >= reyear_date + relativedelta(months=2):
                _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0030", row.get("stdID", ""))
        except ValueError:
            # 日付形式不正の場合もエラーとする
            _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0030", row.get("stdID", "")) # 専用のIDにしても良い

def check_0031(row, errors_list):
    """
    DEKISPART_CHK_0031: stdKaiyakuがTRUEかつstdFlg1がTRUEの場合NG
    """
    if row["stdKaiyaku"] == True and row["stdFlg1"] == True:
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0031", row.get("stdID", ""))

def check_0032(row, errors_list, totalnet_list):
    """
    DEKISPART_CHK_0032: stdNsyu(入金経路)が121　と　トータルネットに登録あるか
    """
    if row["stdNsyu"] == 121:
        if row["stdID"] not in totalnet_list:
                _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0032", row.get("stdID", ""))

def check_0033(row, errors_list, totalnet_list):
    """
    DEKISPART_CHK_0033: stdJifuriDM(自振DM（TRUE＝チェック済))　がTRUE　かつ　トータルネットに登録があるもの
    """
    if row["stdJifuriDM"] is True:
        if row["stdSale1"] in totalnet_list:
            _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0033", row.get("stdID", ""))

def check_0034(row, errors_list, sales_master_list):
    """
    DEKISPART_CHK_0034: 以下のすべての条件を満たす場合NG
    NGパターン:
      - stdKaiyaku = FALSE
      - stdbiko3 に「自振DM不要」の文字列を含まない
      - stdKbiko に「更新案内不要」の文字列を含まない
      - salJifuriDM (sales_master_dict から取得) = TRUE
      - stdNsyu = 122
      - stdJifuriDM (row から取得) = TRUE
    """
    # 各条件を変数に格納 (row.get() を使用し、キーが存在しない場合も安全にアクセス)
    is_not_cancelled = row.get("stdKaiyaku") is False
    
    # stdbiko3 に「自振DM不要」の文字列を含まない
    is_stdbiko3_not_containing_jifuri_dm = not (row.get("stdbiko3") and "自振DM不要" in str(row["stdbiko3"]))

    # stdKbiko に「更新案内不要」の文字列を含まない
    is_std_kbiko_not_containing_renewal = not (row.get("stdKbiko") and "更新案内不要" in str(row["stdKbiko"]))

    # stdNsyu は row から直接取得
    is_std_nsyu_122 = row.get("stdNsyu") == 122
    
    # stdJifuriDM は row から直接取得
    is_std_jifuri_dm_true = row.get("stdJifuriDM") is True

    # salJifuriDM の取得方法を変更: stdSale1 をキーとして sales_master_dict から取得
    is_sal_jifuri_dm_true_from_master = False
    std_sale1 = row.get("stdSale1")
    if std_sale1 in sales_master_list:
        # sales_master_dict の値が辞書形式であることを想定し、.get() でアクセス
        if sales_master_list[std_sale1].get("salJifuriDM") is True:
            is_sal_jifuri_dm_true_from_master = True

    # 全ての条件がANDで結合されるため、全てがTrueの場合にNG
    if (
        is_not_cancelled and
        is_stdbiko3_not_containing_jifuri_dm and
        is_std_kbiko_not_containing_renewal and
        is_sal_jifuri_dm_true_from_master and
        is_std_nsyu_122 and
        is_std_jifuri_dm_true
    ):
        _add_error_message(errors_list, row.get("stdUserID"), "DEKISPART_CHK_0034", row.get("stdID", ""))

def check_0035(row, errors_list, sales_master_dict): # sales_master_dict を引数に追加
    """
    DEKISPART_CHK_0035: 以下の共通条件がすべて満たされる場合NG
    共通条件:
      - stdKaiyaku = FALSE
      - stdbiko3 に「自振DM不要」の文字列を含む
      - stdNsyu = 122
      - stdJifuriDM = TRUE
    NGパターン:
      - stdKbiko および salJifuriDM の値にかかわらず、上記共通条件を満たせばNG
    """

    # -- 共通条件のチェック --
    is_not_cancelled = row.get("stdKaiyaku") is False
    
    # stdbiko3 に「自振DM不要」の文字列を含む
    is_stdbiko3_containing_jifuri_dm = row.get("stdbiko3") and "自振DM不要" in str(row["stdbiko3"])

    is_std_nsyu_122 = row.get("stdNsyu") == 122
    
    is_std_jifuri_dm_true = row.get("stdJifuriDM") is True

    # 共通条件が全てTrueであれば、NGパターンに進む
    common_conditions_met = (
        is_not_cancelled and
        is_stdbiko3_containing_jifuri_dm and
        is_std_nsyu_122 and
        is_std_jifuri_dm_true
    )

    if not common_conditions_met:
        # 共通条件が満たされていない場合は、NGではないのでここで終了
        return

    # -- NGパターンのチェック --
    # 要件のNGパターンを見ると、stdKbiko と salJifuriDM の値によらず
    # 共通条件が満たされていればNGとなるため、ここでは追加の条件判定は不要。

    # stdKbiko に「更新案内不要」の文字列を含むかどうかの判定 (今回はNG判定に直接は使用しない)
    # is_std_kbiko_containing_renewal = row.get("stdKbiko") and "更新案内不要" in str(row["stdKbiko"])

    # salJifuriDM の取得 (今回はNG判定に直接は使用しないが、取得方法は明示)
    # std_sale1 = row.get("stdSale1")
    # is_sal_jifuri_dm_true_from_master = False
    # if std_sale1 in sales_master_dict:
    #     if sales_master_dict[std_sale1].get("salJifuriDM") is True:
    #         is_sal_jifuri_dm_true_from_master = True

    # 共通条件が満たされた時点でNGとなるため、エラーメッセージを追加
    _add_error_message(errors_list, row.get("stdUserID"), "DEKISPART_CHK_0035", row.get("stdID", ""))

def check_0036(row, errors_list, sales_master_dict): # sales_master_dict を引数に追加
    """
    DEKISPART_CHK_0036: 以下の共通条件がすべて満たされる場合NG
    共通条件:
      - stdKaiyaku = FALSE
      - stdbiko3 に「自振DM不要」の文字列を含む
      - stdKbiko に「更新案内不要」の文字列を含む
      - stdNsyu = 122
      - stdJifuriDM = TRUE
    NGパターン:
      - salJifuriDM の値にかかわらず、上記共通条件を満たせばNG
    """

    # -- 共通条件のチェック --
    is_not_cancelled = row.get("stdKaiyaku") is False
    
    # stdbiko3 に「自振DM不要」の文字列を含む
    is_stdbiko3_containing_jifuri_dm = row.get("stdbiko3") and "自振DM不要" in str(row["stdbiko3"])

    # stdKbiko に「更新案内不要」の文字列を含む
    is_std_kbiko_containing_renewal = row.get("stdKbiko") and "更新案内不要" in str(row["stdKbiko"])

    is_std_nsyu_122 = row.get("stdNsyu") == 122
    
    is_std_jifuri_dm_true = row.get("stdJifuriDM") is True

    # 共通条件が全てTrueであれば、NGパターンに進む
    common_conditions_met = (
        is_not_cancelled and
        is_stdbiko3_containing_jifuri_dm and
        is_std_kbiko_containing_renewal and
        is_std_nsyu_122 and
        is_std_jifuri_dm_true
    )

    if not common_conditions_met:
        # 共通条件が満たされていない場合は、NGではないのでここで終了
        return

    # -- NGパターンのチェック --
    # 要件のNGパターンを見ると、salJifuriDM の値によらず
    # 共通条件が満たされていればNGとなるため、ここでは追加の条件判定は不要。
    # ただし、将来的な要件変更に備えて、値の取得は残しておくことも可能。

    # salJifuriDM の取得 (今回はNG判定に直接は使用しないが、取得方法は明示)
    # std_sale1 = row.get("stdSale1")
    # is_sal_jifuri_dm_false_from_master = False
    # is_sal_jifuri_dm_true_from_master = False
    # if std_sale1 in sales_master_dict:
    #     sal_jifuri_dm_value = sales_master_dict[std_sale1].get("salJifuriDM")
    #     if sal_jifuri_dm_value is False:
    #         is_sal_jifuri_dm_false_from_master = True
    #     elif sal_jifuri_dm_value is True:
    #         is_sal_jifuri_dm_true_from_master = True


    # 共通条件が満たされた時点でNGとなるため、エラーメッセージを追加
    _add_error_message(errors_list, row.get("stdUserID"), "DEKISPART_CHK_0036", row.get("stdID", ""))

def check_0037(row, errors_list):
    """
    DEKISPART_CHK_0037: 退会ユーザーでなく、stdNonRenewalがTRUEの場合NG
    """
    if row["stdKaiyaku"] == False and row["stdNonRenewal"] == True:
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0037", row.get("stdID", ""))

def check_0038(row, errors_list, sales_master_dict):
    """
    DEKISPART_CHK_0038: 以下の共通条件が満たされ、かつ、指定された支払い・発送方法のいずれかのパターンに合致する場合NG
    共通条件:
      - stdKaiyaku が FALSE
      - stdKbiko に「更新案内不要」という文字が含まれていない
      - salNotifyRenewal が TRUE
    NGパターン:
      - (stdNsyu=121 かつ stdHassouType=1)
      - (stdNsyu=121 かつ stdHassouType=2)
      - (stdNsyu=122 かつ stdHassouType=1)
      - (stdNsyu=122 かつ stdHassouType=2) 
      - (stdNsyu=211 かつ stdHassouType=1)
      - (stdNsyu=211 かつ stdHassouType=2)
    """
    # 条件をまとめるための変数
    is_not_cancelled = row.get("stdKaiyaku") is False
    # stdKbiko が存在しない場合も「含まれていない」とみなす
    is_kbiko_not_containing_renewal_text = not (row.get("stdKbiko") and "更新案内不要" in row["stdKbiko"])
    # salJifuriDM の取得方法を変更: stdSale1 をキーとして sales_master_dict から取得
    is_sal_notify_renewal_true_from_master = False
    std_sale1 = row.get("stdSale1")
    if std_sale1 in sales_master_dict:
        # sales_master_dict の値が辞書形式であることを想定し、.get() でアクセス
        if sales_master_dict[std_sale1].get("salNotifyRenewal") is True:
            is_sal_notify_renewal_true_from_master = True

    # 全ての共通条件が満たされているか
    common_conditions_met = is_not_cancelled and is_kbiko_not_containing_renewal_text and is_sal_notify_renewal_true_from_master

    if not common_conditions_met:
        # 共通条件が満たされていない場合は、NGではないのでここで終了
        return

    # 支払い・発送方法のパターンチェック
    std_nsyu = row.get("stdNsyu")
    std_hassou_type = row.get("stdHassouType")

    # NGとなる支払い・発送方法の組み合わせを定義
    ng_patterns = [
        (121, 1),
        (121, 2),
        (122, 1),
        (122, 2),
        (211, 1),
        (211, 2)
    ]

    # 現在の行の支払い・発送方法がNGパターンに合致するかチェック
    is_ng_payment_shipping_pattern = (std_nsyu, std_hassou_type) in ng_patterns

    # 共通条件とNGパターンが両方満たされた場合にエラーを追加
    if is_ng_payment_shipping_pattern:
        _add_error_message(errors_list, row.get("stdUserID"), "DEKISPART_CHK_0038", row.get("stdID", ""))

def check_0039(row, errors_list, sales_master_list):
    """
    DEKISPART_CHK_0039: 以下の共通条件とNGパターンが満たされる場合NG
    共通条件:
      - stdKaiyaku が FALSE
      - stdKbiko に「更新案内不要」という文字が含まれている
    NGパターン:
      - salNotifyRenewal の値にかかわらず、
        stdNsyu が (121, 122, 211) のいずれか かつ stdHassouType が (1, 2) のいずれか
    """

    # -- 共通条件のチェック --
    is_not_cancelled = row.get("stdKaiyaku") is False
    # stdKbiko が存在し、かつ「更新案内不要」という文字が含まれているか
    is_kbiko_contains_renewal_text = row.get("stdKbiko") and "更新案内不要" in str(row["stdKbiko"])

    # 共通条件が満たされていない場合は、NGではないのでここで終了
    if not (is_not_cancelled and is_kbiko_contains_renewal_text):
        return

    # -- NGパターンのチェック --
    # is_sal_notify_renewal_false = row.get("salNotifyRenewal") is False
    # is_sal_notify_renewal_true = row.get("salNotifyRenewal") is True
    #is_sal_notify_renewal_true_from_master = False
    #std_sale1 = row.get("stdSale1")
    #if std_sale1 in sales_master_list:
        # sales_master_dict の値が辞書形式であることを想定し、.get() でアクセス
    #    if sales_master_list[std_sale1].get("salNotifyRenewal") is True:
    #        is_sal_notify_renewal_true_from_master = True

    std_nsyu = row.get("stdNsyu")
    std_hassou_type = row.get("stdHassouType")

    # NGとなる stdNsyu と stdHassouType の組み合わせを定義
    # salNotifyRenewal の値に関わらず、以下の組み合わせがNG
    ng_nsyu_types = {121, 122, 211}
    ng_hassou_types = {1, 2}

    # 現在の行の支払い・発送方法がNGパターンに合致するかチェック
    is_ng_payment_shipping_pattern = (
        std_nsyu in ng_nsyu_types and
        std_hassou_type in ng_hassou_types
    )

    # 共通条件とNGパターンが両方満たされた場合にエラーを追加
    if is_ng_payment_shipping_pattern:
        # stdUserID が存在しない場合を考慮し .get() を使用
        _add_error_message(errors_list, row.get("stdUserID"), "DEKISPART_CHK_0039", row.get("stdID", ""))

def check_0040(row, errors_list):
    """
    DEKISPART_CHK_0040: stdKaiyakuがFALSEかつstdTselに×または・が含まれている場合NG
    """
    #担当者マスタリストを取得する
    sales_person_list = load_sales_person_list_from_csv()

    # sales_person_list を担当者コードで検索しやすいように辞書に変換しておく
    # 担当者コードがユニークであることを前提とします
    sales_person_dict = {
        str(person["担当者コード"]): person["担当者名"]
        for person in sales_person_list
        if "担当者コード" in person and "担当者名" in person
    }

    std_tsel_code = str(row["stdTsel"]).strip()
    if std_tsel_code in sales_person_dict:
        person_name = sales_person_dict[std_tsel_code]
        if row["stdKaiyaku"] == False and (person_name.startswith("×") or person_name.startswith("・")):
            _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0040", row.get("stdID", ""))

def check_0041(row, errors_list):
    """
    DEKISPART_CHK_0041: stdKaiyakuがFALSEかつstdTselが空白の場合NG
    """
    if row["stdKaiyaku"] == False and pd.isna(row["stdTsel"]):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0041", row.get("stdID", ""))

def check_0042(row, errors_list):
    """
    DEKISPART_CHK_0042: stdKaiyakuがFALSEかつstdTplaが空白の場合NG
    """
    if row["stdKaiyaku"] == False and pd.isna(row["stdTpla"]):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0042", row.get("stdID", ""))

def check_0043(row, errors_list):
    """
    DEKISPART_CHK_0043: stdKaiyakuがFALSEかつstdTplaに指定の営業所名以外がある場合NG
    担当者マスターから有効な営業所名を取得して検証する
    """
    # 担当者マスタリストを取得する
    sales_person_list = load_sales_person_list_from_csv()
    
    # 部門コードから営業所名のセットを作成
    valid_branches = set()
    for person in sales_person_list:
        if "部門コード" in person and person["部門コード"]:
            valid_branches.add(str(person["部門コード"]))
    
    # 有効な営業所名が取得できなかった場合のフォールバック
    if not valid_branches:
        logging.warning("担当者マスターから営業所名を取得できませんでした。デフォルト値を使用します。")
        valid_branches = {"九州", "仙台", "会社", "北陸", "南九州", "名古屋", "四国", "大手", "広島", "建築", "新潟", "本社", "本社第1", "本社第2", "札幌", "盛岡", "福岡", "関東", "関西"}
    
    if row["stdKaiyaku"] == False and row["stdTpla"] not in valid_branches:
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0043", row.get("stdID", ""))

def check_0044(row, errors_list):
    """
    DEKISPART_CHK_0044: stdKaiyakuがTRUEかつstdReyear1が未来の日付になっている場合NG
    ※ ただし、stdNameに「▲」「×」「■」のいずれかが含まれる場合はチェックをスキップ
    """
    if not any(symbol in str(row["stdName"]) for symbol in ["▲", "×", "■"]):
        if pd.notna(row["stdReyear1"]) and str(row["stdReyear1"]).strip() != "":
            try:
                reyear_date = row["stdReyear1"] if isinstance(row["stdReyear1"], pd.Timestamp) else datetime.strptime(str(row["stdReyear1"]), "%Y-%m-%d")
                if row["stdKaiyaku"] == True and reyear_date > datetime.now():
                    _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0044", row.get("stdID", ""))
            except ValueError:
                _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0044_DATE_PARSE_ERROR", row.get("stdID", ""))

# 以降の空白チェックは同じパターンなので、汎用化も可能です。
def _check_not_blank(row, errors_list, column_name, check_id):
    """指定されたカラムが空白（NaN, None, 空文字列）でないことをチェックする"""
    if row["stdKaiyaku"] == False and pd.isna(row[column_name]): # pd.isnaでNaN, None, empty stringをカバー
        _add_error_message(errors_list, row["stdUserID"], check_id, row.get("stdID", ""))

def check_0045(row, errors_list):
    """DEKISPART_CHK_0045: stdKaiyakuがFALSEかつstdAcdayが空白の場合NG"""
    _check_not_blank(row, errors_list, "stdAcday", "DEKISPART_CHK_0045")

def check_0046(row, errors_list):
    """DEKISPART_CHK_0046: stdKaiyakuがFALSEかつstdRemonが空白の場合NG"""
    _check_not_blank(row, errors_list, "stdRemon", "DEKISPART_CHK_0046")

def check_0047(row, errors_list):
    """DEKISPART_CHK_0047: stdKaiyakuがFALSEかつstdAcyearが空白の場合NG"""
    _check_not_blank(row, errors_list, "stdAcyear", "DEKISPART_CHK_0047")

def check_0048(row, errors_list):
    """DEKISPART_CHK_0048: stdKaiyakuがFALSEかつstdReyear1が空白の場合NG"""
    _check_not_blank(row, errors_list, "stdReyear1", "DEKISPART_CHK_0048")

def check_0049(row, errors_list):
    """DEKISPART_CHK_0049: stdKaiyakuがFALSEかつstdReyear2が空白の場合NG"""
    _check_not_blank(row, errors_list, "stdReyear2", "DEKISPART_CHK_0049")

def check_0050(row, errors_list):
    """DEKISPART_CHK_0050: stdKaiyakuがFALSEかつstdKainsyuが空白の場合NG"""
    _check_not_blank(row, errors_list, "stdKainsyu", "DEKISPART_CHK_0050")

def check_0051(row, errors_list):
    """DEKISPART_CHK_0051: stdKaiyakuがFALSEかつstdNameが空白の場合NG"""
    _check_not_blank(row, errors_list, "stdName", "DEKISPART_CHK_0051")

def check_0052(row, errors_list):
    """DEKISPART_CHK_0052: stdKaiyakuがFALSEかつstdNamefが空白の場合NG"""
    _check_not_blank(row, errors_list, "stdNamef", "DEKISPART_CHK_0052")

def check_0053(row, errors_list):
    """DEKISPART_CHK_0053: stdKaiyakuがFALSEかつstdZipが空白の場合NG"""
    _check_not_blank(row, errors_list, "stdZip", "DEKISPART_CHK_0053")

def check_0054(row, errors_list):
    """DEKISPART_CHK_0054: stdKaiyakuがFALSEかつstdAddが空白の場合NG"""
    _check_not_blank(row, errors_list, "stdAdd", "DEKISPART_CHK_0054")

def check_0055(row, errors_list):
    """DEKISPART_CHK_0055: stdKaiyakuがFALSEかつstdTellが空白の場合NG"""
    _check_not_blank(row, errors_list, "stdTell", "DEKISPART_CHK_0055")

def check_0056(row, errors_list):
    """
    DEKISPART_CHK_0056: stdKaiyakuがFALSEかつ、stdKainsyuがDまたはCDで、stdbiko4に"会員種特別計算"がある場合NG
    """
    if row["stdKaiyaku"] == False and str(row["stdKainsyu"]) in ["D", "CD"] and "会員種特別計算" in str(row["stdbiko4"]):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0056", row.get("stdID", ""))

def check_0057(row, errors_list):
    """
    DEKISPART_CHK_0057: stdNsyu(入金経路)が121でstdHassouType(更新案内不要（0＝不要　1＝送る　2＝別送）)が0の場合NG
    """
    if str(row["stdNsyu"]) == "121" and str(row["stdHassouType"]) == "0":
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0057", row.get("stdID", ""))

def check_0058(row, errors_list):
    """
    DEKISPART_CHK_0058: stdNsyu(入金経路)が121でstdKbiko(備考（更新・一斉）)に”更新案内不要"を含む場合NG
    """
    if str(row["stdNsyu"]) == "121" and "更新案内不要" in str(row["stdKbiko"]):
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0058", row.get("stdID", ""))

def check_0059(row, errors_list, customers_list):
    """
    DEKISPART_CHK_0059: 得意先マスタのD列（担当敬称）とstdFlg4（敬称フラグ）の整合性チェック
    """
    # 得意先コードを取得
    std_sale1 = str(row.get("stdSale1", "")).strip()
    if not std_sale1:
        return
    
    # 得意先マスタから該当する得意先を検索
    customer_info = None
    for customer in customers_list:
        if str(customer.get("得意先コード", "")).strip() == std_sale1:
            customer_info = customer
            break
    
    if not customer_info:
        return  # 得意先マスタに該当データがない場合はスキップ
    
    # D列（担当敬称）を取得
    honorific = str(customer_info.get("担当敬称", "")).strip()
    
    # stdFlg4（敬称フラグ）を取得
    honorific_flag = row.get("stdFlg4", False)
    
    # チェックロジック
    if honorific == "様" and not honorific_flag:
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0059", row.get("stdID", ""))
    elif honorific == "御中" and honorific_flag:
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0059", row.get("stdID", ""))
    elif honorific not in ["様", "御中"] and honorific:  # 空でない場合のみチェック
        _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0059", row.get("stdID", ""))

def check_0060(row, errors_list):
    """
    DEKISPART_CHK_0060: イノサイトデータとの関連チェック
    t_stdidata.stdiinnoidが321から始まり、stdipcodeが1541、かつstdid_i=std_idのデータがある場合、
    関連するT_stdItemにitmCode="1494"が存在しない場合はNG
    """
    try:
        # 現在の行のstdIDを取得
        std_id = row.get("stdID")
        if not std_id:
            return
        
        # Step 1: MySQL（イノサイト）のt_stdidataでデータを検索
        mysql_conn = get_mysql_connection()
        mysql_cursor = mysql_conn.cursor()
        
        mysql_cursor.execute("""
            SELECT COUNT(*) FROM t_stdidata 
            WHERE stdiinnoid LIKE '321%' AND stdipccode = '1541' AND stdid_i = %s
        """, (std_id,))
        
        stdidata_count = mysql_cursor.fetchone()[0]
        mysql_conn.close()
        
        if stdidata_count == 0:
            return  # 該当データがない場合はスキップ
        
        # Step 2: SQL Server（デキスパート）のT_stdItemでデータを検索
        sqlserver_conn = get_sqlserver_connection()
        sqlserver_cursor = sqlserver_conn.cursor()
        
        sqlserver_cursor.execute("""
            SELECT COUNT(*) FROM T_stdItem 
            WHERE itmUser = ? AND itmCode = '1494'
        """, (std_id,))
        
        item_count = sqlserver_cursor.fetchone()[0]
        sqlserver_conn.close()
        
        if item_count == 0:
            _add_error_message(errors_list, row["stdUserID"], "DEKISPART_CHK_0060", row.get("stdID", ""))
        
    except Exception as e:
        logging.error(f"DEKISPART_CHK_0060でエラーが発生しました: {e}")
        # エラーが発生した場合はスキップ（ログに記録）

# データチェック関数
def validate_data(df, progress_callback, individual_list, totalnet_list, sales_person_list, customers_list):
    errors = []  #エラーリストを初期化
    total_ids = len(df)

    # ユーザーIDリストを取得する
    userid_list = get_stdUserID_list(df)

    # 個人名リストを取得する
    individual_list = load_individual_list_from_excel()

    # トータルネットリストを取得する
    totalnet_list = load_totalnet_list_from_csv()

    # 不要販売店リストは削除されました（要望#005対応）

    # 販売店マスタの取得
    sales_master_list = get_sales_master_data() # まずDataFrameとして取得
    # DataFrameを辞書のリストに変換
    sales_master_list = sales_master_list.to_dict(orient="records")
    sales_master_dict = {
        item["salCode"]: {
            "salNotifyRenewal": item["salNotifyRenewal"],
            "salJifuriDM": item["salJifuriDM"],
        }
        for item in sales_master_list
    }

    # 全てのチェック関数をリストにまとめる
    # ここで定義した関数として実装してください。
    check_functions = [
        # 基本的なデータ検証 (引数なし)
        check_0001, check_0002, check_0003, check_0004, check_0005,
        check_0006, check_0007,
        check_0009,
        check_0011, check_0012, check_0013, check_0014, check_0015,
        check_0016, check_0017, check_0018, check_0019, check_0020,
        check_0021, check_0022, check_0023, check_0024, check_0025,
        check_0026, check_0027, check_0028, check_0029, check_0030,
        check_0031, check_0037,
        check_0040, check_0041, check_0042, check_0043,
        check_0044, check_0045, check_0046, check_0047, check_0048,
        check_0049, check_0050, check_0051, check_0052, check_0053,
        check_0054, check_0055, check_0056, check_0057, check_0058,

        # 外部データ (リスト/辞書) を引数に取るチェック
        # 各lambda関数は、rowとerrorsに加えて必要な外部データを渡します。
        lambda row, errors: check_0008(row, errors, userid_list),
        lambda row, errors: check_0010(row, errors, individual_list),
        lambda row, errors: check_0032(row, errors, totalnet_list),
        lambda row, errors: check_0033(row, errors, totalnet_list),
        lambda row, errors: check_0034(row, errors, sales_master_dict),
        lambda row, errors: check_0035(row, errors, sales_master_dict),
        lambda row, errors: check_0036(row, errors, sales_master_dict),
        lambda row, errors: check_0038(row, errors, sales_master_dict),
        lambda row, errors: check_0039(row, errors, sales_master_dict),
        lambda row, errors: check_0059(row, errors, customers_list),
        check_0060,
    ]

    for index, row in df.iterrows():
        current_user_id = row.get("stdUserID")
        maintenance_id = row.get("stdID", "")  # 保守整理番号を取得（要望に基づく）
        row_errors = []

        # 進捗更新
        if progress_callback and (index % 10 == 0 or index == total_ids - 1):
            progress_callback(f"DEKISPART: {current_user_id} をチェック中 ({index+1}/{total_ids})")

        # 各チェック関数を実行
        for check_func in check_functions:
            try:
                check_func(row, row_errors)
            except KeyError as e:
                _add_error_message(row_errors, current_user_id, f"COLUMN_MISSING_ERROR_{check_func.__name__}: {e}", maintenance_id)
            except Exception as e:
                _add_error_message(row_errors, current_user_id, f"UNEXPECTED_ERROR_{check_func.__name__}: {e}", maintenance_id)

        # 保守整理番号を追加
        for error in row_errors:
            if "保守整理番号" not in error or not error["保守整理番号"]:
                error["保守整理番号"] = maintenance_id

        errors.extend(row_errors)

    return pd.DataFrame(errors, columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"])

# Excelに出力
def save_to_excel(errors_df):
    if errors_df is not None and not errors_df.empty:
        errors_df.to_excel("dekispart_validation_results.xlsx", index=False)
        print("チェック結果を dekispart_validation_results.xlsx に保存しました。")
    else:
        print("エラーなし。Excel ファイルは作成されません。")

#ユーザーIDリストを取得する
def get_stdUserID_list(df: pd.DataFrame):
    stdUserID_list = list(set(df['stdUserID'].tolist()))
    return stdUserID_list

# 個人名リストを読み込む
def load_individual_list_from_excel(file_path=None):
    if not file_path or not os.path.exists(file_path):
        # messagebox.showerror("エラー", f"個人名チェックファイルが見つからないか、パスが無効です: {file_path}")
        return [] # 空のリストを返す
    try:
        df = pd.read_excel(file_path)
        if "検索文字" in df.columns:
            keywords = df["検索文字"].dropna().astype(str).tolist()
            return keywords
        else:
            messagebox.showerror("ファイル読み込みエラー", f"個人名チェックファイル '{file_path}' に '検索文字' カラムが見つかりません。")
            return []
    except Exception as e:
        messagebox.showerror("ファイル読み込みエラー", f"個人名チェックファイルの読み込み中にエラーが発生しました: {e}")
        return []

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

# 不要販売店リストを読み込む関数は削除されました（要望#005対応）

# 個人名リストファイルを選択する
def get_individual_list_file_path():
    root = tk.Tk()
    root.withdraw()  # ウィンドウを非表示にする
    file_path = filedialog.askopenfilename(title="個人名チェックファイルを選択してください", filetypes=[("Excel Files", "*.xlsx")])
    return file_path

# 不要販売店リストファイル選択関数は削除されました（要望#005対応）

# トータルネットファイルを選択する
def get_totalnet_file_path():
    root = tk.Tk()
    root.withdraw()  # ウィンドウを非表示にする
    file_path = filedialog.askopenfilename(title="トータルネット登録ファイルを選択してください", filetypes=[("CSV Files", "*.csv")])
    return file_path

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
    required_columns = ["得意先コード", "得意先名１", "使用区分", "担当敬称"]
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

# main_checker_app.py から呼び出されるエントリポイント
def run_dekispart_check(progress_callback=None, aux_paths=None):
    try:
        errors = []
        if progress_callback:
            progress_callback("DEKISPART: 補助ファイルを読み込み中...")

        # 補助ファイルの読み込み
        individual_list_path = aux_paths.get("individual_list_path")
        individual_names = load_individual_list_from_excel(individual_list_path)
        totalnet_df = load_totalnet_list_from_csv(aux_paths.get("totalnet_list_path"))
        # 不要販売店リストは削除されました（要望#005対応）
        sales_person_list = load_sales_person_list_from_csv(aux_paths.get("sales_person_list_path"))
        customers_list = load_customers_list_from_csv(aux_paths.get("customers_list_path"))

        # 補助ファイルの読み込み結果をチェック
        # individual_names, sales_person_list, customers_list はリストなので `not list_name` でチェック
        # totalnet_df は DataFrame なので `totalnet_df.empty` でチェック
        if not individual_names:
            errors.append({"シリーズ": "DEKISPART", "ユーザID": "N/A", "チェックID": "DEKISPART_CHK_0014"})
        if totalnet_df.empty:
            errors.append({"シリーズ": "DEKISPART", "ユーザID": "N/A", "チェックID": "DEKISPART_CHK_0015"})
        # 不要販売店リストのチェックは削除されました（要望#005対応）
        if not sales_person_list:
            errors.append({"シリーズ": "DEKISPART", "ユーザID": "N/A", "チェックID": "DEKISPART_CHK_0017"})
        if not customers_list:
            errors.append({"シリーズ": "DEKISPART", "ユーザID": "N/A", "チェックID": "DEKISPART_CHK_0018"})

        # 必須補助ファイルがない場合、ここで処理を中断してエラーを返す
        if errors:
            return pd.DataFrame(errors, columns=["シリーズ", "ユーザID", "チェックID"])

        if progress_callback:
            progress_callback("DEKISPART: 基幹データを取得中...")

        df = fetch_data()

        if df.empty:
            errors.append({"シリーズ": "DEKISPART", "ユーザID": "N/A", "チェックID": "DEKISPART_CHK_0013"})
            return pd.DataFrame(errors, columns=["シリーズ", "ユーザID", "チェックID"])

        if progress_callback:
            progress_callback("DEKISPART: データチェックを実行中...")

        # validate_data関数に、読み込んだ補助リストを渡す
        validation_results_df = validate_data(df, progress_callback,
                                             individual_names,
                                             totalnet_df, # DataFrameをそのまま渡す
                                             # unnecessary_dealer_list削除（要望#005対応）
                                             sales_person_list, # リストをそのまま渡す
                                             customers_list) # リストをそのまま渡す

        if validation_results_df.empty:
            return pd.DataFrame(columns=["シリーズ", "ユーザID", "チェックID"])
        else:
            validation_results_df["シリーズ"] = "DEKISPART"
            return validation_results_df[["シリーズ", "ユーザID", "保守整理番号", "チェックID"]] # 順序を保証

    except Exception as e:
        # エラー発生時もDataFrameを返すことで、メインアプリでの処理を継続しやすくする
        # traceback を使用して詳細なエラー情報をログに記録
        error_detail = traceback.format_exc()
        messagebox.showerror("DEKISPART エラー", f"DEKISPARTチェック中に予期せぬエラーが発生しました。\n詳細はログを確認してください。\nエラー: {e}")
        print(f"DEKISPART エラー詳細:\n{error_detail}")
        return pd.DataFrame([{
            "シリーズ": "DEKISPART",
            "ユーザID": "N/A",
            "エラー内容": f"処理中にエラーが発生しました: {e}"
        }], columns=["シリーズ", "ユーザID", "エラー内容"])

# メイン処理
def main():
    data = fetch_data()
    errors_df = validate_data(data)
    save_to_excel(errors_df)

if __name__ == "__main__":
    main()