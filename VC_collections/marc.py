import datetime
import os
import re
import sys
from xml.dom import minidom

import alphabet_detector
import dateutil
from fuzzywuzzy import process

from VC_collections.AuthorityFiles import *
from VC_collections.authorities import is_corp, is_pers, find_name, find_role
from VC_collections.authorities import map_role_to_relator
from VC_collections.columns import drop_col_if_exists, column_exists, remove_duplicate_in_column
from VC_collections.explode import explode_col_to_new_df
from VC_collections.project import get_root_title
from VC_collections.value import clean_text, find_nth, replace_lst_dict

# ROOTID finder
ROOTID_finder = lambda x: x[:find_nth(x, '-', x.count('-'))] if '-' in x else ''

Authority_instance = Authority()


def create_MARC_initial_008(df):
    df['008'] = '######k########xx######################d'
    return df


def create_MARC_091(df):
    """
        converts the ['ברקןד'] field to MARC21 091 encoded field
    :param df: The original Dataframe
    :return: The Dataframe with the new 091 field
    """
    df['ברקוד'] = df['ברקוד'].astype(str).replace('.0', '')
    df['091'] = df['ברקוד'].apply(lambda x: '$$a' + x.rstrip('.0') if x != '' else '')
    df = drop_col_if_exists(df, 'ברקוד')
    return df


def create_MARC_911(df):
    """add prefix '$$a' to the value

    :param df = dataframe

    """
    df['911'] = df['סימול'].apply(lambda x: '$$a' + x)
    while True:
        collection_name_heb = input("Please enter a Collection Name in Hebrew: \n")
        if not collection_name_heb:
            print("Please enter a Collection Name.")
        else:
            break

    while True:
        collection_name_eng = input("Please enter a Collection Name in English: \n")
        if not collection_name_eng:
            print("Please enter a Collection Name.")
        else:
            break
    df['911_1'] = df['911'] + '$$c' + collection_name_heb
    df['093_1'] = df['911_1']
    df['911_2'] = df['911'] + '$$c' + collection_name_eng
    df['093_2'] = df['911_2']

    df = drop_col_if_exists(df, '911')
    df = drop_col_if_exists(df, 'שם האוסף')

    return df


def create_MARC_535(df):
    """
            converts the ['סימול'] field to MARC21 535 encoded field.
        According to the NLI Aleph-Alma conventions the 535 $a Field has a prefix "VIS" for Visual Culture.

        If field ['מיקום פיזי'] exist in original data, then add another 5351 $b field with

        1st indicator (Custodial role) = 1 - Holder of originals.
        $a - Custodian (NR)
        $b - Postal address (R)

        (https://www.loc.gov/marc/bibliographic/bd535.html)[LOC MARC21 bibliographic guidelines]

        :param df: The original Dataframe
        :return: The Dataframe with the new 535 field

        """
    df['5351_1'] = df.סימול.apply(lambda x: '$$aVIS ' + x)

    if column_exists(df, 'מיקוםפיזי'):
        col = 'מיקוםפיזי'
    elif column_exists(df, 'מיקום פיזי'):
        col = 'מיקום פיזי'

    try:
        col
    except NameError:
        print("col variable not defined")
        pass
    else:
        df['5351_2'] = df[col].apply(lambda x: '$$b' + x if x != '' else '')

    df = df.set_index('סימול')
    df = drop_col_if_exists(df, 'סימול')
    drop_col_if_exists(df, col)

    return df


def create_MARC_351_LDR(df):
    """
        converts the ['רמת תיאור'] field to MARC21 351 $c encoded field.
    Information about the organization and arrangement of a collection of items. A closed list of values defined
    by NLI.

    $c - Hierarchical level (NR)

    Also creates MARC LDR  based on hierarchical level.
            - 00000npd^a22^^^^^^a^4500  - for file and item level records
            - 00000npc^a22^^^^^^^^4500 - for all other levels
    :param df: The original Dataframe
    :return:The Dataframe with the new 351 field
    """

    def define_LDR(hier):

        if hier == 'File Record' or hier == 'Item Record':
            return '00000npd#a22######a#4500'
        else:
            return '00000npc#a22########4500'

    if column_exists(df, 'רמת תיאור'):
        col = 'רמת תיאור'
    elif column_exists(df, 'רמתתיאור'):
        col = 'רמתתיאור'
    try:
        col
        df['LDR'] = df[col].apply(define_LDR)
        df['351'] = df[col].apply(lambda x: '$$c' + x)
        df = drop_col_if_exists(df, 'רמתתיאור')
    except NameError:
        print("col variable not defined, cannot find")
        pass
    return df


def create_MARC_245(df):
    """
        converts the ['כותרת'] field to MARC21 24510 $a encoded field.

    1st indicator (Title added entrye) = 1 - Added entry.
    2nd indicator (Nonfiling characters) = 0 - No nonfiling characters

    $a - Title

    :param df: The original dataframe.
    :return The Dataframe with the new 245 field
    """

    col = 'כותרת'

    try:
        col
    except NameError:
        print("col variable not defined")
        pass
    else:
        df['24510'] = df[col].apply(lambda x: '$$a' + str(x).strip() if x != '' else print(f"bad header: [{x}"))
        df = drop_col_if_exists(df, col)

    if column_exists(df, 'כותרתאנגלית'):
        col = 'כותרתאנגלית'
    elif column_exists(df, 'כותרת אנגלית'):
        col = 'כותרת אנגלית'
    else:
        return df

    df['2461'] = df[col].apply(lambda x: '$$iTranslated title:$$a' + x)

    return df


def clean_header_row(df):
    """
        Prepare table headers/column names for further processing:
        - remove unnamed columns
        - clean and convert column names to lower case
        - remove spaces and special characters

    :param df: the original Dataframe.
    :return: The Dataframe with cleaned headers.
    """
    if 'parent' in list(df.columns) and 'סימולאב' in list(df.columns):
        df = drop_col_if_exists(df, 'parent')

    # remove columns which names starts with 'unnamed'
    unnamed_cols = [x for x in list(df.columns) if 'unnamed' in x]

    for col in unnamed_cols:
        df = drop_col_if_exists(df, col)

    # clean and convert column names to lower case
    column_clean = [clean_text(col) for col in list(df.columns)]
    column_clean = map(lambda x: x.lower(), column_clean)
    df.columns = column_clean

    return df



