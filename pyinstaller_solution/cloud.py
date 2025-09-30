import pyodbc
import pymysql
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import re
import os
import traceback # Import traceback for detailed error logging
import configparser


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

# グローバル変数として定義
contract_fields = [
    'DB_ContractInactive', 'SB_ContractInactive', 'FN_ContractInactive', 
    'SBT_ContractInactive', 'DBP_ContractInactive', 'SBR_ContractInactive', 
    'KC_ContractInactive', 'DQC_ContractInactive', 'KSSCAN_ContractInactive', 
    'PMC_ContractInactive', 'CQC_ContractInactive', 'WLC_ContractInactive', 
    'KTD_ContractInactive'
]

contract_end_fields = {
    'DB_ContractInactive': 'DB_ContractEnd',
    'SB_ContractInactive': 'SB_ContractEnd',
    'FN_ContractInactive': 'FN_ContractEnd',
    'SBT_ContractInactive': 'SBT_ContractEnd',
    'DBP_ContractInactive': 'DBP_ContractEnd',
    'SBR_ContractInactive': 'SBR_ContractEnd',
    'KC_ContractInactive': 'KC_ContractEnd',
    'DQC_ContractInactive': 'DQC_ContractEnd',
    'KSSCAN_ContractInactive': 'KSSCAN_ContractEnd',
    'PMC_ContractInactive': 'PMC_ContractEnd',
    'CQC_ContractInactive': 'CQC_ContractEnd',
    'WLC_ContractInactive': 'WLC_ContractEnd',
    'KTD_ContractInactive': 'KTD_ContractEnd'
}

contract_start_fields = {
    'DB_ContractInactive': 'DB_ContractStart',
    'SB_ContractInactive': 'SB_ContractStart',
    'FN_ContractInactive': 'FN_ContractStart',
    'SBT_ContractInactive': 'SBT_ContractStart',
    'DBP_ContractInactive': 'DBP_ContractStart',
    'SBR_ContractInactive': 'SBR_ContractStart',
    'KC_ContractInactive': 'KC_ContractStart',
    'DQC_ContractInactive': 'DQC_ContractStart',
    'KSSCAN_ContractInactive': 'KSSCAN_ContractStart',
    'PMC_ContractInactive': 'PMC_ContractStart',
    'CQC_ContractInactive': 'CQC_ContractStart',
    'WLC_ContractInactive': 'WLC_ContractStart',
    'KTD_ContractInactive': 'KTD_ContractStart'
}

# DBからデータを取得
def fetch_data():
    config = configparser.ConfigParser()
    config.read('config.ini')
    db_config = config['KSCLOUDDB']

    conn_str = _build_sqlserver_conn_str(db_config)
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM t_kscmain ORDER BY ID ASC")  # 任意のクエリ
    columns = [column[0] for column in cursor.description]  # カラム名を取得
    data = cursor.fetchall()
    conn.close()

    # データが1列の場合、各行をリストに変換
    data = [list(row) for row in data]  # 必要に応じて形状を修正

    # DataFrameに変換
    df = pd.DataFrame(data, columns=columns)
    # データフレームのカラムを確認

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

# ショップDBデータを取得
def get_shop_db_data():
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
    cursor.execute("SELECT * FROM t_stdmain_h")
    
    # カラム名を取得
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    conn.close()

    # DataFrameに変換
    df = pd.DataFrame(data, columns=columns)

    return df

