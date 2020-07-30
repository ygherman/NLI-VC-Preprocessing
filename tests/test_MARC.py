from unittest import TestCase, main

import pandas as pd


class Test_MARC(TestCase):
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

        countries_correct = "גרמניה;הולנד"
        countries_false = "ברלין, גרמניה"
        self.assertEqual(
            update_008_from_260(countries_correct), (["$$agw", "$$ane"], "gw#")
        )

    def test_create_marc_999_values_list(self):
        from VC_collections.marc import create_MARC_999_values_list

        list_999_values_test = ["תצלומים", "שמע", "תשריט", "מפת מדידה"]
        self.assertEqual(
            create_MARC_999_values_list(list_999_values_test),
            [
                "$$aAUDIO FILE (AUDIO FILE)",
                "$$aPHOTOGRAPH (PHOTOGRAPH)",
                "$$aMAP (MAP)",
            ],
        )

    def test_create_710_current_owner_val(self):
        from VC_collections.marc import create_710_current_owner_val

        eng = "Goor Archive"
        heb = "ארכיון גור"
        self.assertEqual(
            "$$aארכיון גור$$9heb$$ecurrent owner", create_710_current_owner_val(heb)
        )
        self.assertEqual(
            "$$aGoor Archive$$9eng$$ecurrent owner", create_710_current_owner_val(eng)
        )

    def test_create_marc_655(self):
        from VC_collections.marc import create_MARC_655

        xl = pd.ExcelFile("Resources/ArBe_test_data.xlsx")
        test_df = xl.parse("קטלוג")
        test_655 = test_df["סוג חומר"]

    def test_create_marc_942(self):
        from VC_collections.marc import create_MARC_942

        xl = pd.ExcelFile("Resources/ArHb_test_data.xlsx")
        test_df = xl.parse("קטלוג")
        df = create_MARC_942(test_df, "ArHb")

        self.fail()


if __name__ == "__main__":
    main()