def create_MARC_500(df):
    """
        converts the columns [מספר מיכל] and [קוד תיק ארכיון] and [הערות גלוי למשתמש קצה] and [מילות מפתח_מקומות] to
    MARC21 500 encoded field.

    Definition: General information for which a specialized 5XX note field has not been defined.
    Subfield Codes: $a - General note (NR)

    Actions:
    - add prefix '$$a' to all values
    - check if the there a value for [מספר מיכל] - if yes, concat the value to field 500
    - check if the there a value for [קוד תיק ארכיון] - if yes, concat the value to field 500
    - check if the there a value for [הערות גלוי למשתמש קצה] - if yes, concat the value to field 500
    - check if the there a value for [מילות מפתח_מקומות] - if yes, concat the value to field 500

    :param df: The original Dataframe
    :return: The Dataframe with the new 500 field
    """
    for index, row in df.iterrows():
        new_value = '$$a'
        if 'מספר מיכל' in list(df.columns.values) and str(row['מספר מיכל']) != '':
            new_value = new_value + 'מספר מיכל: ' + str(row['מספר מיכל']) + ';'
        if 'מיכל' in list(df.columns.values) and row['מיכל'] != '':
            new_value = new_value + 'מספר מיכל: ' + str(row['מיכל']) + ';'
        if 'קוד תיק ארכיון' in list(df.columns.values) and str(row['קוד תיק ארכיון']).replace('.0','') != '':
            new_value = new_value + 'קוד תיק ארכיון: ' + row['קוד תיק ארכיון'] + ';'
        if 'הערות גלוי למשתמש קצה' in list(df.columns.values) and row['הערות גלוי למשתמש קצה'] != '':
            new_value = new_value + 'הערות: ' + row['הערות גלוי למשתמש קצה'] + ';'
        if 'מילות מפתח_מקומות' in list(df.columns.values) and row['מילות מפתח_מקומות'] != '':
            new_value = new_value + 'מקומות המוזכרים בתיק: ' + row['מילות מפתח_מקומות'] + ';'

        if new_value == '$$a':
            new_value = ''

        df.loc[index, '500'] = new_value

    return df


def create_MARC_500s_4collection(df):
    df = df.rename(columns={'היסטוריה ארכיונית': '500_1',
                            'תיאור הטיפול באוסף בפרויקט': '500_2',
                            'סוג אוסף': '500_3',
                            'ביבליוגרפיה ומקורות מידע': '581'
                            })
    df['500_1'] = df['500_1'].apply(lambda x: '$$a' + x if x != '' else '')
    df['500_2'] = df['500_2'].apply(lambda x: '$$a' + x if x != '' else '')
    df['500_3'] = df['500_3'].apply(lambda x: '$$aסוג האוסף: ' + x if x != '' else '')
    df = explode_col_to_new_df(df, '581')

    return df


def create_MARC_561(df):
    """
        onverts the columns [סימול מקורי] to  MARC21 561 encoded field.

    Definition: opy-specific field that contains information concerning the ownership and custodial history o
    f the described materials from the time of their creation to the time of their accessioning,
    including the time at which individual items or groups of items were first brought together in their
    current arrangement or collation.

    Subfield Codes: $a - History (NR)

    :param df: The original Dataframe
    :return: The Dataframe with the new 561 field
    """
    if 'סימולמקורי' in list(df.columns.values):
        df['561'] = df['סימולמקורי'].apply(lambda x: '$$a' + str(x) if str(x) != '' else '')
        df = drop_col_if_exists(df, 'סימולמקורי')
    return df


def first_creator(x):
    """
    helper function for creating 100/700 and 110/710 distinction.
    search for first creator (first value until semicolon)

    :param x: a string containing the names and roles of all the creators, separated by semicolons
    :return x: the first value in list

    """
    if ";" in x:
        x = x[: x.find(";")]
        return x
    else:
        return x


def all_rest_creators(x):
    """
    helper function for creating 100/700 and 110/710 distinction.
    search for all rest of the creators

    :param x: a string containing the names and roles of all the creators, separated by semicolons
    :return x: the list without the first creator occurance
    """
    if ";" in x:
        return x[x.find(';') + 1:]
    else:
        return ''


def name_lang_check(val, mode="PERS"):
    """
        Checks the language of a given value (mostly English and Hebrew), in order to add the $e subfield for
    language encoded information for the 1XX/6XX/7XX MARC21 Fields.

    :param mode: is searching language for person or corporation. Defualt set to PERS
    :param: val - the string to check the laguage
    :return: new string for cretor, exchanging adding '$$e' for
        spaces and $$9 for language
    :type val: string
    """

    ad = alphabet_detector.AlphabetDetector()

    val = str(val)
    val = val.strip()

    if val == '' or val == np.nan:
        return ''

    # find alphabet - if there is more that one default it's hebrew
    if len(ad.detect_alphabet(find_name(val))) > 1:
        lang = 'heb'
    elif len(ad.detect_alphabet(find_name(val))) < 1:
        lang = 'heb'
    else:
        lang = ad.detect_alphabet(find_name(val)).pop()[:3].lower()

    # find role
    role = find_role(val)

    if role != '':
        if is_pers(val, Authority_instance.df_creator_pers_role):
            role = map_role_to_relator(find_role(val), Authority_instance.df_creator_pers_role, lang)
        elif is_corp(val, Authority_instance.df_creator_corps_role):
            role = map_role_to_relator(find_role(val), Authority_instance.df_creator_corps_role, lang, mode="CORPS")
        else:
            print("role not found: ", find_role(val))
            role = ''

    if role == '' or role is None:
        val = '$$a' + find_name(val) + "$$9" + lang

    else:
        val = '$$a' + find_name(val) + "$$e" + role + "$$9" + lang

    if val == '$$a$$9heb':
        return ""
    return val


