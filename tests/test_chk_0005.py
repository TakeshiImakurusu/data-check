
import unittest
import pandas as pd
from dekispart import check_0005

class TestCheck0005(unittest.TestCase):
    def test_cases(self):
        # テストケース定義
        test_cases = [
            # 入力値, 期待結果(エラーなし=True, エラーあり=False)
            ("12345678", True, "パターンA：半角数字8桁"),
            ("", True, "チェック除外"),
            (None, True, "チェック除外(None)"),
            ("01231246-1", True, "パターンB：先頭8桁数値＋記号"),
            ("01201152(7)", True, "パターンB：先頭8桁数値＋記号"),
            ("01210469関東", True, "パターンB：先頭8桁数値＋全角文字"),
            ("123456789", False, "数値のみで9桁のため（誤入力扱い）"),
            ("1234567", False, "8文字未満のため"),
            ("1234567A", False, "8文字目以内に文字が混入しているため"),
            ("ABCDEFGH", False, "数値以外のみ"),
            ("12345678A", True, "8桁数値＋文字"), 
        ]

        for input_val, expected_valid, note in test_cases:
            with self.subTest(input=input_val, note=note):
                row = {"stdUserID": input_val, "stdID": "TEST001"}
                errors_list = []
                check_0005(row, errors_list)
                
                if expected_valid:
                    self.assertEqual(len(errors_list), 0, f"Expected valid for {input_val} ({note}), but got errors: {errors_list}")
                else:
                    self.assertEqual(len(errors_list), 1, f"Expected invalid for {input_val} ({note}), but got no errors")
                    self.assertEqual(errors_list[0]["チェックID"], "DEKISPART_CHK_0005")

if __name__ == "__main__":
    unittest.main()
