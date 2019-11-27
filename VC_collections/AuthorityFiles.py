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
    Date: 02/08/2019 00:25
    
    $
"""

from pathlib import Path

import gspread
import numpy as np
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

from .files import create_df_from_gs


def create_df_from_gs(spreadsheet, worksheet):
    """
    Function gets name of worksheet from a Google Sheet Spreadsheet, and returns it
    as a pandas DataFrame
    :param spreadsheet:
    :param worksheet: The name of the worksheet
    :return: df - pandas Dataframe of the worksheet
             cols - list of column names
    """
    # create a dataframe from the given worksheet
    sheet = spreadsheet.worksheet(worksheet)
    dict_gs = sheet.get_all_records(head=1)
    #     pprint.pprint(dict_gs)
    df = pd.DataFrame(dict_gs)
    cols = list(dict_gs[1].keys())
    #     print(cols)

    # remove empty rows
    df.replace(np.nan, '', inplace=True)

    return df, cols


def order_media_format(df_media_format_auth):
    # drop first row
    # df_media_format_auth = df_media_format_auth.reindex(df_media_format_auth.index.drop(0))
    df_media_format_auth = df_media_format_auth.rename(columns={'מדיה MEDIA + פורמט': 'MEDIA_FORMAT', 'מדיה': 'MEDIA',
                                                                'קוד מונח': 'MEDIA_ID', 'פורמט': 'FORMAT'})

    df_media_format_auth['TEMP'] = df_media_format_auth.MEDIA_FORMAT.str.split('--')

    # expand df.media_format into its own dataframe
    media_format = df_media_format_auth['TEMP'].apply(pd.Series)

    # rename each variable
    media_format = media_format.rename(columns={0: 'MEDIA', 1: 'FORMAT'})
    # media_format = media_format.dropna()

    # join the tags dataframe back to the original dataframe
    df_media_format_auth = pd.concat([df_media_format_auth[:], media_format[:]], axis=1)
    # df_media_format_auth = df_media_format_auth.dropna()

    df_media_format_auth = df_media_format_auth.drop('TEMP', 1)

    media_format_auth = df_media_format_auth

    media_format_auth_mapping = media_format_auth.loc[:,
                                ['MARC21 534', 'MEDIA_FORMAT', 'MARC 338 rdacarrier', 'MARC 337 rdamedia']]

    media_format_mapping_dict = pd.Series(media_format_auth_mapping['MARC21 534'].values,
                                          index=media_format_auth['MEDIA_FORMAT'].values).to_dict()

    return media_format_auth, media_format_mapping_dict


def order_archival_material(df_arch_mat_auth):
    archiv_mat_cols = {
        'סוג חומר': 'ARCHIVAL_MATERIAL',
        'מונח סוג חומר רמה 1': 'skosxl:broader@prefLabel',
        'מונח סוג חומר רמה 2': 'skosxl:prefLabel@lang=heb',
        'הסבר למונח': 'skosxl:scopeNote@lang=heb',
        'ערכים לשדות כותרת ותיאור *ערכים אלו אינם מופיעים במקור נתונים': 'ARCHIVAL_MATERIAL_ALT_HEB',
        'מדינת הפרסום/צילום': 'country_needed',
        'סוג יוצר איש': 'creator_pers',
        'סוג יוצר תאגיד': 'creator_corp'
    }

    # rename columns names of Archival material table
    df_arch_mat_auth = df_arch_mat_auth.rename(columns=archiv_mat_cols)
    # create a dictionary for mapping
    df_arch_mat_mapping = df_arch_mat_auth.loc[
        df_arch_mat_auth.index, ['ARCHIVAL_MATERIAL', 'MARC21 655 7', 'rdacontent 336']]
    arch_mat_mapping_dict = pd.Series(df_arch_mat_mapping['MARC21 655 7'].values,
                                      index=df_arch_mat_mapping.ARCHIVAL_MATERIAL.values).to_dict()

    return df_arch_mat_auth, arch_mat_mapping_dict


class Authority:
    BASE_PATH = Path.cwd()

    def __init__(self):
        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds']
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name('google_drive_api/client_secret.json', scope)
        except OSError as e:
            creds = ServiceAccountCredentials.from_json_keyfile_name(r'C:\Users\Yaelg\Google '
                                                                     r'Drive\National_Library\Python\VC_Preprocessing'
                                                                     r'\google_drive_api\client_secret.json', scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(
            "https://docs.google.com/spreadsheets/d/1736sL9unbiOMbcrIYgSkCSvhU2-LCthSLVtYLPSpZ98")

        # fetch all tables
        df_media_format_auth, media_cols = create_df_from_gs(spreadsheet, 'מדיה פורמט')
        df_arch_mat_auth, archival_cols = create_df_from_gs(spreadsheet, 'סוג חומר')
        df_arch_mat_mapping = df_arch_mat_auth.loc[:, ['ARCHIVAL_MATERIAL', 'MARC21 655 7', 'rdacontent 336']]
        df_creator_corps_role, corps_role_cols = create_df_from_gs(spreadsheet, 'סוגי ארגונים-תפקידים')
        df_creator_corps_role = df_creator_corps_role.rename(columns={'סוגי ארגונים': 'CREATOR_CROPS_ROLE'})
        df_creator_pers_role, pers_role_cols = create_df_from_gs(spreadsheet, 'סוגי אישים-תפקידים')
        df_creator_pers_role = df_creator_pers_role.rename(
            columns={'מילות מפתח - סוגי אישים בפרוייקט': 'CREATOR_PERS_ROLE'})
        df_catalogers, cataloger_cols = create_df_from_gs(spreadsheet, 'שם הרושם')
        df_catalogers = df_catalogers.set_index('שם הרושם')
        cataloger_name_mapper = df_catalogers.to_dict()['קיצור אלף']

        df_countries, countries_cols = create_df_from_gs(spreadsheet, 'מדינת פרסום')
        roles_dict = {"pers_roles": df_creator_pers_role["CREATOR_PERS_ROLE"].tolist(),
                      "corps_roles": df_creator_corps_role["CREATOR_CROPS_ROLE"].tolist()}

        df_languages, languages_cols = create_df_from_gs(spreadsheet, 'שפה')
        df_languages = df_languages.set_index('שם שפה עברית')

        df_level, level_cols = create_df_from_gs(spreadsheet, 'רמת תיאור')

        self.df_media_format_auth, self.media_format_mapping_dict = order_media_format(df_media_format_auth)
        self.df_arch_mat_auth, self.arch_mat_mapping_dict = order_archival_material(df_arch_mat_auth)
        self.df_arch_mat_mapping = df_arch_mat_mapping
        self.df_creator_corps_role = df_creator_corps_role
        self.df_creator_pers_role = df_creator_pers_role
        self.df_cataloguers = df_catalogers
        self.cataloger_name_mapper = cataloger_name_mapper
        self.df_countries = df_countries
        self.df_languages = df_languages

        self.roles_dict = roles_dict
        self.df_level = df_level


if __name__ != '__main__':
    Authority_instance = Authority()