def aleph_creators(df, col_name, mode='PERS'):
    """
    fuction's input is the entire table as a dataframe and
        the column name which contains the creators
    :param df: the entire table
    :param col_name: the column names which contain the cretors
    :param mode: whether we are looking for person roles or corporate body roles
    :return: the new data frame with the split columns for first
        creator and rest of creators
    """
    for index, row in df.iterrows():
        new_creators = list()
        if row[col_name] is None or row[col_name] == '':
            continue
        creators = row[col_name].split(";")
        if len(creators) < 1 and creators[0] == '':
            continue

        elif len(creators) <= 1 and creators[0] != '':
            creator = name_lang_check(creators[0])
            df.loc[index, col_name] = creator
            continue

        for creator in creators:
            creator = name_lang_check(creator)
            creator = creator.strip()
            new_creators.append(creator)

        df.at[index, col_name] = ";".join(new_creators)
    df = remove_duplicate_in_column(df, col_name)
    return df


def create_MARC_100_110(df):
    """
    create coluumn for first creator
    check if creator is a person of a corporate body - against the CVOC of creators roles,
    and insert the value in the respective colomn

    100 - Main Entry-Personal Name (NR)
    -----------------------------------
    Definition:
    Personal name used as a main entry in a bibliographic record. Main entry is assigned according to various
    cataloging rules, usually to the person chiefly responsible for the work.

    1st indicator (Title added entrye) = 1 - Surname

    Subfield Codes:
    $a - Personal name (NR)
    $e - Relator term (R)
    $9 - language code

    110 - Main Entry-Corporate Name (NR)
    ------------------------------------
    Definition:
    Corporate name used as a main entry in a bibliographic record. According to various cataloging rules,
    main entry under corporate name is assigned to works that represent the collective thought of a body.

    1st indicator (Type of corporate name entry element) = 2 - Name in direct order

    Subfield Codes:
    $a - Corporate name or jurisdiction name as entry element (NR)
    $e - Relator term (R)
    $9 - language code

    :param df:
    :return: the modified dataframe with the new 100 and 110 MARC21 encoded fields
    """

    df['1001'] = ''
    df['1102'] = ''

    # create column for first creator
    df['יוצר_ראשון'] = df.יוצרים.apply(lambda x: first_creator(x))
    df = df.replace(np.nan, '')

    # check if first creator is a person or a corporate body
    for index, row in df['יוצר_ראשון'].iteritems():
        if is_corp(row, Authority_instance.df_creator_corps_role):
            df.loc[index, '1102'] = row
        elif is_pers(row, Authority_instance.df_creator_pers_role):
            df.loc[index, '1001'] = row

    df = df.replace(np.nan, '')
    df = drop_col_if_exists(df, 'יוצר_ראשון')
    df['1001'] = df['1001'].apply(name_lang_check)
    df['1102'] = df['1102'].apply(name_lang_check)

    return df


def create_MARC_700_710(df):
    """
    create new column in dataframe for all the rest of creators
    :param: df: the dataframe
    """

    # all the rest of creators (Personalities)
    df['7001'] = df['יוצרים אישים'].apply(lambda x: all_rest_creators(x))
    # all the rest of creators (Corporate bodies)
    df['7102'] = df['יוצרים מוסדות'].apply(lambda x: all_rest_creators(x))

    df = project_photographer(df)

    df = aleph_creators(df, '7001')
    df = aleph_creators(df, '7102')

    df['7001'] = df['7001'].astype('str')
    df['7102'] = df['7102'].astype('str')

    df = remove_duplicate_in_column(df, '7001')
    df = remove_duplicate_in_column(df, '7102')

    # check there are no duplicates in 100 and 700
    for index, row in df.iterrows():
        lst_7001 = row['7001'].split(";")
        lst_7102 = row['7102'].split(";")

        if row['1001'] in lst_7001 and row['1001'] != '':
            print("100", row['1001'], "is in 700", lst_7001)
            lst_7001.remove(row['1001'])

        if row['1102'] in lst_7102 and row['1102'] != '':
            print("110", row['1102'], "is in 710", lst_7102)
            lst_7102.remove(row['1102'])

        df.loc[index, '7001'] = ';'.join(lst_7001)
        df.loc[index, '7102'] = ';'.join(lst_7102)

    df = explode_col_to_new_df(df, '7001')
    df = explode_col_to_new_df(df, '7102')

    df = drop_col_if_exists(df, '7001')
    df = drop_col_if_exists(df, '7102')

    return df


def create_MARC_300(df):
    """
        converts the ['רמת תיאור'] field to MARC21 351 $c encoded field.
    Information about the organization and arrangement of a collection of items. A closed list of values defined
    by NLI.

    $c - Hierarchical level (NR)

    :param df: The original Dataframe
    :return:The Dataframe with the new 351 field
    """
    col = [x for x in list(df.columns.values) if 'היקף' in x][0]

    try:
        col
    except NameError:
        print("col variable not defined")
        pass
    else:
        df['300'] = df[col].apply(lambda x: '$$c' + str(x))

        df = drop_col_if_exists(df, col)

    return df


def check_values_arch_mat(df, arch_mat_col, arch_mat_mapping_dict):
    arch_test = df[arch_mat_col].tolist()
    new_arch = ';'.join(arch_test)
    new_arch = list(set(new_arch.split(";")))
    new_arch = list(filter(None, new_arch))  # fastest

    error_values = list()

    for item in new_arch:
        best, score = process.extractOne(item, list(arch_mat_mapping_dict.keys()))
        #     print(item, 'best choice:', best, item == best)
        if best == item:
            continue
        else:
            error_values.append(item)
    #             raise Exception("{} is not in archival material controlled vocabulary".format(item))
    return error_values


def create_MARC_defualt_copyright(df):
    df['5420'] = '$$lCopyright status not determined; ' + \
                 'Contract$$nNo copyright analysis' + \
                 f'$$oNoam Solan by Yael Gherman {datetime.datetime.now().strftime("%Y%m%d")}$$qללא ניתוח מצב זכויות'
    df['5061'] = '$$aLibrary premises only;$0000000008'
    df['540'] = '$$aאיסור העתקה' + \
                '$$uhttp://web.nli.org.il/sites/NLI/Hebrew/library/items-terms-of-use/Pages/nli-copying-prohibited.aspx'

    return df


