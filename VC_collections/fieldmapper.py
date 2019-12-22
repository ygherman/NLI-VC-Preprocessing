"""
SYNOPSIS
    TODO helloworld [-h,--help] [-v,--verbose] [--version]

DESCRIPTION
    TODO This describes how to use this script. This docstring
    will be printed by the script if there is an error or
    if the user requests help (-h or --help).
    
PROJECT NAME:
    helper_fuctions

AUTHOR
    Yael Vardina Gherman <Yael.VardinaGherman@nli.org.il>
    Yael Vardina Gherman <gh.gherman@gmail.com>

LICENSE
    This script is in the public domain, free from copyrights or restrictions.

VERSION
    Date: 22/08/2019 15:54
    
    $
"""

field_mapper = {'אוסףפתוח': 'ACCURALS',
                'ביבליוגרפיהומקורותמידע': 'BIBLIOGRAPHY',
                'ברקוד': 'BARCODE',
                'דיגיטציה': 'DIGITIZATION',
                'היסטוריהארכיונית': 'BIOGHIST',
                'היקף': 'EXTENT',
                'היקףהחומר': 'EXTENT',
                'הערות': 'NOTES',
                'הערותגלוילמשתמשקצה': 'NOTES',
                'הערותלאגלוילמשתמש': 'NOTES_HIDDEN',
                'חומריםקשורים': 'RELATED_MATERIALS',
                'טכניקה': 'TECHNIQUE',
                'יוצריהאוסף': 'ADD_CREATOR_PERS',
                'יוצרים': 'COMBINED_CREATORS',
                'יוצריםנוספים': 'ADD_CREATORS',
                'יוצריםנוספיםאיש': 'ADD_CREATOR_PERS',
                'יוצריםנוספיםמוסד': 'ADD_CREATOR_CORPS',
                'יוצרראשיאיש': 'FIRST_CREATOR_PERS',
                'יוצרראשימוסד': 'FIRST_CREATOR_CORP',
                'כותרת': 'UNITITLE',
                'כותרתאנגלית': 'UNITITLE_ENG',
                'למחיקה': 'TO_DELETE',
                'מגבלותלתצוגהבאינטרנט': 'ACCESSRESTRICT',
                'מגבלותפרטיות': 'ACCESSRESTRICT',
                'מדיהפורמט': 'MEDIUM_FORMAT',
                'מדינתהפרסום': 'PUBLICATION_COUNTRY',
                'מדינתהפרסוםהצילום': 'PUBLICATION_COUNTRY',
                'מידות': 'DIMENSIONS',
                'מידענוסף': 'SCOPECONTENT',
                'מידעעלהצטברותהאוסף': 'BIOGHIST',
                'מידעעלהצטברותהחומר': 'BIOGHIST',
                'מידעעלסידורהאוסףשיטתהסידור': 'ARRANGEMENT',
                'מידעעלסידורהחומר': 'ARRANGEMENT',
                'מיכל': 'CONTAINER',
                'מילותמפתחאישיליבה': 'PERSNAME',
                'מילותמפתחיצירותליבה': 'WORKS',
                'מילותמפתחמוסדותליבה': 'CORPNAME',
                'מילותמפתחנושאיליבה': 'SUBJECT',
                'מילותמפתחאישים': 'PERSNAME',
                'מילותמפתחארגונים': 'CORPNAME',
                'מילותמפתחיצירות': 'WORKS',
                'מילותמפתחמוסדות': 'CORPNAME',
                'מילותמפתחמקומות': 'GEOGNAME',
                'מילותמפתחנושאים': 'SUBJECT',
                'מיקוםפיזי': 'PHYSLOC',
                'מסלולדיגיטציה': 'DIGITIZATION',
                'מספרהמיכל': 'CONTAINER',
                'מספרהמיכלבונמצאהתיקפריט': 'CONTAINER',
                'מספרמיכל': 'CONTAINER',
                'מספרקבציםלסריקה': 'EST_FILES_NUM',
                'מספרקבציםמוערך': 'EST_FILES_NUM',
                'מקוםהפרסום': 'PUBLICATION_COUNTRY',
                'נשלחלדיגיטציה': 'DIGITIZATION',
                'סוגאוסף': 'COLLECTION_TYPE',
                'סוגהחומר': 'ARCHIVAL_MATERIAL',
                'סוגחומר': 'ARCHIVAL_MATERIAL',
                'סוגיוצרראשיאיש': 'TYPE_FIRST_CREATOR_PERS',
                'סוגיוצראיש': 'TYPE_FIRST_CREATOR_PERS',
                'סוגיוצרראשימוסד': 'TYPE_FIRST_CREATOR_CORP',
                'סוגיוצרמוסד': 'TYPE_FIRST_CREATOR_CORP',

                'סימול': 'UNITID',
                'סימולאב': 'ROOTID',
                'סימולהאוסף': 'UNITID',
                'סימולמספרמזהה': 'UNITID',
                'סימולמקורי': 'ORIDINAL_ID',
                'סימולפרויקט': 'UNITID',
                'סריקהדוצדדית': 'TWO_SIDE_SCAN',
                'סריקתדוצדדית': 'TWO_SIDE_SCAN',
                'פומבי': 'PUBLIC',
                'קודתיקארכיון': 'ARCHIV_ID',
                'קנהמידה': 'SCALE',
                'רושם': 'CATALOGUER',
                'רמתתיאור': 'LEVEL',
                'שם': 'UNITITLE',
                'שםהאוסף': 'UNITITLE',
                'שםהמקטלג': 'CATALOGUER',
                'שםהרושם': 'CATALOGUER',
                'שםיוצרראשימוסד': 'FIRST_CREATOR_CORP',
                'שםיוצרמוסד': 'FIRST_CREATOR_CORP',
                'שםיוצראיש': 'FIRST_CREATOR_PERS',
                'שםיוצרראשיאיש': 'FIRST_CREATOR_PERS',
                'שפה': 'LANGUAGE',
                'תאריך': 'DATE_NORMAL',
                'תאריךהרישום': 'DATE_CATALOGING',
                'תאריךחופשי': 'DATE',
                'תאריךמנורמל': 'DATE_NORMAL',
                'תאריךמנורמלמאוחר': 'DATE_END',
                'תאריךמנורמלמוקדם': 'DATE_START',
                'תאריךפתיחתרשומה': 'RECORD_CREATE_DATE',
                'תאריךקיטלוג': 'DATE_CATALOGING',
                'תאריךרישום': 'DATE_CATALOGING',

                'תאריךצילוםמנורמלמוקדם': 'PHOTO_DATE_EARLY',
                'תאריךצילוםמנורמלמאוחר': 'PHOTO_DATE_LATE',
                'תאריךתצלוםחפץטקסטמוערמוקדם': 'PHOTO_DATE_EARLY',
                'תאריךתצלוםחפץטקסטמוערמאוחר': 'PHOTO_DATE_LATE',


                'תיאור': 'SCOPECONTENT',
                'תיאורהחומרבפרויקטתרבותחזותיתואמנויותהבמה': 'APPRAISAL',
                'תיאורהטיפולבאוסףבפרויקט': 'APPRAISAL'
                }

