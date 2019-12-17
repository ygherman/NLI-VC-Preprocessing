import difflib
import os
import pprint
from collections import defaultdict

import pandas as pd
from fuzzywuzzy import process

from VC_collections import Collection
from VC_collections.AuthorityFiles import *
from VC_collections.columns import clean_text_cols, strip_whitespace_af_semicolon, remove_duplicate_in_column, \
    drop_col_if_exists, replace_NaN
from VC_collections.files import write_excel


def split_creators_by_type(df, col_name):
    """
    take the col name of the col that contains multiple creators (corps+pers) and split them in to\
    2 different columns take the add_creators column and split it in to add_pers and add_corp according to the role.
    if the role is in the corps role, and if the role in in the pers role list

    :param df: The original Dataframe
    :param col_name:  the column name which contains the creators
    :return: df: the modified dataframe with two new columns - creators_pers and creators corps
    """

    for index, row in df.iterrows():
        add_pers_creators = []
        add_corps_creators = []
        for creator in str(row[col_name]).split(';'):
            for k, v in Authority_instance.roles_dict.items():
                if find_role(creator) in v:
                    if "pers" in k:
                        add_pers_creators.append(creator)
                    else:
                        add_corps_creators.append(creator)
        if "CREATOR_" in df.columns.values:
            if str(row['CREATOR_PERS']) != "":
                add_pers_creators.append(
                    str(row['CREATOR_PERS']).strip() + ' [' + str(row['CREATOR_PERS_ROLE']).strip() + ']')
            if str(row['CREATOR_CORP']) != "":
                add_corps_creators.append(
                    str(row['CREATOR_CORP']).strip() + ' [' + str(row['CREATOR_CORP_ROLE']).strip() + ']')

        add_pers_creators = list(filter(None, add_pers_creators))
        add_corps_creators = list(filter(None, add_corps_creators))

        df.loc[index, "COMBINED_CREATORS_PERS"] = ";".join(add_pers_creators)
        df.loc[index, "COMBINED_CREATORS_CORPS"] = ";".join(add_corps_creators)
    if 'COMBINED_CREATORS' in df.columns.values:
        df.COMBINED_CREATORS = df.COMBINED_CREATORS.str.strip()
    df.COMBINED_CREATORS_CORPS = df.COMBINED_CREATORS_CORPS.str.strip()
    df.COMBINED_CREATORS_PERS = df.COMBINED_CREATORS_PERS.str.strip()
    return df


def create_authority_file(df, col_name, delimiter=';'):
    """
    creates an authority file of values in a given column (col_name)
    of a given DataFrame.
    The values in the cells of the column are delimited with a
    semicolon ;

    :param delimiter:
    :param df: the dataframe to work on
    :param col_name:
    :return: returns a dictionary of all named authorities in the column
    """

    # create an empty dictionary of authorities
    authority_list = {}

    for item, frame in df[col_name].iteritems():
        if not pd.isnull(frame):
            if ";" in str(frame):
                names = frame.split(delimiter)
                for name in names:
                    authority_list = create_authority(
                        df, item, name.strip(), authority_list)
            else:
                authority_list = create_authority(
                    df, item, str(frame).strip(), authority_list)

    return authority_list


def create_authority(df, index, frame, authority_list):
    """
    Creates a dictionary of all the authorities in a Dataframe

    :param authority_list: the entire authority dictionary of the DataFrame
    :param frame: the value of the cell
    :param index: index of the frame
    :rtype: dict
    :type df: pd.DataFrame
    :param df:
    """

    if frame not in authority_list:
        authority_list[frame] = {}
        authority_list[frame]['UNITID'] = []
    if "[" in frame:
        authority_list[frame]['role'] = find_role(frame)
    else:
        authority_list[frame]['role'] = ''

    authority_list[frame]['UNITID'].append(df.loc[index, 'UNITID'])

    return authority_list


def authority_Excelfile(df, column):
    """
    creates an authority datafames of a given column
    :param df:
    :param column:
    :return: the authority dataframe
    """
    df = df.reset_index()
    df_auth = pd.DataFrame.from_dict(create_authority_file(df[['UNITID', column]].dropna(how='any'),
                                                           column),
                                     orient='index')
    # create new column to count the number of occurrences
    df_auth['COUNT'] = df_auth['UNITID'].apply(lambda x: len(x))

    # split list of unitids into columns
    df_auth = pd.concat([df_auth['COUNT'],
                         df_auth['UNITID'].apply(pd.Series)], axis=1)
    return df_auth