def create_marc_655(df):
    """
        [סוג חומר] column

    All archival material concepts (in hebrew) in the The Visual Arts project Authority file for Archival Material have
     been mapped and aligned to Getty's Art and Architecture Thesaurus (AAT)

    Since all of our concepts are aligned to AAT, the indicators of the 655 field are:
    2nd indicator = 7 - Source specified in subfield $2 (aat, tgm, and so on) if the value is aligned to a known controlled vocabulary
    2nd indicator = 7 - Source = "local" specified in subfield $2 if there is no mapping to a known controlled vocabulary.

    subfields
    $a - Genre/form data or focus term
    $0 - Authority record control number or standard number - we use the direct URI of the Getty's AAT Linked Data
    $2 - Source of term - for this data always AAT
    :param df:
    :return df: the modified df
    """

    if column_exists(df, 'סוגחומר'):
        col = 'סוגחומר'
    elif column_exists(df, 'סוגהחומר'):
        col = 'סוגהחומר'
    elif column_exists(df, 'סוג החומר'):
        col = 'סוגהחומר'
    elif column_exists(df, 'סוג חומר'):
        col = 'סוגהחומר'
    try:
        col
    except NameError:
        print("col variable not defined")
        pass
    else:
        arch_mat_col = process.extractOne(col, list(df.columns))[0]

        df_arch_mat_mapping = Authority_instance.df_arch_mat_auth.loc[
            Authority_instance.df_arch_mat_auth.index, ['ARCHIVAL_MATERIAL', 'MARC21 655 7', 'rdacontent 336']]
        arch_mat_mapping_dict = pd.Series(df_arch_mat_mapping['MARC21 655 7'].values,
                                          index=df_arch_mat_mapping.ARCHIVAL_MATERIAL.values).to_dict()

        test_655 = check_values_arch_mat(df, arch_mat_col, arch_mat_mapping_dict)

        for index, row in df.iterrows():
            lst_655_7 = row[arch_mat_col].split(";")
            # print(index, '\n', 'before:', lst_655_7)
            lst_655_7 = list(map(str.strip, lst_655_7))
            temp = list()
            final = list()
            for term in lst_655_7:
                if ")" in term:
                    temp.append(re.findall(r'\((.*)\)', term)[0])
            for term in temp:
                if term == 'תצלומים':
                    continue
                final.append(term.strip())
            lst_655_7 = lst_655_7 + final
            lst_655_7 = replace_lst_dict(lst_655_7, arch_mat_mapping_dict)
            # print('after:', lst_655_7)

            df.loc[index, '655 7'] = ";".join(lst_655_7)

        df = remove_duplicate_in_column(df, '655 7')

        df = explode_col_to_new_df(df, '655 7')
        df = drop_col_if_exists(df, '655 7')
    return df


def project_photographer(df):
    for index, row in df.iterrows():
        if 'צלם פרויקט' in row['7001']:
            val = df.loc[index, '7001']
            val = val.replace('צלם פרויקט', 'צלם')
            # update 5420
            df.loc[index, '5420'] = '$$dNational Library of Israel$$dהספריה הלאומית'
            df.loc[index, '7001'] = val
        if 'צלמת פרויקט' in row['7001']:
            val = df.loc[index, '7001']
            val = val.replace('צלמת פרויקט', 'צלם')
            # update 5420
            df.loc[index, '5420'] = '$$dNational Library of Israel$$dהספריה הלאומית'
            df.loc[index, '7001'] = val

    return df


def create_MARC_506_post_copyright(df, cols):
    """
    fuction's input is the entire table as a dataframe and constructs the 506 field according to the POST_COPYRIGHT
    file.

    :param cols:
    :param df: the entire table
    :return: the new data frame with the new MARC 506 encoded Field
    """
    if 'd' in cols[0]:
        field_506d = cols[0]
        field_506 = cols[1]
    else:
        field_506d = cols[1]
        field_506 = cols[0]

    df[field_506d] = df[field_506d].apply(lambda x: '$$d' + x if x != '' else '')
    df['506'] = df[field_506] + df[field_506d]

    df = drop_col_if_exists(df, field_506d)
    df = drop_col_if_exists(df, field_506)

    return df


def create_MARC_041(df):
    """
    fuction's input is the entire table as a dataframe and constructs the 041 field according to the [שפה] column.

    :param df: the entire table
    :return: the new data frame with the new MARC 041 encoded Field
    """
    col = 'שפה'

    try:
        col
    except NameError:
        print("col variable not defined")
        pass
    else:
        language_mapper = Authority_instance.df_languages.to_dict()

        for index, row in df.iterrows():
            if row['שפה'] == '':
                continue
            languages = row['שפה'].split(';')
            try:

                new_lang = ['$$a' + language_mapper['קוד שפה'][k] for k in languages if len(languages) > 0]
            except:
                pass
            df.loc[index, '041'] = ''.join(new_lang)

            field_008 = list(row['008'])
            # insert MARC langauge code in positions 35-37
            for i in range(35, 38):
                field_008[i] = new_lang[0][i - 32]

            df.loc[index, '008'] = ''.join(field_008)

        # df = drop_col_if_exists(df, 'שפה')

    return df


def create_MARC_542_post_copyright(df, col):
    """
    fuction's input is the entire table as a dataframe and constructs the 542 field according to the POST_COPYRIGHT
    file.

    :param col:
    :param df: the entire table
    :return: the new data frame with the new MARC 542 encoded Field
    """

    df = df.rename(columns={col[0]: '542'})

    return df


def create_MARC_540_post_copyright(df, col):
    """
    fuction's input is the entire table as a dataframe and constructs the 542 field according to the POST_COPYRIGHT
    file.

    :param col:
    :param df: the entire table
    :return: the new data frame with the new MARC 540 encoded Field
    """

    df = df.rename(columns={col[0]: '540'})

    return df


def create_MARC_597(df, col):
    """
       fuction's input is the entire table as a dataframe and constructs the 597 field according to the POST_COPYRIGHT
       file.

       :param col:
       :param df: the entire table
       :return: the new data frame with the new MARC 597 encoded Field
       """

    # df = df.rename(columns={col[0]: '597'})
    df[col[0]] = df[col[0]].apply(lambda x: '$$a' + x)
    df[col[1]] = df[col[1]].apply(lambda x: '$$b' + x)
    df['597'] = df[col[0]] + df[col[1]]

    df = drop_col_if_exists(df, col[0])
    df = drop_col_if_exists(df, col[1])

    return df