field_mapper_back = {
    "ACCURALS": "אוסף פתוח",
    "BIBLIOGRAPHY": "ביבליוגרפיה ומקורות מידע",
    'BARCODE': 'ברקוד',
    'BIOGHIST': 'היסטוריה ארכיונית',
    'EXTENT': 'היקף',
    'NOTES': 'הערות גלוי למשתמש קצה',
    'NOTES_HIDDEN': 'הערות לא גלוי למשתמש',
    'RELATED_MATERIALS': "חומרים קשורים",
    'TECHNIQUE': 'טכניקה',
    'FIRST_CREATOR_PERS': 'יוצר ראשי-איש',
    'FIRST_CREATOR_CORP': 'יוצר ראשי-מוסד',
    'COMBINED_CREATORS': 'יוצרים',
    'ADD_CREATOR_PERS': 'יוצרים נוספים איש',
    'ADD_CREATOR_CORPS': 'יוצרים נוספים מוסד',
    'UNITITLE': 'כותרת',
    'UNITITLE_ENG': 'כותרת אנגלית',
    'TO_DELETE': 'למחיקה',
    'ACCESSRESTRICT': 'מגבלות פרטיות',
    'MEDIUM_FORMAT': 'מדיה+פורמט',
    'PUBLICATION_COUNTRY': 'מדינת הפרסום/הצילום',
    'DIMENSIONS': 'מידות',
    'ARRANGEMENT': 'מידע על סידור החומר',
    'CONTAINER': 'מיכל',
    'PERSNAME': 'מילות מפתח_אישים',
    'WORKS': 'מילות מפתח_יצירות',
    'CORPNAME': 'מילות מפתח_מוסדות',
    'GEOGNAME': 'מילות מפתח_מקומות',
    'SUBJECT': 'מילות מפתח_נושאים',
    'PHYSLOC': 'מיקום פיזי',
    'DIGITIZATION': 'מסלול דיגיטציה',
    'EST_FILES_NUM': 'מספר קבצים מוערך',
    'COLLECTION_TYPE': 'סוג אוסף',
    'ARCHIVAL_MATERIAL': 'סוג חומר',
    'TYPE_FIRST_CREATOR_PERS': 'סוג יוצר ראשי-איש',
    'TYPE_FIRST_CREATOR_CORP': 'סוג יוצר ראשי-מוסד',
    'UNITID': 'סימול',
    'ROOTID': 'סימול אב',
    'ORIDINAL_ID': 'סימול מקורי',
    'TWO_SIDE_SCAN': 'סריקה דו צדדית',
    'PUBLIC': 'פומבי',
    'ARCHIV_ID': 'קוד תיק ארכיון',
    'SCALE': 'קנה מידה',
    'LEVEL': 'רמת תיאור',
    'CATALOGUER': 'שם הרושם',
    'LANGUAGE': 'שפה',
    'DATE': 'תאריך חופשי',
    'DATE_NORMAL': 'תאריך מנורמל',
    'DATE_END': 'תאריך מנורמל מאוחר',
    'DATE_START': 'תאריך מנורמל מוקדם',
    'RECORD_CREATE_DATE': 'תאריך פתיחת רשומה',
    'DATE_CATALOGING': 'תאריך רישום',
    'PHOTO_DATE_LATE': 'תאריך תצלום  חפץ/טקסט מוער מאוחר',
    'PHOTO_DATE_EARLY': 'תאריך תצלום חפץ/טקסט מוער מוקדם',
    'SCOPECONTENT': 'תיאור',
    'APPRAISAL': 'תיאורהטיפולבאוסףבפרויקט'

}