def create_match_file(branch, collectionID, df_authority_file, df_auth, column):
    """

    :param branch:
    :param collectionID:
    :param df_authority_file:
    :param df_auth:
    :param column:
    """
    file_name = collectionID + '_' + column + '.xlsx'
    choices = list()
    match_results = dict()

    choices = choices + df_authority_file.index.tolist()

    if column == "ARCHIVAL_MATERIAL":
        for index, frame in df_authority_file.iterrows():
            choices.append(frame["ARCHIVAL_MATERIAL"])
            if str(frame['ARCHIVAL_MATERIAL_ALT_HEB']) == '':
                continue
            else:
                choices += frame['ARCHIVAL_MATERIAL_ALT_HEB']

    if column == "MEDIUM_FORMAT":
        choices = df_authority_file['MEDIA_FORMAT'].tolist()

    # fuzzy matching process
    for value in df_auth.index:
        from fuzzywuzzy import process
        match_results[value] = process.extract(value, choices, limit=4)

    new_match_results = dict()
    for key, value in match_results.items():
        choich, score = value[0]
        if str(score) != '100':
            new_match_results[key] = value

    # create a dataframe from the match results

    df_match_results = pd.DataFrame.from_dict(new_match_results)
    df_match_results = df_match_results.transpose()
    # df_match_results['Match'] = np.where('100' not in df['אפשרות1'], 'No', 'Yes')
    # df_match_results['Match'] =
    #                          ['No'if '100' in x  else 'Yes' for x in df_match_results[df_match_results.columns[0]]]
    if len(new_match_results) > 0:
        df_match_results.columns = ['אפשרות1', 'אפשרות2', 'אפשרותו3', 'אפשרות4']

    # split the tuple of the value and match score into 2 columns
    #     for cols in df_match_results.columns.values:
    #         df_match_results[['match'+cols, 'score'+cols]] = df[cols].apply(pd.Series)

    # create a list of sheet names
    sheets = list()
    sheets.append(collectionID + '_' + column + '_c')
    sheets.append(collectionID + '_' + column)
    sheets.append(column + '_match_results')

    combined_results = pd.concat([df_match_results, df_auth], axis=1)

    # create a list of dataframe that should
    dfs = list()
    dfs.append(combined_results)
    dfs.append(df_auth)
    dfs.append(df_match_results)

    write_excel(dfs, os.path.join(os.getcwd(), branch, collectionID, 'Authorities', file_name), sheets)


def is_corp(creator, df_corp_roles):
    """
        Checks if Creator is a Corporation (including role in brackets)
    :param creator: the creator to check
    :param df_corp_roles: the dataframe of the roles to check against
    :return: True if the creator is a Corporation, False if otherwise
    """
    if find_role(creator) in df_corp_roles.loc[:, 'CREATOR_CROPS_ROLE'].tolist():
        return True
    else:
        return False


def is_pers(creator, df_pers_roles):
    """
        Checks if Creator is a Person  (including role in brackets)
    :param creator: the creator to check
    :param df_pers_roles: the dataframe of the roles to check against
    :return: True if the creator is a Person, False if otherwise
    """
    if find_role(creator) in df_pers_roles.loc[:, 'CREATOR_PERS_ROLE'].tolist():
        return True
    else:
        return False


def find_role(name):
    """
    from a given name string value returns only the name.
    Ex. אפרתי משה [צלם]  returns only צלם

    :rtype: str
    :type name: str
    :return: returns the role of the creator
    :param name: the value of the a creator with a role
    """
    name = name.strip()
    if '[' in name:
        start = name.find('[') + 1
        return name[start:name.find(']')]
    else:
        return ""


def find_name(name):
    """"
    from a given name string value returns only the name.
    Ex. אפרתי משה [צלם]  returns only אפרתי משה

    :rtype: str
    :param name: the value of the a creator with a role
    :return: only the name of the given string
    """
    if "[" in name:
        start = name.find('[')
        return name[:start].rstrip()
    else:
        return name.rstrip()


