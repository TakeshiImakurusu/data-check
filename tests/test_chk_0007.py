
import unittest
import pandas as pd
import dekispart

class TestChk0007(unittest.TestCase):
    def test_valid_cases(self):
        """
        正常系: 不正な文字が含まれていない場合
        (8桁数字、7桁数字、9桁数字、英字など、不正文字以外は全てOK)
        """
        valid_values = [
            "12345678",   # 8 digits
            "1234567",    # 7 digits
            "123456789",  # 9 digits
            "ABCDEFGH",   # Alphabets
            "1234ABCD",   # Mix
            "13",         # previously invalid specific value
            "9",          # previously invalid specific value
            "15",         # previously invalid specific value
        ]
        
        for val in valid_values:
            with self.subTest(val=val):
                row = {"stdUserID": val, "stdID": "A001"}
                errors = []
                dekispart.check_0007(row, errors)
                self.assertEqual(len(errors), 0, f"Expected no error for value: {val}")

    def test_invalid_cases(self):
        """
        異常系: 不正な文字が含まれている場合
        (半角スペース、全角スペース、改行コード)
        """
        invalid_values = [
            "1234 5678",  # Half-width space
            " ",          # Only space
            "1234　5678", # Full-width space
            "1234\r5678", # CR
            "1234\n5678", # LF
            "1234\r\n5678", # CRLF
            " 12345678",  # Leading space
            "12345678 ",  # Trailing space
        ]
        
        for val in invalid_values:
            with self.subTest(val=val):
                row = {"stdUserID": val, "stdID": "A001"}
                errors = []
                dekispart.check_0007(row, errors)
                self.assertEqual(len(errors), 1, f"Expected error for value: {val!r}")
                self.assertEqual(errors[0]["チェックID"], "DEKISPART_CHK_0007")

    def test_empty_values(self):
        """
        空文字やNoneの場合はチェック対象外（またはエラーにならない）
        """
        empty_values = [
            "",
            None,
            float("nan"),
        ]
        for val in empty_values:
            with self.subTest(val=val):
                row = {"stdUserID": val, "stdID": "A001"}
                errors = []
                dekispart.check_0007(row, errors)
                self.assertEqual(len(errors), 0)

if __name__ == "__main__":
    unittest.main()
