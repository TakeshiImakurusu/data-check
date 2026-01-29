
import unittest
import pandas as pd
from dekispart import check_0008

class TestCheck0008(unittest.TestCase):
    def test_cases(self):
        # テストケース定義
        test_cases = [
            # ID: TC-01
            # stdUserID, duplicate_user_ids(重複IDセット), 期待結果(エラーなし=True), 備考
            ("USER_001", {"USER_001", "USER_002"}, False, "有効な値の重複はNG"),
            
            # ID: TC-02
            # NULL同士は重複とみなさない
            (None, {None, "USER_001"}, True, "NULLは重複リストに含まれていても除外(OK)"),
            (float('nan'), {float('nan'), "USER_001"}, True, "NaNは重複リストに含まれていても除外(OK)"),
            
            # ID: TC-03
            # 空文字同士は重複とみなさない
            ("", {"", "USER_001"}, True, "空文字は重複リストに含まれていても除外(OK)"),
            
            # ID: TC-04 (Not explicit in function args but implicitly tested by having varied inputs)
            # 片方が空欄の場合 -> Function receives one row at a time.
            # If input is unique (not in duplicate set), it's OK.
            ("USER_003", {"USER_001", "USER_002"}, True, "重複リストに含まれていない値はOK"),
        ]

        for input_val, duplicate_set, expected_valid, note in test_cases:
            with self.subTest(input=input_val, note=note):
                row = {"stdUserID": input_val, "stdID": "TEST008"}
                errors_list = []
                
                # Check 0008 takes row, errors_list, and duplicate_user_ids
                check_0008(row, errors_list, duplicate_set)
                
                if expected_valid:
                    self.assertEqual(len(errors_list), 0, f"Expected valid for {input_val} ({note}), but got errors: {errors_list}")
                else:
                    self.assertEqual(len(errors_list), 1, f"Expected invalid for {input_val} ({note}), but got no errors")
                    self.assertEqual(errors_list[0]["チェックID"], "DEKISPART_CHK_0008")

if __name__ == "__main__":
    unittest.main()
