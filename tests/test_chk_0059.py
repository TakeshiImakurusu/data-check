
import unittest
from dekispart import check_0059

class TestChk0059(unittest.TestCase):
    def test_cases(self):
        """
        Verify that using '会社敬称' works correctly.
        """
        # Case 1: Customer '御中' (Company Honorific), User 'False' (御中) -> Should Pass.
        # Currently (Bug): Reads '担当敬称' ('様') -> Fails.
        errors_list_1 = []
        row_1 = {
            "stdUserID": "TEST_USER",
            "stdID": "TEST_ID",
            "stdSale1": "123456",
            "stdFlg4": False # False means 御中
        }
        customers_dict_1 = {
            "123456": {
                "担当敬称": "様",
                "会社敬称": "御中"
            }
        }
        
        check_0059(row_1, errors_list_1, customers_dict_1)
        # We expect 0 errors after fix.
        # Before fix: 1 error.
        
        # Case 2: Customer '様' (Company Honorific), User 'True' (様) -> Should Pass.
        # Currently (Bug): Reads '担当敬称' ('御中') -> Fails.
        errors_list_2 = []
        row_2 = {
            "stdUserID": "TEST_USER",
            "stdID": "TEST_ID",
            "stdSale1": "123456",
            "stdFlg4": True # True means '様'
        }
        customers_dict_2 = {
            "123456": {
                "担当敬称": "御中",
                "会社敬称": "様"
            }
        }
        
        check_0059(row_2, errors_list_2, customers_dict_2)
        # We expect 0 errors after fix.
        # Before fix: 1 error.

        # Case 3: Customer '御中' (Company Honorific), User 'True' (様) -> Should Fail.
        # Currently (Bug): Reads '担当敬称' ('様') -> Puts it as PASS (Incorrect).
        errors_list_3 = []
        row_3 = {
            "stdUserID": "TEST_USER",
            "stdID": "TEST_ID",
            "stdSale1": "123456",
            "stdFlg4": True # True means '様'
        }
        customers_dict_3 = {
            "123456": {
                "担当敬称": "様",
                "会社敬称": "御中"
            }
        }
        check_0059(row_3, errors_list_3, customers_dict_3)
        # We expect 1 error after fix.
        # Before fix: 0 errors.

        # If we assert correct behavior, all checks will fail in the current buggy state.
        self.assertEqual(len(errors_list_1), 0, f"Case 1 Failed: {errors_list_1}")
        self.assertEqual(len(errors_list_2), 0, f"Case 2 Failed: {errors_list_2}")
        self.assertEqual(len(errors_list_3), 1, "Case 3 Failed: Expecting Error but got None")
        if len(errors_list_3) > 0:
            self.assertEqual(errors_list_3[0]["チェックID"], "DEKISPART_CHK_0059")

if __name__ == "__main__":
    unittest.main()