# データチェック関数
def validate_data(df, progress_callback):
    errors = []  # 🔹 エラーリストを初期化
    total_ids = len(df)

    # 不要販売店リストは削除されました（要望#005対応）

    # 対象外営業リストの取得
    excluded_sales_list = fetch_excluded_sales_data()["salCode"].tolist()

    # 販売店マスタの取得
    shop_db_df = get_shop_db_data() # まずDataFrameとして取得
    # DataFrameを辞書のリストに変換
    shop_db_list = shop_db_df.to_dict(orient="records")
    shop_db_dict = {
        item["maiCode"]: {
            "maiCloudUpdateLimit": item["maiCloudUpdateLimit"],
        }
        for item in shop_db_list
    }

    for index, row in df.iterrows():
        error_messages = []
        current_id = row.get("ManagementCode") # 適切なIDカラム名に置き換える
        maintenance_id = row.get("HoshuId", "")  # 保守整理番号を取得（要望に基づく）
        # 進捗更新
        if progress_callback and (index % 10 == 0 or index == total_ids - 1): # 10件ごとに更新、または最後
            progress_callback(f"CLOUD: {current_id} をチェック中 ({index+1}/{total_ids})")

        # CHK_0001: CloudStoreCode(販店1マスタ)のバリデーション
        if pd.notna(row["CloudStoreCode"]) and str(row["CloudStoreCode"]).strip() != "":
            if not (str(row["CloudStoreCode"]).isdigit() and len(str(row["CloudStoreCode"])) == 6) and \
            not (str(row["CloudStoreCode"]).startswith("kshh") and len(str(row["CloudStoreCode"])) == 4) and \
            not str(row["CloudStoreCode"]).startswith("A"):
                error_messages.append({
                    "シリーズ": "CLOUD",
                    "ユーザID": row["ManagementCode"],
                    "保守整理番号": maintenance_id,  # 保守整理番号を追加
                    "チェックID": "CLOUD_CHK_0001"
                })

        # CHK_0002:CloudStoreCodeが"ksALL"を含んでいる場合はNG
        if "ksALL" in str(row["CloudStoreCode"]):
            error_messages.append({
                "シリーズ": "CLOUD",
                "ユーザID": row["ManagementCode"],
                "保守整理番号": maintenance_id,  # 保守整理番号を追加
                "チェックID": "CLOUD_CHK_0002"
            })

        # CHK_0003: CloudStoreCodeが004359(リコー)の場合、CloudStoreCode2が空白だとNG
        if row.get("CloudStoreCode") == "004359" and not str(row.get("CloudStoreCode2", "")).strip():
            error_messages.append({
                "シリーズ": "CLOUD",
                "ユーザID": row["ManagementCode"],
                "保守整理番号": maintenance_id,  # 保守整理番号を追加
                "チェックID": "CLOUD_CHK_0003"
            })

        # CHK_0004: CloudStoreCodeが000286(建築資料)の場合、CloudStoreCode2が空白だとNG
        if row["CloudStoreCode"] == "000286" and not row["CloudStoreCode2"]:
            error_messages.append({
                "シリーズ": "CLOUD",
                "ユーザID": row["ManagementCode"],
                "保守整理番号": maintenance_id,  # 保守整理番号を追加
                "チェックID": "CLOUD_CHK_0004"
            })

        # CHK_0005: CloudStoreCodeが001275(キヤノン(新潟のみ）)の場合、CloudStoreCode2が空白だとNG
        if row["CloudStoreCode"] == "001275" and not row["CloudStoreCode2"]:
            error_messages.append({
                "シリーズ": "CLOUD",
                "ユーザID": row["ManagementCode"],
                "保守整理番号": maintenance_id,  # 保守整理番号を追加
                "チェックID": "CLOUD_CHK_0005"
            })

        # CHK_0006: CloudStoreName, CloudStoreName2, KsNaviStoreName, KsNaviStoreName2, KSARStoreName, KSARStoreName2に▲、×、■を含む場合NG
        invalid_characters = ["▲", "×", "■"]
        fields_to_check = ["CloudStoreName", "CloudStoreName2", "KsNaviStoreName", "KsNaviStoreName2", "KSARStoreName", "KSARStoreName2"]

        for field in fields_to_check:
            if any(char in (row.get(field) or "") for char in invalid_characters):
                error_messages.append({
                "シリーズ": "CLOUD",
                "ユーザID": row["ManagementCode"],
                "保守整理番号": maintenance_id,  # 保守整理番号を追加
                "チェックID": "CLOUD_CHK_0006"
            })

        # CHK_0007:更新案内送る新進(1)でCloudStoreCode　が　更新案内不要リストに存在する場合NG
            # CLOUDシリーズ
            check_0007(
                row, shop_db_dict, error_messages,
                "SendUpdateGuidanceState", "PaymentType", "ManagementCode",
                "CloudStoreCode", "CLOUD_CHK_0007"
            )
            # 快測ナビシリーズ
            check_0007(
                row, shop_db_dict, error_messages,
                "KsNaviSendUpdateGuidanceState", "KsNaviPaymentType", "ManagementCode", # 例: ユーザーIDのキーも変わる可能性
                "KsNaviStoreCode", "CLOUD_CHK_0007" # CHK_IDもシリーズごとに変わる可能性
            )
            # 工事実績DBクラウドシリーズ
            check_0007(
                row, shop_db_dict, error_messages,
                "KDCSendUpdateGuidanceState", "KDCPaymentType", "ManagementCode",
                "KDCStoreCode", "CLOUD_CHK_0007"
            )
            # 快測ARシリーズ
            check_0007(
                row, shop_db_dict, error_messages,
                "KSARSendUpdateGuidanceState", "KSARPaymentType", "ManagementCode",
                "KSARStoreCode", "CLOUD_CHK_0007"
            )   

        # CHK_0008: SendUpdateGuidanceStateが1以外の場合、NotesForUpdate、NotesForETCに特別発送、更新案内の記載がない場合NG
            # CLOUDシリーズ
            check_0008(
                row, shop_db_dict, error_messages,
                "SendUpdateGuidanceState", "PaymentType", "ManagementCode",
                "CloudStoreCode", "CLOUD_CHK_0008"
            )
            # 快測ナビシリーズ
            check_0008(
                row, shop_db_dict, error_messages,
                "KsNaviSendUpdateGuidanceState", "KsNaviPaymentType", "ManagementCode", # 例: ユーザーIDのキーも変わる可能性
                "KsNaviStoreCode", "CLOUD_CHK_0008" # CHK_IDもシリーズごとに変わる可能性
            )
            # 工事実績DBクラウドシリーズ
            check_0008(
                row, shop_db_dict, error_messages,
                "KDCSendUpdateGuidanceState", "KDCPaymentType", "ManagementCode",
                "KDCStoreCode", "CLOUD_CHK_0008"
            )
            # 快測ARシリーズ
            check_0008(
                row, shop_db_dict, error_messages,
                "KSARSendUpdateGuidanceState", "KSARPaymentType", "ManagementCode",
                "KSARStoreCode", "CLOUD_CHK_0008"
            )

        # CHK_0009:工事実績DBクラウド

        # CHK_0010 備考(NotesForRTC)に補助金の記載がある場合に日付が過去になっているとNG
        check_subsidy_date(row, error_messages)

        # CHK_0011: データバンク 退会(DB_ContractInactive)がTrueで処理中（DB_UpdateInprogress）がtrueの場合NG
        check_inactive_and_inprogress(row, "DB_ContractInactive", "DB_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: サイトボックスで複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "SB_ContractInactive", "SB_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: フィールドネットで複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "FN_ContractInactive", "FN_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: サイトボックストンネルで複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "SBT_ContractInactive", "SBT_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: 写管屋クラウドで複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "DBP_ContractInactive", "DBP_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: 配筋検査で複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "SBR_ContractInactive", "SBR_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: KENTEM-CONNECTで複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "KC_ContractInactive", "KC_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: 出来形管理クラウドで複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "DQC_ContractInactive", "DQC_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: 快測Scanで複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "KSSCAN_ContractInactive", "KSSCAN_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: 日報管理クラウドで複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "PMC_ContractInactive", "PMC_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: 品質管理クラウドで複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "CQC_ContractInactive", "CQC_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: 施工体制クラウドで複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "WLC_ContractInactive", "WLC_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011: KENTEM-ToDoで複数年の場合に記載がない場合はNG
        check_inactive_and_inprogress(row, "KTD_ContractInactive", "KTD_UpdateInprogress", error_messages, "CLOUD_CHK_0011")
        # CHK_0011:快測AR
        # CHK_0011:工事実績DBクラウド

        # CHK_0012: 加入中で担当営業が売上あがらない営業担当になっている場合NG
        check_series_and_sales_rep(row, excluded_sales_list, error_messages, "CLOUD_CHK_0012")

        # CHK_0013: 加入中で満了日が過去になっている場合NG
        check_active_and_expired(row, error_messages, "CLOUD_CHK_0013")

        # CHK_0014: 退会中で満了日が未来になっている場合NG
        check_inactive_and_not_expired(row, error_messages, "CLOUD_CHK_0014")

        # CHK_0015: 加入中で加入日が過去になっている場合はNG

        # CHK_0016: 退会中で加入日が未来の日付になっている場合NG
        check_inactive_and_future_start(row, error_messages, "CLOUD_CHK_0016")

        # CHK_0017: 加入中＝更新月　空白
        # CHK_0018: 加入中＝加入年数　空白

        # CHK_0019 加入中で満了日が空白になっている場合NG
        check_active_and_empty_expiration(row, error_messages, "CLOUD_CHK_0019")

        # CHK_0020 加入中で開始日が空白になっている場合NG
        check_active_and_empty_start(row, error_messages, "CLOUD_CHK_0020")

        # CHK_0021 備考が空白でないものをチェック
        if row['NotesForUpdate'] or row['NotesForETC']:
            error_messages.append({
                "シリーズ": "CLOUD",
                "ユーザID": row["ManagementCode"],
                "保守整理番号": maintenance_id,  # 保守整理番号を追加
                "チェックID": "CLOUD_CHK_0021"
            })

        # CHK_0022 減らして更新のキーワードが残っている場合NG
        check_notes_for_keywords(row, error_messages, "CLOUD_CHK_0022")

        #CHK_0023 データバンクの契約期間内に収まっていない場合はNG
        check_contract_period_within_databank(row, error_messages, "CLOUD_CHK_0023")
    
        # 保守整理番号を追加
        for error in error_messages:
            if "保守整理番号" not in error or not error["保守整理番号"]:
                error["保守整理番号"] = maintenance_id
        
        # 各行のエラーをメインの errors リストに追加
        errors.extend(error_messages) 

    # エラーがあれば DataFrame として返す、なければ None を返す
    return pd.DataFrame(errors, columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"])

# Excelに出力
def save_to_excel(errors_df):
    if errors_df is not None:
        errors_df.to_excel("cloud_validation_results.xlsx", index=False)
        print("チェック結果を cloud_validation_results.xlsx に保存しました。")
    else:
        print("エラーなし。Excel ファイルは作成されません。")

# 不要販売店リストを読み込む関数は削除されました（要望#005対応）
# 不要販売店リストファイル選択関数は削除されました（要望#005対応）

# CHK_0007 更新案内が1(送る新進)の場合stdDsale1(販店1マスタ)が更新案内不要販売店リストに存在する場合NG
def check_0007(
    row: dict,
    shop_db_dict: dict,
    error_messages: list,
    guidance_state_key: str,
    payment_type_key: str,
    user_id_key: str,
    main_sales_key: str, # stdSale1 に相当するキー
    check_id: str
):
    """
    CLOUD_CHK_0007: 契約アクティブかつ指定されたNotesForUpdateの条件と
    maiCloudUpdateLimit, PaymentType, SendUpdateGuidanceState の組み合わせでNG
    """
    # 前提条件チェック（共通部分）
    is_any_active = is_any_contract_active(row)
    is_renewal_needed_biko1 = not contains_exclusion_keyword(row.get("NotesForUpdate"))
    is_renewal_needed_biko2 = not contains_exclusion_keyword(row.get("NotesForETC"))

    # 前提条件をまとめてチェック
    if not (is_any_active and is_renewal_needed_biko1 and is_renewal_needed_biko2):
        return # 条件を満たさない場合は以降のチェックをスキップ

    # 販売店コードの存在チェック
    if row.get(main_sales_key) not in shop_db_dict:
        return

    # NotesForUpdate の内容を事前に取得し、正規化
    notes_for_update_text = str(row.get("NotesForUpdate", "")).lower().replace(' ', '').replace('　', '')

    # -- NGパターンの定義 --
    # パターンA: NotesForUpdateに「更新案内不要」の文字列を含まない
    is_notes_for_update_not_contains_renewal = not contains_specific_keyword(notes_for_update_text, ["更新案内不要"])
    
    # パターンAのNG組み合わせ (maiCloudUpdateLimit, PaymentType, SendUpdateGuidanceState)
    ng_combinations_A = {
        (2, 122, 1), (2, 122, 2),
        (2, 211, 1), (2, 211, 2),
        (3, 122, 1), (3, 122, 2),
        (3, 211, 1), (3, 211, 2),
        (4, 122, 1), (4, 122, 2),
        (4, 211, 1), (4, 211, 2),
        (5, 122, 1), (5, 122, 2),
        (5, 211, 0) 
    }

    # パターンB: NotesForUpdateに「NP不可」または「ＮＰ不可」の文字列を含む (パターン⑯〜㉑)
    is_notes_for_update_contains_np_fuka = contains_specific_keyword(notes_for_update_text, ["np不可", "ｎｐ不可"])

    # パターンBのNG組み合わせ (maiCloudUpdateLimit, PaymentType, SendUpdateGuidanceState)
    ng_combinations_B = {
        (2, 211, 1), (2, 211, 2),
        (3, 122, 1), (3, 122, 2),
        (3, 211, 1), (3, 211, 2)
    }

    # パターンC: NotesForUpdateに「NP不可」または「ＮＰ不可」の文字列を含まない (パターン㉒〜㊱)
    # これはパターンAとNotesForUpdateの条件が異なるだけで、組み合わせ自体は同じものも含まれるが、
    # 別の条件セットとして定義する。
    is_notes_for_update_not_contains_np_fuka = not contains_specific_keyword(notes_for_update_text, ["np不可", "ｎｐ不可"])

    # パターンCのNG組み合わせ (maiCloudUpdateLimit, PaymentType, SendUpdateGuidanceState)
    ng_combinations_C = {
        (2, 122, 1), (2, 122, 2),
        (2, 211, 1), (2, 211, 2),
        (3, 122, 1), (3, 122, 2),
        (3, 211, 1), (3, 211, 2),
        (4, 122, 1), (4, 122, 2),
        (4, 211, 1), (4, 211, 2),
        (5, 122, 1), (5, 122, 2),
        (5, 211, 0) # ㊱のみ SendUpdateGuidanceState=0
    }

    # 現在の行の該当する値を取得
    store_flags = shop_db_dict[row.get(main_sales_key)]
    current_maicloud_update_limit = store_flags.get('maiCloudUpdateLimit')
    current_payment_type = row.get(payment_type_key)
    current_send_update_guidance_state = row.get(guidance_state_key)

    # 全てのNGパターンをまとめてチェック
    is_ng = False

    # 現在の組み合わせ (タプル)
    current_combination = (
        current_maicloud_update_limit,
        current_payment_type,
        current_send_update_guidance_state
    )

    if is_notes_for_update_not_contains_renewal and current_combination in ng_combinations_A:
        is_ng = True
    elif is_notes_for_update_contains_np_fuka and current_combination in ng_combinations_B:
        is_ng = True
    elif is_notes_for_update_not_contains_np_fuka and current_combination in ng_combinations_C:
        is_ng = True
    
    # NG条件が満たされた場合にエラーメッセージを追加
    if is_ng:
        error_messages.append({
            "シリーズ": "CLOUD", # 固定値と仮定
            "ユーザID": row.get(user_id_key),
            "保守整理番号": row.get("HoshuId", ""),  # 保守整理番号を追加
            "チェックID": check_id
        })

# CHK_0008 更新案内が1(送る新進)の場合stdDsale1(販店1マスタ)が更新案内不要販売店リストに存在する場合NG
# CHK_0008 更新案内が1(送る新進)の場合stdDsale1(販店1マスタ)が更新案内不要販売店リストに存在する場合NG
def check_0008(
    row: dict,
    shop_db_dict: dict, # sales_master_dict に相当
    error_messages: list,
    guidance_state_key: str, # 例えば 'stdSendUpdateGuidanceState'
    payment_type_key: str,   # 例えば 'stdPaymentType'
    user_id_key: str,        # 例えば 'stdUserID'
    main_sales_key: str,     # 今回のチェックでは未使用だが、関数の引数として残す
    check_id: str
):
    """
    DEKISPART_CHK_0008: 契約アクティブかつ指定されたNotesForUpdateの条件と
    maiCloudUpdateLimit, PaymentType, SendUpdateGuidanceState の組み合わせでNG
    """

    # -- 共通条件のチェック --
    # ***_ContractInactive=FALSE に相当
    is_contract_active = is_any_contract_active(row)
    
    if not is_contract_active:
        return # 共通条件を満たさない場合はスキップ

    # 販売店コードの存在チェック
    if row.get(main_sales_key) not in shop_db_dict:
        return

    # NotesForUpdate の内容を事前に取得し、正規化
    notes_for_update_text = str(row.get("NotesForUpdate", "")).lower().replace(' ', '').replace('　', '')

    # -- NotesForUpdate の条件判定 --
    # NotesForUpdateに「更新案内不要」の文字列を含むか
    contains_renewal_guidance_exclusion = contains_specific_keyword(notes_for_update_text, ["更新案内不要"])
    # NotesForUpdateに「NP不可」または「ＮＰ不可」の文字列を含むか
    contains_np_fuka = contains_specific_keyword(notes_for_update_text, ["np不可", "ｎｐ不可"])

    # -- NGパターンの定義 --

    # グループA: NotesForUpdateに「更新案内不要」の文字列を含む (パターン①〜⑳)
    # maiCloudUpdateLimit, PaymentType, SendUpdateGuidanceState の組み合わせ
    ng_combinations_group_A = {
        (1, 122, 1), (1, 122, 2), (1, 211, 1), (1, 211, 2),
        (2, 122, 1), (2, 122, 2), (2, 211, 1), (2, 211, 2),
        (3, 122, 1), (3, 122, 2), (3, 211, 1), (3, 211, 2),
        (4, 122, 1), (4, 122, 2), (4, 211, 1), (4, 211, 2),
        (5, 122, 1), (5, 122, 2), (5, 211, 1), (5, 211, 2)
    }

    # グループB: NotesForUpdateに「NP不可」または「ＮＰ不可」の文字列を含む (パターン㉑〜㉘)
    # maiCloudUpdateLimit, PaymentType, SendUpdateGuidanceState の組み合わせ
    ng_combinations_group_B = {
        (1, 122, 1), (1, 122, 2),
        (2, 122, 1), (2, 122, 2),
        (4, 122, 1), (4, 122, 2), # maiCloudUpdateLimit=3 は含まれない
        (5, 122, 1), (5, 122, 2)
    }

    # 現在の行の該当する値を取得
    store_flags = shop_db_dict[row.get(main_sales_key)]
    current_maicloud_update_limit = store_flags.get('maiCloudUpdateLimit')
    current_payment_type = row.get(payment_type_key)
    current_send_update_guidance_state = row.get(guidance_state_key)

    # 現在の組み合わせ (タプル)
    current_combination = (
        current_maicloud_update_limit,
        current_payment_type,
        current_send_update_guidance_state
    )

    is_ng = False

    # 各グループの条件とNG組み合わせをチェック
    if contains_renewal_guidance_exclusion and current_combination in ng_combinations_group_A:
        is_ng = True
    elif contains_np_fuka and current_combination in ng_combinations_group_B:
        is_ng = True
    
    # NG条件が満たされた場合にエラーメッセージを追加
    if is_ng:
        error_messages.append({
            "シリーズ": "CLOUD",
            "ユーザID": row.get(user_id_key),
            "保守整理番号": row.get("HoshuId", ""),  # 保守整理番号を追加
            "チェックID": check_id
        })

# '更新案内不要', 'NP不可', 'ＮＰ不可' のいずれかの文字列が含まれているかをチェックするヘルパー関数
def contains_specific_keyword(text_field, keywords):
    if not text_field:
        return False
    normalized_text = str(text_field).lower().replace(' ', '').replace('　', '')
    for keyword in keywords:
        # keywordsは既に小文字、半角に正規化されていると仮定
        if keyword in normalized_text:
            return True
    return False

# '更新案内不要', 'NP不可', 'ＮＰ不可' , '特別発送' のいずれかの文字列が含まれているかをチェックするヘルパー関数
def contains_exclusion_keyword(text_field):
    if not text_field:
        return False
    # 大文字小文字、全角半角を考慮せず、スペースも無視して比較するために正規化する
    normalized_text = text_field.lower().replace(' ', '').replace('　', '')
    
    exclusion_keywords = ["更新案内不要", "NP不可", "ＮＰ不可","特別発送"] # 全て小文字、半角に統一
    
    for keyword in exclusion_keywords:
        if keyword in normalized_text:
            return True
    return False

# いずれかの契約がアクティブかどうかをチェックする関数
def is_any_contract_active(row):
    return any(not row[field] for field in contract_fields)

# 複数年チェック
def check_subsidy_date(row, error_messages):
    if "補助金" in (row.get("NotesForRTC") or ""):
        # 日付のパターンを正規表現で検索
        date_pattern = re.compile(r"\d{4}/\d{1,2}|\d{4}/\d{1,2}/\d{1,2}")
        dates = date_pattern.findall(row["NotesForRTC"])
        for date_str in dates:
            try:
                if len(date_str.split('/')) == 2:
                    date_obj = datetime.strptime(date_str, "%Y/%m")
                else:
                    date_obj = datetime.strptime(date_str, "%Y/%m/%d")
                if date_obj.date() < datetime.now().date():
                    error_messages.append({
                "シリーズ": "CLOUD",
                "ユーザID": row["ManagementCode"],
                "保守整理番号": maintenance_id,  # 保守整理番号を追加
                "チェックID": "CLOUD_CHK_0010"
            })
                    break
            except ValueError:
                continue

# CHK_0011 退会で処理中の場合はNG
def check_inactive_and_inprogress(row, inactive_field, inprogress_field, error_messages, chk_code):
    if row[inactive_field] and row[inprogress_field]:
        error_messages.append({
            "シリーズ": "CLOUD",
            "ユーザID": row["ManagementCode"],
            "保守整理番号": row.get("HoshuId", ""),  # 保守整理番号を追加
            "チェックID": chk_code
        
        })

def check_series_and_sales_rep(row, excluded_sales_list, error_messages, chk_code):
    # いずれかの契約がアクティブかどうかをチェック
    is_any_active = is_any_contract_active(row)
    
    # 担当営業コードが対象外営業リストに含まれているかをチェック
    if is_any_active and row['SalesRepresentativeCode'] in excluded_sales_list:
        error_messages.append({
            "シリーズ": "CLOUD",
            "ユーザID": row["ManagementCode"],
            "保守整理番号": row.get("HoshuId", ""),  # 保守整理番号を追加
            "チェックID": chk_code
        
        })

# いずれかの契約がアクティブかどうかをチェックする関数
def is_any_contract_active(row):
    return any(not row[field] for field in contract_fields)

# 加入中の場合に満了日が過去になっていないかをチェックする関数
def check_active_and_expired(row, error_messages, chk_code):
    # アクティブな契約とその満了日を取得
    active_contracts = get_active_contracts_and_expiration_dates(row)
    
    # 満了日が過去の日付かどうかをチェック
    expired_contracts = [inactive_field for inactive_field, end_date in active_contracts if end_date < datetime.now()]
    
    if expired_contracts:
        error_messages.append({
            "シリーズ": "CLOUD",
            "ユーザID": row["ManagementCode"],
            "保守整理番号": row.get("HoshuId", ""),  # 保守整理番号を追加
            "チェックID": chk_code
        
        })


# 加入中のシリーズを取得する関数
def get_active_contracts_and_expiration_dates(row):
    active_contracts = []
    for inactive_field, end_field in contract_end_fields.items():
        if not row[inactive_field]:
            active_contracts.append((inactive_field, row[end_field]))
    return active_contracts

# 退会中で満了日が未来になっていないかをチェックする関数
def check_inactive_and_not_expired(row, error_messages, chk_code):
    # 退会中の契約とその満了日を取得
    inactive_contracts = [(inactive_field, row[end_field]) for inactive_field, end_field in contract_end_fields.items() if row[inactive_field]]

    # 満了日が未来の日付かどうかをチェック
    future_expired_contracts = [inactive_field for inactive_field, end_date in inactive_contracts if end_date > datetime.now()]
    
    if future_expired_contracts:
        error_messages.append({
            "シリーズ": "CLOUD",
            "ユーザID": row["ManagementCode"],
            "保守整理番号": row.get("HoshuId", ""),  # 保守整理番号を追加
            "チェックID": chk_code
        
        })

# 退会中で加入日が未来になっていないかをチェックする関数
def check_inactive_and_future_start(row, error_messages, chk_code):
    # 退会中の契約とその加入日を取得
    inactive_contracts = [(inactive_field, row[start_field]) for inactive_field, start_field in contract_start_fields.items() if row[inactive_field]]
    
    # 加入日が未来の日付かどうかをチェック
    future_start_contracts = [inactive_field for inactive_field, start_date in inactive_contracts if start_date > datetime.now()]
    
    if future_start_contracts:
        error_messages.append({
            "シリーズ": "CLOUD",
            "ユーザID": row["ManagementCode"],
            "保守整理番号": row.get("HoshuId", ""),  # 保守整理番号を追加
            "チェックID": chk_code
        
        })

# 加入中で満了日が空白でないかチェックする関数
def check_active_and_empty_expiration(row, error_messages, chk_code):
    # アクティブな契約とその満了日を取得
    active_contracts = [(inactive_field, row[end_field]) for inactive_field, end_field in contract_end_fields.items() if not row[inactive_field]]
    
    # 満了日の値が空白かどうかをチェック
    empty_expiration_contracts = [inactive_field for inactive_field, end_date in active_contracts if not end_date]
    
    if empty_expiration_contracts:
        error_messages.append({
            "シリーズ": "CLOUD",
            "ユーザID": row["ManagementCode"],
            "保守整理番号": row.get("HoshuId", ""),  # 保守整理番号を追加
            "チェックID": chk_code
        
        })

# 加入中で開始日が空白でないかチェックする関数
def check_active_and_empty_start(row, error_messages, chk_code):
    # アクティブな契約とその開始日を取得
    active_contracts = [(inactive_field, row[start_field]) for inactive_field, start_field in contract_start_fields.items() if not row[inactive_field]]
    
    # 開始日の値が空白かどうかをチェック
    empty_start_contracts = [inactive_field for inactive_field, start_date in active_contracts if not start_date]
    
    if empty_start_contracts:
        error_messages.append({
            "シリーズ": "CLOUD",
            "ユーザID": row["ManagementCode"],
            "保守整理番号": row.get("HoshuId", ""),  # 保守整理番号を追加
            "チェックID": chk_code
        
        })

# 減らして更新のキーワードがあるかチェックする関数
def check_notes_for_keywords(row, error_messages, chk_code):
    # 各シリーズのフィールドリスト
    notes_fields = [
        'DB_NotesForMultipleYears', 'SB_NotesForMultipleYears', 'FN_NotesForMultipleYears', 
        'SBT_NotesForMultipleYears', 'DBP_NotesForMultipleYears', 'SBR_NotesForMultipleYears', 
        'KC_NotesForMultipleYears', 'DQC_NotesForMultipleYears', 'KSSCAN_NotesForMultipleYears', 
        'PMC_NotesForMultipleYears', 'CQC_NotesForMultipleYears', 'WLC_NotesForMultipleYears', 
        'KTD_NotesForMultipleYears'
    ]
    
    # キーワード
    keyword = '減らして更新'
    
    # 各フィールドをチェック
    for field in notes_fields:
        if isinstance(row[field], str) and keyword in row[field]:
            error_messages.append({
            "シリーズ": "CLOUD",
            "ユーザID": row["ManagementCode"],
            "保守整理番号": row.get("HoshuId", ""),  # 保守整理番号を追加
            "チェックID": chk_code
            
        })

# データバンクの契約期間内に他のシリーズが収まっているかをチェックする関数
def check_contract_period_within_databank(row, error_messages, chk_code):
    # データバンクの契約期間を取得
    db_start = row.get('DB_ContractStart')
    db_end = row.get('DB_ContractEnd')
    
    # データバンクの契約がない場合はスキップ
    if not db_start or not db_end:
        return
    
    # 他のシリーズの契約期間をチェック
    for series, inactive_field in contract_start_fields.items():
        if series != 'DB_ContractInactive' and not row[inactive_field]:
            start_field = contract_start_fields[series]
            end_field = contract_end_fields[series]
            series_start = row.get(start_field)
            series_end = row.get(end_field)
            
            if series_start and series_end:
                if not (db_start <= series_start <= db_end and db_start <= series_end <= db_end):
                    error_messages.append({
            "シリーズ": "CLOUD",
            "ユーザID": row["ManagementCode"],
            "保守整理番号": row.get("HoshuId", ""),  # 保守整理番号を追加
            "チェックID": chk_code
                    
        })

# main_checker_app.py から呼び出されるエントリポイント
def run_cloud_check(progress_callback=None, aux_paths=None):
    try:
        errors = []
        if progress_callback:
            progress_callback("CLOUD: 補助ファイルを読み込み中...")

        # 補助ファイルの読み込み
        # 不要販売店リストは削除されました（要望#005対応）

        # 補助ファイルの読み込み結果をチェック
        # 不要販売店リストのチェックは削除されました（要望#005対応）
        # totalnet_df は DataFrame なので `totalnet_df.empty` でチェック
        # 不要販売店リストのチェックは削除されました（要望#005対応）

        # 必須補助ファイルがない場合、ここで処理を中断してエラーを返す
        if errors:
            return pd.DataFrame(errors, columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"])

        if progress_callback:
            progress_callback("CLOUD: 基幹データを取得中...")

        df = fetch_data()

        if df.empty:
            errors.append({"シリーズ": "CLOUD", "ユーザID": "N/A", "保守整理番号": "", "チェックID": "基幹データが取得できませんでした。"})
            return pd.DataFrame(errors, columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"])

        if progress_callback:
            progress_callback("CLOUD: データチェックを実行中...")

        # validate_data関数に、読み込んだ補助リストを渡す
        validation_results_df = validate_data(df, progress_callback)

        if validation_results_df.empty:
            return pd.DataFrame(columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"])
        else:
            validation_results_df["シリーズ"] = "CLOUD"
            return validation_results_df[["シリーズ", "ユーザID", "保守整理番号", "チェックID"]] # 順序を保証

    except Exception as e:
        # エラー発生時もDataFrameを返すことで、メインアプリでの処理を継続しやすくする
        # traceback を使用して詳細なエラー情報をログに記録
        error_detail = traceback.format_exc()
        messagebox.showerror("CLOUD エラー", f"CLOUDチェック中に予期せぬエラーが発生しました。\n詳細はログを確認してください。\nエラー: {e}")
        print(f"CLOUD エラー詳細:\n{error_detail}")
        return pd.DataFrame([{
            "シリーズ": "CLOUD",
            "ユーザID": "N/A",
            "チェックID": f"処理中にエラーが発生しました: {e}"
        }], columns=["シリーズ", "ユーザID", "チェックID"])

# メイン処理
def main():
    data = fetch_data()
    errors_df = validate_data(data)
    save_to_excel(errors_df)

if __name__ == "__main__":
    main()