def create_MARC_260(df, col, date_cols):
    """
        fuction's input is the entire table as a dataframe and constructs the 260 field according to the POST_COPYRIGHT
        file.

        :param date_cols:
        :param col:
        :param df: the entire table
        :return: the new data frame with the new MARC 008 encoded Field
        """

    countries_code_mapper = Authority_instance.df_countries.set_index('מדינת פרסום').to_dict()['MARC']

    df[date_cols[0]] = df[date_cols[0]].astype(str)
    df[date_cols[1]] = df[date_cols[1]].astype(str)

    """
    **************************************************************************************************** 
    the usage of only the year (first 4 digits will be kept only until we figure out what to do with all 
    the date, and in which MARC field the full notmalized -date (YYYY-MM-DD) can be recorded
    ****************************************************************************************************
    """
    df[date_cols[0]] = df[date_cols[0]].apply(lambda x: x[:4])
    df[date_cols[1]] = df[date_cols[1]].apply(lambda x: x[:4])

    for index, row in df.iterrows():
        if row[col] == '' or row[col] is None:
            continue
        countries = row[col].split(';')
        countries = list(filter(None, countries))
        if len(countries) > 0:
            field_008_country = ['$$a' + countries_code_mapper[k] for k in countries if len(k) > 0]
            first_country = field_008_country[0][3:]
            if len(first_country) == 2:
                first_country += '#'

            df.loc[index, '044'] = ''.join(field_008_country)
        else:
            first_country = 'xx#'  # code xx# is xx# No place, unknown, or undetermined

        countries = ['$$e[' + x + ']$$9heb' for x in countries]

        if row[date_cols[2]] == '' or row[date_cols[2]] == None:
            df.loc[index, '260'] = ''.join(countries)
        else:
            df.loc[index, '260'] = ''.join(countries) + '$$g' + str(row[date_cols[2]]).strip()

        # deal with 008 field
        # insert date 1 and date 2 in positions 7-14
        field_008 = list(row['008'])
        date = row[date_cols[0]] + row[date_cols[1]]
        try:
            for i in range(7, 15):
                field_008[i] = date[i - 7]
        except:
            print('error')
            sys.exit()
        # insert MARC country code in positions 15-17

        for i in range(15, 18):
            try:
                field_008[i] = first_country[i - 15]
            except:
                pass

        df.loc[index, '008'] = ''.join(field_008)

    df = drop_col_if_exists(df, 'col')

    return df


def create_MARC_520(df):
    """
        converts the ['תיאור'] field to MARC21 520 $a encoded field.

    Subfield Codes
    $a - Summary, etc. (NR)

    :param df: The original dataframe.
    :return The Dataframe with the new 245 field
    """

    col = 'תיאור'

    try:
        col
    except NameError:
        print("col variable not defined")
        pass
    else:
        try:
            df['520'] = df[col].apply(lambda x: '$$a' + str(x).strip() if str(x) != '' else '' or x is not None)
            df = drop_col_if_exists(df, col)
        except:
            pass

    return df


def get_cms_sid(custom04_path, collectionID, df, CMS):
    """
        Fumctions takes the custom04 that maps the call number and the Aleph systme number,
    creates a mapping dataframe (df_aleph) and adds a column system number to the original dataframe.
    :param CMS:
    :type df: Dataframe
    :type custom04_path: Path
    :param custom04_path:
    :param collectionID:
    :param df: the original dataframe
    :return: Two dataframes:
                1. df_aleph - the dataframe that  maps the call number (911) to Aleph system number.
                2. df - the dataframe with system number column
    """
    sysno_file = custom04_path / (collectionID + '_{}_sysno.xlsx'.format(CMS))

    assert os.path.isfile(sysno_file), "There is no such File: sysno_file"

    # parse sysno file
    xl2 = pd.ExcelFile(sysno_file)
    if CMS == 'aleph':
        df_aleph = xl2.parse('Sheet1')
    else:
        df_aleph = xl2.parse('results')

    # rename columns
    df_aleph = df_aleph.rename(columns={'Adlib reference (911a)': '911##a'})

    df_aleph = df_aleph.set_index(list(df_aleph)[1])
    df_aleph.index.names = ['סימול']
    df_aleph = df_aleph.iloc[:, 0:1]
    df_aleph.columns = ['System number']

    df = df.join(df_aleph, how='left')

    return df, df_aleph


def get_parent_root_mms_id(index):
    return ROOTID_finder(index)


def create_MARC_773(df):
    for index, row in df.iterrows():
        try:
            if '$$cSection Record' in row['351']:
                continue

            df.loc[index, '77318'] = f"$$t{get_root_title(df, index)}$$w{ROOTID_finder(index)}"
        except:
            pass

    return df


def format_cat_date(df):
    """
        convert the date into YYMM format for construction of the 921/933 fields.
    :param df: the original dataframe
    :return: the modified dataframe with the reformatted cataloguing date field.
    """
    if column_exists(df, clean_text('תאריך הרישום')):
        cat_date_col = clean_text('תאריך הרישום')
    else:
        cat_date_col = process.extractOne('date_cataloguing', list(df.columns))

    df[cat_date_col] = df[cat_date_col].apply(str)

    df[cat_date_col] = df[cat_date_col].apply(lambda x:
                                              datetime.datetime.strftime(dateutil.parser.parse(x), '%Y%m')
                                              if len(x) > 6 else x)

    return df