level_mapper = {
    'אוסף': 'Section Record',
    'חטיבה': 'Fonds Record',
    'תתחטיבה': 'Sub-Fonds Record',
    'סדרה': 'Series Record',
    'תתסדרה': 'Sub-Series Record',
    'תת סדרה': 'Sub-Series Record',
    'תיק': 'File Record',
    'פריט': 'Item Record',
    'סידרה': 'Series Record',
    'תתסידרה': 'Sub-Series Record'
}

collection_field_mapper = {
    'סימול האוסף': 'UNITID',
    'סימול מקורי': 'ORIDINAL_ID',
    'רמת תיאור': 'LEVEL',
    'שם האוסף': 'UNITITLE',
    'תאריך חופשי': 'DATE',
    'יוצרי האוסף': 'ADD_CREATOR_PERS',
    'מילות מפתח_אישי ליבה': 'PERSNAME',
    'מילות מפתח_מוסדות ליבה': 'CORPSNAME',
    'מילות מפתח_יצירות ליבה': 'WORKS',
    'מילות מפתח_נושאי ליבה': 'SUBJECT',
    'סוג חומר': 'ARCHIVAL_MATERIAL',
    'היסטוריה ארכיונית': 'BIOGHIST',
    'תיאור הטיפול באוסף בפרויקט': 'APPRAISAL',
    'סוג אוסף': 'COLLECTION_TYPE',
    'היקף': 'EXTENT',
    'אוסף פתוח': 'ACCURALS',
    'ביבליוגרפיה ומקורות מידע': 'BIBLIOGRAPHY',
    'מיקום פיזי': 'PHYSLOC',
    'חומרים קשורים': 'RELATED_MATERIAL',
    'הערות - גלוי למשתמש קצה': 'NOTES',
    'הערות - לא גלוי למשתמש קצה': 'NOTES_HIDDEN',
    'שם הרושם': 'CATALOGUER',
    'תאריך הרישום': 'DATE_CATALOGING'
}

field_types_dict = {
    'date': ['CATALOGUING_DATE', 'DATE_END', 'DATE_NORMAL', 'DATE_START',
             'EARLY_NORMAL_DATE', 'LATE_NORMAL_DATE', 'DATE_CATALOGING'],
    'number': ['BOX', 'CONTAINER'],
    'text': ['BIBLIOGRAPHY', 'BARCODE', 'BIOGHIST', 'EXTENT', 'NOTES',
             'NOTES_HIDDEN', 'RELATED_MATERIALS', 'COMBINED_CREATORS', 'FIRST_CREATOR_PERS', 'FIRST_CREATOR_CORP',
             'UNITITLE', 'UNITITLE_ENG’', 'DIMENSIONS', 'ARRANGEMENT', 'EST_FILES_NUM', 'ORIDINAL_ID', 'ARCHIV_ID',
             'Parent', 'PHYSLOC', 'PROJECT_ID', 'ROOTID', 'SCOPECONTENT', 'STAGE', '', 'UNITID', 'UNITITLE',
             'TO_DELETE', 'DATE', 'APPRAISAL', 'ARCHIV_ID'],
    'value_list': ['CATALOGUER', 'ADD_CREATORS', 'ADD_CREATORS_CORPS', 'ARCHIVAL_MATERIAL', 'COMBINED_CREATORS',
                   'COMBINED_CREATORS_CORPS', 'COMBINED_CREATORS_PERS', 'CORPNAME', 'CREATOR_CORPS', 'CREATOR_PERS',
                   'DIMENSIONS', 'GEOGNAME', 'PUBLICATION_COUNTRY', 'MEDIUM_FORMAT', 'PERSNAME', 'SCALE',
                   'SUBJECT', 'WORKS', 'SIZE', 'TYPE_FIRST_CREATOR_PERS', 'TYPE_FIRST_CREATOR_CORP', 'COLLECTION_TYPE',
                   'PUBLICATION_COUNTRY']}


class FieldMapper:

    def __init__(self):
        self.field_mapper = field_mapper
        self.field_mapper_back = field_mapper_back
        self.level_mapper = level_mapper
        self.collection_field_mapper = collection_field_mapper