def create_combined_creators(row):
    if row['FIRST_CREATOR_PERS'] != '':
        first_creator = str(row['FIRST_CREATOR_PERS']) + ' [' + str(row['TYPE_FIRST_CREATOR_PERS']) + ']'
    else:
        first_creator = str(row['FIRST_CREATOR_CORP']) + ' [' + str(row['TYPE_FIRST_CREATOR_CORP']) + ']'
    add_creators = str(row['ADD_CREATOR_PERS']) + ';' + str(row['ADD_CREATOR_CORPS'])

    combined_creators = f'{first_creator};{add_creators}'
    print(combined_creators)

    combined_creators.rstrip(';')
    combined_creators.lstrip(';')
    combined_creators.replace(';;', ';')

    return combined_creators


def map_role_to_relator(role, df, lang, mode='PERS'):
    """
        Map role to RDA Relator
    :param role: the original role to map
    :param df: the original
    :param lang: the language of the role
    :param mode: personalities or corporations
    :return: the dataframe with the mapped relator values
    """
    if mode == "PERS":
        if lang == 'heb':
            return df.loc[df[df["CREATOR_PERS_ROLE"] == role].index.item(), 'RELATOR_HEB']
        if lang == 'eng':
            return df.loc[df[df["CREATOR_PERS_ROLE"] == role].index.item(), 'RELATOR_ENG']
    elif mode == "CORPS":
        if lang == 'heb':
            return df.loc[df[df["CREATOR_CROPS_ROLE"] == role].index.item(), 'RELATOR_HEB']
        if lang == 'eng':
            return df.loc[df[df["CREATOR_CROPS_ROLE"] == role].index.item(), 'RELATOR_ENG']


def unique_creators(df):
    """
        Check that the value in COMBINED_CREATORS do not appear in the CONTROL_ACCESS columns: PERNAME, CORPNAME.
        Create a new combined creators column which contains only values that do not appear in PERNAME and
        CORPNAME columns/
    :param df:
    :return:
    """
    for index, frame in df.iterrows():
        l1 = str(frame['COMBINED_CREATORS']).split(";")
        creator_names = set([find_name(x) for x in l1])

        new_persnames = str(frame['PERSNAME']).split(';')
        new_persnames = list(filter(None, new_persnames))
        if len(new_persnames) > 0:
            new_persnames = [x for x in new_persnames if x not in creator_names]

        new_corpsnames = list(filter(None, str(frame['CORPNAME']).split(';')))
        if len(new_corpsnames) > 0:
            new_corpsnames = [x for x in new_corpsnames if x not in creator_names]

        df.loc[index, 'PERSNAME'] = ';'.join(new_persnames)
        df.loc[index, 'CORPNAME'] = ';'.join(new_corpsnames)

    return df


def map_relators(collection, df, authority_role_list):
    """

    :param authority_role_list:
    :param collection:
    :return:
    """
    df["COMBINED_CREATORS"] = df["COMBINED_CREATORS"].str.strip('\n')
    df["COMBINED_CREATORS"] = df["COMBINED_CREATORS"].str.rstrip('')

    # initiate empty lists
    temp_role_dict = defaultdict(list)
    roles = []
    role_not_found = []

    indexes_roles_not_found = []
    for index, row in df.iterrows():
        for creator in str(row['COMBINED_CREATORS']).strip().split(';'):
            temp_role = find_role(creator)
            roles.append(temp_role)
            if temp_role.strip() not in authority_role_list:
                indexes_roles_not_found.append((temp_role, index))

    for role_1, index_1 in indexes_roles_not_found:
        temp_role_dict[role_1].append(index_1)

    # Check which role does not appear in the authority file of creators role (persons and corporates)
    for role in roles:
        if role.strip() in authority_role_list:
            continue
        else:
            role_not_found.append(role)

    role_not_found = set(x for x in role_not_found if x != 'nan' or x != '')

    if len(indexes_roles_not_found) != 0:
        collection.logger.error(f"[CREATORS] Roles check - list of roles not found in roles authority list:"
                                f" {'; '.join(role_not_found)}.")
        print('\n', "role_not_found:", role_not_found)

    return roles, role_not_found, temp_role_dict