def create_MARC_921_933(df):
    """
        Fields [שם הרושם] [תאריך הרישום] are converted into the format of NLI cataloguer signiture.
    The mapping is defined in the AuthorityFiles Class instance - in the cataloger_name_mapper attribute.
    The format of the MARC encoded 921/933 fields is "F[first name + last name initials] MMYYYY

    Change the catalogers names to their Aleph abbriviation as defined in above dictionary
    Add [year][month] to the string and place value in 921##a field.

    steps:
    ------
    1. extract extract the unique catalogers names from field [שם הרושם]
    2. match the names to the existing names of cataloguer in the controlled vocabulary
    3. map and replace the cataloguer names with the correct names of the controlled vocabulary
    4. map and replace the cataloguer names to their Aleph codes.
    5. construct the 921 field following the NLI guidelines - "$$a[cataloguer code] [YYYYMM]"

    NOTES for current version:
    --------------------------
    in the meantime its year month are static figures
    if cataloger field was empty a default value was introduced

    :param df:
    :return: The modified dataframe with the new 921 and 933 fields
    """

    try:
        cat_col = process.extractOne('שםהרושם', list(df.columns))[0]
    except:
        cat_col = process.extractOne('cataloger', list(df.columns))[0]

    try:
        cat_date_col = process.extractOne('תאריךהרישום', list(df.columns))[0]
    except:
        cat_date_col = process.extractOne('datecataloging', list(df.columns))[0]
    print("cat_col:", cat_col)
    print("cat_date_col:", cat_date_col)

    # initialize 921/933 columns
    df['921'] = ''
    # df['933'] = ''

    if df[cat_col].str.contains(";").any():
        df['933'] = ''
        df_multi_cat = df[df[cat_col].str.contains(';')]
        for index, row in df_multi_cat.iterrows():
            df.loc[index, '921'] = first_creator(row[cat_col])
            df.loc[index, '933'] = all_rest_creators(row[cat_col])

    # map and replace the cataloguer names with the correct names of the controlled vocabulary
    # map and replace the cataloguer names to their Aleph codes
    # construct the 921 field following the NLI guidelines
    df['921'] = df[cat_col].map(Authority_instance.cataloger_name_mapper)
    df['921'] = df['921'].map(str) + ' ' + df[cat_date_col]
    print('cat_date type: ', df[cat_date_col].dtype)
    df['921'] = df['921'].apply(lambda x: '$$a' + x)

    if column_exists(df, '933'):
        df['933'] = df['933'].map(Authority_instance.cataloger_name_mapper)
        df['933'] = df['933'].map(str) + ' ' + df[cat_col]
        df['933'] = df['933'].apply(lambda x: '$$a' + x)

    return df


def create_MARC_BAS(df):
    """

    :param df: the original Dataframe
    :return: The modified datafrmae with the additional BAS encoded field contaning 'VIS'
    """
    df['906'] = '$$aVIS'
    return df


def create_MARC_OWN(df):
    """
        Adding OWN field to the data frame.
    :param df: the original Dataframe
    :return: The modified datafrmae with the additional OWN encoded field contaning 'NNL'
    """
    df['948'] = '$$aNNL'
    return df


def create_MARC_FMT(df):
    """
        Adding FMT field to the data frame.
        derived from Leader/006.
        for the sake of the example it is assumed that the collection contains mixed materials,
        and that Leader/006 = 'p'.

    sources:
    ---------
    LoC MARC21 Guidelines/Leader
    ExLibris/Logic for assigning FMT
    :param df: the original Dataframe
    :return: The modified datafrmae with the additional OWN encoded field contaning 'NNL'
    """
    df['FMT'] = 'MX'
    return df


def create_MARC_999(df):
    """
        999##a - in the meantime not defined (it should be first hierarchy of 'סוג חומר')
        999##b - static value is 'NOULI'

    :param df:
    :return:
    """
    df['999_1'] = '$$bNOULI'
    df['999_2'] = '$$bNOOCLC'
    df['999_3'] = '$$aARCHIVE'

    return df


def create_MARC_524(df):
    """
        524$$a - Preferred Citation of Described Materials Note
    :param df: 
    :return: 
    """

    collection_name_heb = df.loc[df.index[df['רמת תיאור'] == 'Section Record'], '911_1']
    collection_name_eng = df.loc[df.index[df['רמת תיאור'] == 'Section Record'], '911_2']

    def create_citation_heb(index, collection_name_heb):
        citation_heb = collection_name_heb + ', ' + 'הספריה הלאומית, סימול: ' + index
        return citation_heb

    def create_citation_eng(index, collection_name):
        citation_eng = collection_name_eng + ', ' + 'National Library of Israel, Reference code: ' + index
        return citation_eng

    for index, row in df.iterrows():
        citation_heb = '$$a' + create_citation_heb(index, collection_name_heb)
        citation_eng = '$$a' + create_citation_eng(index, collection_name_eng)
        df.loc[index, '524_1'] = citation_heb
        df.loc[index, '524_2'] = citation_eng

    return df


def create_MARC_600(df):
    """
    create column for personal entry names and add column to table as number
    of names occurances that appear in field

    colomn [מילות מפתח_אישים]
    Subject added entry in which the entry element is a personal name.
    First Indicator - Type of personal name entry element = 1 - Surname

    :param df:
    :return:
    :param: df: the dataframe

    """
    if column_exists(df, 'מילותמפתחאישים'):
        df = aleph_creators(df, 'מילותמפתחאישים')
        df['6001'] = df['מילותמפתחאישים']
        df = drop_col_if_exists(df, 'מילותמפתחאישים')

        df = explode_col_to_new_df(df, '6001')
        df = df.fillna('')

        df = drop_col_if_exists(df, '6001')

    return df


def create_MARC_610(df):
    """
    create column for personal entry names and add column to table as number
    of names occurances that appear in field
    :param df:
    :return:
    :param: df: the dataframe

    """

    if column_exists(df, 'מילותמפתחאישים'):
        col = 'מילותמפתחארגונים'
    elif column_exists(df, 'מילותמפתחמוסדות'):
        col = 'מילותמפתחמוסדות'
    else:
        return df

    df = aleph_creators(df, col)
    df['6102'] = df[col]
    df = drop_col_if_exists(df, col)

    df = explode_col_to_new_df(df, '6102')
    df = df.fillna('')

    df = drop_col_if_exists(df, '6102')

    return df


def create_MARC_630(df):
    """
    create coloumn for first creator
    check if creator is a person of a corporate body - against the CVOC of creators roles,
    and insert the value in the respective colomn

    Column [מילות מפתח יצירות]
    Subject added entry in which the entry element is a uniform title.

    first indicator: Nonfiling - empty
    second indicator: Thesaurus

    4 - Source not specified
    Subfield used: $a


    :param: df: the dataframe

    """
    if column_exists(df, 'מילותמפתחיצירות'):
        df = aleph_creators(df, 'מילותמפתחיצירות')
        df['630 4'] = df['מילותמפתחיצירות']
        df = drop_col_if_exists(df, 'מילותמפתחיצירות')

        df = explode_col_to_new_df(df, '630 4')
        df = df.fillna('')

        df = drop_col_if_exists(df, '630 4')

    return df


