import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd


def _forbidden_connect(*args, **kwargs):  # pragma: no cover - safeguard
    raise RuntimeError("Unexpected DB connection during tests")


sys.modules.setdefault("pymysql", SimpleNamespace(connect=_forbidden_connect))
sys.modules.setdefault("pyodbc", SimpleNamespace(connect=_forbidden_connect))

import dekispart


class DummyCursor:
    def __init__(self, rows):
        self._rows = rows
        self.closed = False
        self.last_query = None

    def execute(self, query):
        self.last_query = query

    def fetchall(self):
        return self._rows

    def close(self):
        self.closed = True


class DummyConnection:
    def __init__(self, rows):
        self.cursor_obj = DummyCursor(rows)
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def close(self):
        self.closed = True


class DekispartTests(unittest.TestCase):
    def test_prepare_chk0060_reference_sets(self):
        mysql_conn = DummyConnection([("A001",), ("B002",), (None,)])
        sql_conn = DummyConnection([("A001",), ("C003",)])

        with patch("dekispart.get_mysql_connection", return_value=mysql_conn), patch(
            "dekispart.get_sqlserver_connection", return_value=sql_conn
        ):
            std_ids = pd.Series(["A001", "B002", "D004"])
            target_ids, item_ids = dekispart.prepare_chk0060_reference_sets(std_ids)

        self.assertEqual(target_ids, {"A001", "B002"})
        self.assertEqual(item_ids, {"A001"})
        self.assertTrue(mysql_conn.closed)
        self.assertTrue(mysql_conn.cursor_obj.closed)
        self.assertTrue(sql_conn.closed)
        self.assertTrue(sql_conn.cursor_obj.closed)

    def test_validate_data_uses_preloaded_resources(self):
        row = {
            "stdID": "A001",
            "stdUserID": "01234567",
            "stdItmS": "ＬＡＮ",
            "stdKaiyaku": False,
            "stdSuppID": "01234567",
            "stdTan1": "担当太郎",
            "stdNamCode": "123456",
            "stdSale1": "123456",
            "stdSaleNam1": "CUST1",
            "stdSale2": "00r1",
            "stdNsyu": 122,
            "stdAdd": "東京都千代田区",
            "stdKbiko": "",
            "stdbiko3": "",
            "stdbiko4": "",
            "stdJifuriDM": False,
            "stdHassouType": "1",
            "stdNonRenewal": False,
            "stdTsel": "SEL1",
            "stdTpla": "TPLA1",
            "stdReyear1": pd.Timestamp("2020-01-01"),
            "stdReyear2": pd.Timestamp("2021-01-01"),
            "stdAcday": 1,
            "stdRemon": 1,
            "stdAcyear": 2020,
            "stdKainsyu": "A",
            "stdName": "株式会社テスト",
            "stdNamef": "テストカブシキガイシャ",
            "stdZip": "1000000",
            "stdTell": "0312345678",
            "stdFlg4": False,
            "stdFlg3": False,
            "stdFlg1": False,
        }

        df = pd.DataFrame([row])

        dekispart.check_0038_sales_master_related = lambda row, errors, sales_master_dict: None

        with patch(
            "dekispart.get_sales_master_data",
            return_value=pd.DataFrame(
                [
                    {
                        "salCode": "123456",
                        "salNotifyRenewal": False,
                        "salJifuriDM": False,
                    }
                ]
            ),
        ), patch("dekispart.prepare_salKName2K_dict", return_value={"mock_code": "TPLA1"}), patch(
            "dekispart.prepare_chk0060_reference_sets", return_value=({"A001"}, set())
        ):
            sales_person_records = [
                {"担当者コード": "SEL1", "担当者名": "×山田", "部門コード": "001"}
            ]

            customers_records = [
                {"得意先コード": "CUST1", "得意先名１": "×不正店", "担当敬称": "御中", "使用区分": ""},
                {"得意先コード": "123456", "得意先名１": "正規店", "担当敬称": "様", "使用区分": ""},
            ]

            result = dekispart.validate_data(
                df,
                progress_callback=None,
                individual_list=[],
                totalnet_records=pd.DataFrame(columns=["顧客番号"]),
                sales_person_records=sales_person_records,
                customers_records=customers_records,
            )

        check_ids = set(result["チェックID"])
        expected = {
            "DEKISPART_CHK_0027",
            "DEKISPART_CHK_0040",
            "DEKISPART_CHK_0059",
            "DEKISPART_CHK_0060",
        }

        self.assertTrue(expected.issubset(check_ids))
        self.assertTrue(all(result["シリーズ"] == "DEKISPART"))
        self.assertEqual(set(result["保守整理番号"]), {"A001"})

    def test_check_0040_ignores_kaiyaku_status(self):
        errors = []
        row = {
            "stdTsel": "SEL1",
            "stdUserID": "01234567",
            "stdID": "A001",
            "stdKaiyaku": True,
        }
        sales_person_dict = {"SEL1": {"担当者名": "・田中"}}

        dekispart.check_0040(row, errors, sales_person_dict)

        self.assertEqual([error["チェックID"] for error in errors], ["DEKISPART_CHK_0040"])

if __name__ == "__main__":
    unittest.main()
