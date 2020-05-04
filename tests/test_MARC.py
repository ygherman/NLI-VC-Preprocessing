from unittest import TestCase, main

import pandas as pd


class Test(TestCase):
    def test_create_MARC_921_933(self):
        test_df = pd.DataFrame(
            {
                "תאריך הרישום": {
                    "997007810681405171": "2020-01-26 15:56",
                    "997007810681305171": "2019-11-25 13:06",
                    "997007810681205171": "2019-11-25 13:41",
                    "997007810681105171": "2019-11-25 16:15",
                    "997007810681005171": "2019-11-25 13:06",
                    "997007810680905171": "2019-11-21 8:59",
                    "997007810680805171": "2019-11-25 15:09",
                    "997007810680705171": "2019-11-25 17:52",
                    "997007810680605171": "2019-11-25 17:53",
                    "997007810680505171": "2019-11-25 17:53",
                    "997007810680405171": "2019-12-18 16:20",
                    "997007810680305171": "2019-12-18 16:24",
                    "997007810680205171": "2019-12-18 16:24",
                    "997007810680105171": "2019-12-18 16:25",
                },
                "שם הרושם": {
                    "997007810681405171": "יובל עציוני;צליל ניב",
                    "997007810681305171": "יובל עציוני",
                    "997007810681205171": "יובל עציוני",
                    "997007810681105171": "יובל עציוני",
                    "997007810681005171": "יובל עציוני",
                    "997007810680905171": "יובל עציוני",
                    "997007810680805171": "יובל עציוני",
                    "997007810680705171": "יובל עציוני",
                    "997007810680605171": "יובל עציוני",
                    "997007810680505171": "יובל עציוני",
                    "997007810680405171": "יובל עציוני",
                    "997007810680305171": "יובל עציוני",
                    "997007810680205171": "יובל עציוני",
                    "997007810680105171": "יובל עציוני",
                },
            }
        )


    def test_more_than_one_value_in_cell(self):
        from io import StringIO
        from VC_collections.marc import more_than_one_value_in_cell

        expected_str = """
col_name
אין מגבלות פרטיות;פרטיות-הסכמים וחוזה
פרטיות-הסכמים וחוזים
פרטיות-נתונים אישיים
פרטיות-צנעת הפרט
פרטיות-מידע רפואי
פרטיות-אחר"""

        data = pd.read_csv(StringIO(expected_str))
        print(data)
        print("columns: ", data.columns)
        result = more_than_one_value_in_cell(data, "col_name")
        self.assertEqual(result, True)

    def test_check_date_values_in_row(self):
        from VC_collections.marc import extract_years_from_text

        self.assertEquals(extract_years_from_text("1930/1990"), ["1930", "1990"])
        self.assertEquals(extract_years_from_text("[בערך 1940-2018]"), ["1940", "2018"])

    def test_update_008_from_260(self):
        from VC_collections.marc import update_008_from_260
        countries_correct = 'גרמניה;הולנד'
        countries_false = 'ברלין, גרמניה'
        self.assertEqual(update_008_from_260(countries_correct), (["$$agw", "$$ane"], 'gw#'))


if __name__ == "__main__":
    main()