def create_MARC_336(df):
    """
        he form of communication through which a work is expressed.
         Used in conjunction with Leader /06 (Type of record), which indicates the general type of content
         of the resource.
         Field 336 information enables expression of more specific content types and content types from various lists.

         subfields
            $a - Content type term (R) - Content type of the work being described.
            $b - Content type code (R) - Code representing the content type of the work being described.
            $2 - Source (NR) - MARC code that identifies the source of the term or code used to record the content
            type information. Code from: Genre/Form Code and Term Source Codes.
            The Project mapped all it's Archival Materiel terms from its Archival Materiel controlled vocabulary
            to the RDA content type terms and constructed the subfields according to the agreed upon mapping with Ahava.
            (Archival Material - RDA content type mapping talbe)
    :param df:
    :return:
    """
    arch_mat_map_336 = Authority_instance.df_arch_mat_auth.loc[:,
                       ['ARCHIVAL_MATERIAL', 'rdacontent 336']].set_index('ARCHIVAL_MATERIAL').to_dict()[
        'rdacontent 336']

    for index, row in df.iterrows():
        lst_336 = row['סוג חומר'].split(";")
        lst_336 = list(map(str.strip, lst_336))
        lst_336 = replace_lst_dict(lst_336, arch_mat_map_336)
        print(lst_336)
        df.loc[index, '336'] = ";".join(lst_336)

    df = remove_duplicate_in_column(df, '336')

    df_explode_336 = df['336'].str.split(';', expand=True).rename(columns=lambda x: f"336_{x + 1}")
    df_explode_336 = df_explode_336.replace(np.nan, '')
    df = pd.concat([df, df_explode_336], axis=1)
    cols_336 = [x for x in list(df.columns.values) if '336' in x]
    df = drop_col_if_exists(df, '336')
    df = drop_col_if_exists(df, 'סוג חומר')

    return df, df_explode_336


def create_MARC_337_338(df):
    """
        ccording to Ahava, the RDA Media Type and RDA Carrier Type should be for all the resources in the project as follows:

        337 = online resource
        338 = computer
        Therefore the two fields will contain a constant string:

        '337' = 𝑎𝑜𝑛𝑙𝑖𝑛𝑒𝑟𝑒𝑠𝑜𝑢𝑟𝑐𝑒bcr$$2rdacarrier
        '338' = 𝑎𝑐𝑜𝑚𝑝𝑢𝑡𝑒𝑟bc$$2rdamedia

    :param df:
    :return:
    """
    df['337'] = '$$acomputer$$bc$$2rdamedia'
    df['338'] = '$$aonline resource$$bcr$$2rdacarrier'

    return df


def create_MARC_534(df):
    """
        rom LoC MARC21 format for bibliogrphic records guidelines: Descriptive data for an original item when
         the main portion of the bibliographic record describes a reproduction of that item and the data differ.
         Details relevant to the original are given in field 534.

         The resource being cataloged may either be a reproduction (e.g., scanned image, or PDF), or an edition
         that is similar enough that it could serve as a surrogate for the original (e.g., HTML).

            $e - Physical description, etc. of original (NR)
            $p - constant text: "מנשא והפורמט הפיזי של הפריט המקורי" + "carrier and format of original item"

    :param df:
    :return:
    """
    # create a dataframe as source for mapping media/format values
    df_media_format_mapping = Authority_instance.df_media_format_auth.loc[Authority_instance.df_media_format_auth.index,
                                                                          ['MEDIA_FORMAT', 'MARC21 534']]

    # export media/format mapping DF to dictionary
    arch_media_format_map_534 = pd.Series(df_media_format_mapping['MARC21 534'].values,
                                          index=df_media_format_mapping.MEDIA_FORMAT.values).to_dict()

    df = remove_duplicate_in_column(df, 'מדיה + פורמט')

    for index, row in df.iterrows():
        try:
            lst_534 = row['מדיה + פורמט'].split(";")
        except:
            print(df.columns)
        lst_534_final = ['$$pמנשא והפורמט הפיזי של הפריט המקורי.' + "$$e" + s.strip() if s != '' else '' for s in
                         lst_534]
        lst_534_final = replace_lst_dict(lst_534_final, arch_media_format_map_534)
        df.at[index, '534'] = ";".join(lst_534_final)

    df = remove_duplicate_in_column(df, '534')
    df = explode_col_to_new_df(df, '534')
    df = drop_col_if_exists(df, '534')

    return df


def create_MARC_STA(df):
    df['STA'] = '$$aSUPPRESSED'
    return df