def correct_relators(collection: Collection, authority_role_list: list,
                     roles: list,  role_not_found: list,
                     temp_role_dict: dict):
    """

    :param collection:
    :param authority_role_list:
    :param roles:
    :param role_not_found:
    :param temp_role_dict:
    """

    def create_error_report():
        """

        """
        res = [(role,) + item for role in role_not_found for item in
               process.extract(role, authority_role_list, limit=5)]
        df_roles = pd.DataFrame(res, columns=['role', 'match', 'match score'])
        df_indexes_roles_not_found = pd.DataFrame.from_dict(temp_role_dict, orient='index').transpose()
        df_roles_sheets = ['roles not found', 'example_items']

        dfs_roles_list = [df_roles, df_indexes_roles_not_found]

        roles_check_file_name = collection.collection_id + '_roles_check' + collection.dt_now + '.xlsx'
        collection.logger.info(f"[ROLES] Creating {collection.collection_id} _roles_check_ "
                               f"{collection.dt_now}.xlsx file")

        write_excel(dfs_roles_list, os.path.join(collection.authorities_path, roles_check_file_name), df_roles_sheets)

    role_not_found = list(filter(None, role_not_found))

    if len(role_not_found) > 0:
        for role in role_not_found:
            collection.logger.info("[ROLES] Printing roles that are not found - and the options for corrections")
            pprint.pprint(str(role))
            pprint.pprint(process.extract(str(role), authority_role_list))
        pprint.pprint(set(role_not_found))
        create_error_report()

    else:
        collection.logger.info("[ROLES] all values matched to creator roles controlled vocabulary")


def clean_creators(collection: Collection) -> Collection:
    """

    :param collection:
    :return:
    """
    df = collection.full_catalog
    df = replace_NaN(df)

    authority_role_list = list(set(Authority_instance.df_creator_corps_role['CREATOR_CROPS_ROLE'])) + \
                          list(set(Authority_instance.df_creator_pers_role['CREATOR_PERS_ROLE']))

    creators_cols = [col for col in df.columns if "CREATOR" in col]
    if 'COMBINED_CREATORS' in creators_cols:
        creators_cols.remove('COMBINED_CREATORS')
        collection.logger.info("[CREATORS] COMBINED_CREATORS found: 1 creators column")
        for col in creators_cols:
            df = drop_col_if_exists(df, col)
        df = remove_duplicate_in_column(df, 'COMBINED_CREATORS')
    elif 'FIRST_CREATOR_PERS' in creators_cols:
        df['COMBINED_CREATORS'] = df[creators_cols].apply(create_combined_creators, axis=1)

    assert 'COMBINED_CREATORS' in list(df.columns), print(list(df.columns))

    roles, role_not_found, temp_role_dict = map_relators(collection, df, authority_role_list)
    df = clean_text_cols(df, 'COMBINED_CREATORS')
    df = strip_whitespace_af_semicolon(df, 'COMBINED_CREATORS')

    df = unique_creators(df)
    correct_relators(collection, authority_role_list, roles, role_not_found, temp_role_dict)
    collection.full_catalog = df

    return collection


def replace_wrong_values(df, col, test_list, map_dict):
    loop = len(test_list)
    index = 0


    while index < loop:
        term = test_list[index]
        choices = difflib.get_close_matches(term, list(map_dict.keys()), n=1, cutoff=0.6)
        print(choices)
        try:
            assert (type(choices) == list)
            assert (len(choices) >= 1)
            assert (len(difflib.get_close_matches(term, list(map_dict.keys()), n=1, cutoff=0.6)) > 0)
            new_term = difflib.get_close_matches(term, list(map_dict.keys()), n=1, cutoff=0.6)[0]
            while True:
                q = input("Replace the term [{}] with new term [{}]? type Y/n".format(term, new_term))
                if q.lower() == 'y':
                    df.replace(term, new_term, inplace=True)
                    break
                elif q.lower() == 'n':
                    break

                else:
                    print('please type Y/N')
        except:
            print("[{}] did not find value {} in values dictionary".format(col, term))
            pass

        index += 1
    return df


def check_values_against_cvoc(collection: Collection, col: str, mapping_dict: dict) -> list:
    """

    :param collection:
    :param df:
    :param col:
    :param mapping_dict:
    :return:
    """
    collection.logger.info(f"[{col.upper()}] Checking Value in {col} column against Controlled Vocabulary.")
    df = collection.full_catalog
    new_arch = list(filter(None, list(set(df[col].tolist()))))





    # declare empty list to save the values that don't exist in CVOC
    error_values = list()

    for item in new_arch:
        best, score = process.extractOne(item, list(mapping_dict.keys()))
        if best == item:
            continue
        else:
            error_values.append(item)
    # if all('' == s or s.isspace() for s in test_655):
    collection.logger.info("replace wrong values in Archival material")
    df = replace_wrong_values(df, col, error_values, Authority_instance.arch_mat_mapping_dict)
    collection.full_catalog = df

    return collection