def create_MARC_590(df):
    def digitization_data(row):
        if column_exists(df, 'estfilesnum'):
            new_value = 'מסלולי דיגיטציה: '
            if str(row['digitization']) != '' and (
                    str(row['digitization']).strip() == 'כן' or str(row['digitization']).strip() == 'לא'):
                new_value = new_value + 'מיועד לסריקה-' + str(row['digitization']) + ';'

            if str(row['twosidescan']) != '':
                new_value = new_value + 'סריקה דו-צדדית-' + str(row['twosidescan']) + ';'
            if str(row['estfilesnum']) != '':
                new_value = new_value + 'מספר קבצים מוערך-' + str(row['estfilesnum']) + ';'
            if new_value == 'מסלולי דיגיטציה: ':
                return ''
        elif column_exists(df, 'נשלחלדיגיטציה') or column_exists(df, 'נשלח לדיגיטציה'):
            new_value = 'מסלולי דיגיטציה: '
            if str(row['נשלחלדיגיטציה']) != '' and (
                    str(row['נשלחלדיגיטציה']).strip() == 'כן' or str(row['נשלחלדיגיטציה']).strip() == 'לא'):
                new_value = new_value + 'מיועד לסריקה-' + str(row['נשלחלדיגיטציה']) + ';'
            elif str(row['נשלחלדיגיטציה']) != '' and (
                    str(row['נשלחלדיגיטציה']).strip() != 'כן' or str(row['נשלחלדיגיטציה']).strip() != 'לא'):
                new_value = new_value + 'מסלול דיגיטציה-' + str(row['נשלחלדיגיטציה']) + ';'
            if str(row['סריקהדוצדדית']) != '':
                new_value = new_value + 'סריקה דו-צדדית-' + str(row['סריקהדוצדדית']) + ';'
            if str(row['מספרקבציםמוערך']) != '':
                new_value = new_value + 'מספר קבצים מוערך-' + str(row['מספרקבציםמוערך']) + ';'
            if new_value == 'מסלולי דיגיטציה: ':
                return ''

        elif column_exists(df, 'דיגיטציה'):
            new_value = 'מסלולי דיגיטציה: '
            if str(row['דיגיטציה']) != '' and (
                    str(row['דיגיטציה']).strip() == 'כן' or str(row['דיגיטציה']).strip() == 'לא'):
                new_value = new_value + 'מיועד לסריקה-' + str(row['דיגיטציה']) + ';'
            elif str(row['דיגיטציה']) != '' and (
                    str(row['דיגיטציה']).strip() != 'כן' or str(row['דיגיטציה']).strip() != 'לא'):
                new_value = new_value + 'מסלול דיגיטציה-' + str(row['דיגיטציה']) + ';'
            if str(row['סריקהדוצדדית']) != '':
                new_value = new_value + 'סריקה דו-צדדית-' + str(row['סריקהדוצדדית']) + ';'
            if str(row['מספרקבציםמוערך']) != '':
                new_value = new_value + 'מספר קבצים מוערך-' + str(row['מספרקבציםמוערך']) + ';'
            if new_value == 'מסלולי דיגיטציה: ':
                return ''

        else:
            new_value = 'מסלולי דיגיטציה: '
            if row['מסלולדיגיטציה'] != '' and (
                    row['מסלולדיגיטציה'].strip() == 'כן' or row['מסלולדיגיטציה'].strip() == 'לא'):
                new_value = new_value + 'מיועד לסריקה-' + str(row['מסלולדיגיטציה']) + ';'
            elif row['מסלולדיגיטציה'] != '' and (
                    row['מסלולדיגיטציה'].strip() != 'כן' or row['מסלולדיגיטציה'].strip() != 'לא'):
                new_value = new_value + 'מסלול דיגיטציה-' + str(row['מסלולדיגיטציה']) + ';'
            if row['סריקהדוצדדית'] != '':
                new_value = new_value + 'סריקה דו-צדדית-' + str(row['סריקהדוצדדית']) + ';'
            if row['מספרקבציםמוערך'] != '':
                new_value = new_value + 'מספר קבצים מוערך-' + str(row['מספרקבציםמוערך']) + ';'
            if new_value == 'מסלולי דיגיטציה: ':
                return ''
        value = '$$a' + new_value
        return value.strip()

    df['590_1'] = df.apply(lambda row: digitization_data(row), axis=1)
    if column_exists(df, 'הערותחסויותלמשתמש'):
        df['590_2'] = df['הערותחסויותלמשתמש'].apply(lambda x: '$$a' + x.strip() if x != '' else '')

    if column_exists(df, '590_2'):
        df['590_2'] = df['590_2'].where(df['590_2'] == '$$a', '')

    return df


def create_MARC_584(df):
    if column_exists(df, 'ACCURALS') or column_exists(df, 'אוסףפתוח') or column_exists(df, 'אוסף פתוח'):
        accurals_mapper = {'כן': 'האוסף המקורי ממשיך לצבור חומרים (אוסף פתוח)',
                           'לא': '$aהאוסף המקורי אינו צובר חומרים חדשים (אוסף סגור)'}
        df['584'] = df['584'].map(accurals_mapper)
        df['584'] = df['584'].apply(lambda x: '$a' + x)
        return df


def create_907_dict(ROS_file):
    d = {}
    for record in ROS_file.getElementsByTagName('record'):
        # for e in record.getElementsByTagName('controlfield'):
        #     if e.attributes['tag'].value == '001':
        #         id = e.childNodes[0].data
        id = next(e.childNodes[0].data for e in record.getElementsByTagName('controlfield') if
                  e.attributes['tag'].value == '001')

        dd = {}
        for e in record.getElementsByTagName('datafield'):
            if e.attributes['tag'].value == '907':
                for sb in e.getElementsByTagName('subfield'):
                    dd['907' + sb.attributes['code'].value] = sb.childNodes[0].data

        d[id] = dd
    return d


def create_907_value(id, dict_907):
    words = []
    for tag, value in dict_907.items():

        if len(value) == 0:
            return ''
        else:
            words.append(tag[3:] + value)
    return '$$' + '$$'.join(words)


def add_MARC_907(collection):
    rosetta_file_path = str(collection.digitization_path / "ROS" / (collection.collection_id + "_907.xml"))
    rosetta_file = minidom.parse(rosetta_file_path)
    df = collection.df_final_data
    rosetta_dict = create_907_dict(rosetta_file)

    df['907'] = ''
    for index, row in df.iterrows():
        try:
            if index == np.nan:
                sys.stderr.write(f"this index: {index} for {row['סימול']} is missing")
            elif index not in rosetta_dict.keys():
                sys.stderr.write(f"there is no 907 field for : {index}, for call number {row['סימול']}.")
                sys.exit()
            elif len(rosetta_dict[index]) == 0:
                continue
            else:
                df.loc[index, '907'] = create_907_value(index, rosetta_dict[index])
        except:
            pass


    return collection


def add_MARC_597(collection):
    df_597 = Authority_instance.df_credits
    collection.df_final_data['597'] = f"$$a{str(df_597.loc[collection.collection_id, 'קרדיט עברית']).strip()}" \
                                      f"$$b{str(df_597.loc[collection.collection_id, 'קרדיט אנגלית']).strip()}"

    return collection


def create_MARC_final_table(collection):
    df_final_cols = [x for x in list(collection.df_final_data.columns) if x[0].isdigit()] + ['LDR']
    collection.marc_data = collection.df_final_data[df_final_cols]

    counter, run_time = collection.create_MARC_XML()
    sys.stderr.write("%s total records written to file in %s seconds.\n\n" % \
                     (counter, run_time))

    return collection
