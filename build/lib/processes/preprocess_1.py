import sys
import timeit

from alphabet_detector import AlphabetDetector
from df2gspread import df2gspread as d2g

from VC_collections.fieldmapper import (
    field_mapper,
    level_mapper,
    final_fields_back_mapper,
    final_column_order,
)
from VC_collections.logger import initialize_logger

sys.path.insert(
    1, "C:/Users/Yaelg/Google Drive/National_Library/Python/VC_Preprocessing"
)
from VC_collections.project import ROOTID_finder, get_alma_sid
from VC_collections.columns import *
from VC_collections.value import *

from VC_collections.authorities import *
from VC_collections.Collection import (
    get_google_drive_credentials,
    export_entire_catalog,
    clean_catalog,
    retrieve_collection,
    connect_to_google_drive,
)


def check_missing_rootids(collection):
    logger = logging.getLogger(__name__)
    root_ids = list(set(collection.full_catalog["ROOTID"].tolist()))
    missing_root_ids = list()
    logger.info("[ROOTID's] checking for missing root ids in the index")
    for value in root_ids:
        if (
                value in collection.full_catalog.index
                or value == ""
                or value == collection.collection_id
        ):
            continue
        else:
            logger.error(
                "[ROOTID] Error - ROOTIDs that don't have corresponding unitid: "
                + str(value)
            )
            missing_root_ids.append(str(value))

    assert len(missing_root_ids) == 0, (
        ""
        "The following ROOT IDs do not appear in UNITID: \n {}".format(
            ", ".join(missing_root_ids)
        )
    )


def create_ROOT_id(df):
    logger = logging.getLogger(__name__)
    logger.info("Creating ROOTIDs column")
    df["ROOTID"] = df.index
    df.loc[df.index[1:], "ROOTID"] = df.loc[df.index[1:], "ROOTID"].apply(ROOTID_finder)

    # reset ROOTID of section record to null
    if len(df[df["LEVEL"] == "Section Record"]) == 1:
        df.loc[df["LEVEL"] == "Section Record", "ROOTID"] = ""

    elif len(df[df["LEVEL"] == "Section Record"]) > 1:
        logger.error(
            "[ROOTID] Error - There is more than one record with LEVEL='Section Record'"
        )
        print(df[df["LEVEL"] == "Section Record"])
        sys.exit()

    return df


def remove_unnecessary_cols(collection):
    if "סימול אב" in list(collection.df_catalog.columns) and "ROOTID" in list(
            collection.df_catalog.columns
    ):
        logger.info(f"Removing previous ROOTID column")
        collection.df_catalog = drop_col_if_exists(collection.df_catalog, "ROOTID")

    unnamed_columns = [col for col in list(collection.df_catalog) if "unnamed" in col]
    for col in unnamed_columns:
        logger.info(f"Removing {col} column from Catalog")
        drop_col_if_exists(collection.df_catalog, col)


def clean_headers(df):
    """

    :param df: the original dataframe
    :return:
    """
    headers = list(df.columns)
    headers = [x.upper().strip() for x in headers]
    df.columns = headers
    return df


def drop_cols_not_in_mapping(df):
    ad = AlphabetDetector()
    for header in list(df.columns):
        if ad.is_hebrew(header) and clean_text(header) not in list(field_mapper.keys()):
            df = drop_col_if_exists(df, header)

        if ad.is_latin(header) and header not in list(field_mapper.values()):
            df = drop_col_if_exists(df, header)
    return df


def remove_definition_row(collection):
    if collection.df_catalog["UNITID"].str.contains("שדה חובה").any():
        logger.info(f"Removing definition row from catalog table, at {datetime.now()}")
        collection.df_catalog.drop(collection.df_catalog.index[0], inplace=True)

    if collection.df_collection["UNITID"].str.contains("שדה חובה").any():
        logger.info(
            f"Removing definition row from collection table, at {datetime.now()}"
        )
        collection.df_collection.drop(collection.df_collection.index[0], inplace=True)

    return collection


def map_level_to_eng(df):
    return df.replace({"LEVEL": level_mapper})


def check_mandatory_cols_v1(df):
    mandatory_cols_version1 = [
        "UNITID",
        "LEVEL",
        "UNITITLE",
        "EXTENT",
        "CATALOGUER",
        "DATE_CATALOGING",
        "COMBINED_CREATORS",
    ]

    #     assert (mandatory_cols in list(df.columns)), "not all mandatory columns exist in table"
    for col in mandatory_cols_version1:
        assert col in list(df.columns), f"Mandatory element [{col}] no in table"
        mask = df[col] == ""
        assert len(df[mask]) == 0, (
            f"Mandatory element [{col}] is empty in {len(df[mask])} rows, "
            f"{df.loc[df[mask].index.values, 'UNITID']}"
        )


def check_mandatory_cols_v2(df):
    creators_cols = [x for x in list(df.columns) if "CREATOR" in x]
    mandatory_cols_version2 = [
                                  "UNITID",
                                  "LEVEL",
                                  "UNITITLE",
                                  "EXTENT",
                                  "CATALOGUER",
                                  "DATE_CATALOGING",
                              ] + creators_cols

    #     assert (mandatory_cols in list(df.columns)), "not all mandatory columns exist in table"
    for col in mandatory_cols_version2:
        assert col in list(df.columns), "Mandatory element [{}] no in table".format(col)


def check_unitid(df):
    df = df.reset_index()
    logger = logging.getLogger(__name__)

    df["UNITID"] = df["UNITID"].apply(whiteSpaceStriper)
    dup_unitid = dupCheck(df, "UNITID")

    assert (
            type(dup_unitid) == str
    ), f'[UNITID] These UNITID reoccur: ", {dup_unitid.UNITID.unique}'
    logger.info(f"[UNITID] no non-unique values found")

    df = df.set_index("UNITID")

    return df


def clean_record_title(df):
    # replace first comma in title to hyphen
    logger = logging.getLogger(__name__)
    logger.info("[UNITITLE] Replacing first comma in title with hyphen")
    df.UNITITLE = df.UNITITLE.astype(str)

    df["UNITITLE"] = df["UNITITLE"].apply(lambda x: x.replace(",", " -", 1))
    return df


def create_authorities_report(collection, authority_type):
    df = collection.full_catalog

    if authority_type == "PERS":
        col = "PERSNAME"
        combined_authority_col = "COMBINED_CREATORS_" + authority_type
        authority_col = "CREATOR_" + authority_type
    elif authority_type == "CORPS":
        col = "CORPNAME"
        combined_authority_col = "COMBINED_CREATORS_" + authority_type
        authority_col = "CREATOR_" + authority_type
    elif authority_type == "GEO":
        col = "GEOGNAME"
        combined_authority_col = "GEOGNAME"
        authority_col = "GEOGNAME"
    elif authority_type == "WORKS":
        col = "WORKS"
        combined_authority_col = "WORKS"
        authority_col = "WORKS"

    if col not in list(df.columns):
        return collection

    logger.info(f"[{col}] Creating a dataframe for creators which are {authority_type}")

    try:
        col in list(df.columns)

    except:
        sys.stderr(f"There is no [{col}] column in full catalog dataframe")
        return collection

    df = remove_duplicate_in_column(df, col)

    df = df.reset_index()

    if combined_authority_col in df.columns.values:
        df_creator = pd.DataFrame.from_dict(
            create_authority_file(
                df[["UNITID", combined_authority_col]].dropna(how="any"),
                combined_authority_col,
            ),
            orient="index",
        )
    else:
        df_creator = pd.DataFrame.from_dict(
            create_authority_file(
                df[["UNITID", authority_col]].dropna(how="any"), authority_col
            ),
            orient="index",
        )

    # create a dataframe for personalities in the access points (persname) which are persons
    df_access = pd.DataFrame.from_dict(
        create_authority_file(df[["UNITID", col]].dropna(how="any"), col),
        orient="index",
    )

    df_creator = df_creator.reset_index()
    df_access = df_access.reset_index()

    df_creator["Name"] = df_creator["index"].apply(
        lambda x: find_name(x).strip() if isinstance(x, str) else x
    )
    df_access["Name"] = df_access["index"].apply(
        lambda x: find_name(x).strip() if isinstance(x, str) else x
    )
    # df_access["Role"] = df_access["index"].apply(
    #     lambda x: find_role(x).strip() if isinstance(x, str) else x
    # )
    df_creator["Type"] = "CREATOR"
    df_access["Type"] = col

    df_authority = pd.concat([df_creator, df_access], sort=True)
    df_authority["Count"] = df_authority.apply(lambda row: len(row["UNITID"]), axis=1)
    df_authority.where(df_authority["Name"] != '').dropna(how="all")

    df_authority = pd.concat(
        [
            df_authority["Name"],
            df_authority["Role"],
            df_authority["Count"],
            df_authority["UNITID"].apply(pd.Series),
        ],
        axis=1,
    )

    unique_authority_filename = collection.authorities_path / (
            collection.collection_id
            + "_"
            + authority_type.lower()
            + "_unique_"
            + collection.dt_now
            + ".xlsx"
    )
    authority_occurrences_filename = collection.authorities_path / (
            collection.collection_id
            + "_"
            + authority_type.lower()
            + "_report_"
            + collection.dt_now
            + ".xlsx"
    )
    df_authority = df_authority.reset_index(drop=True)
    logger.info(
        f"[Authorities - {authority_type}] creating report for unique {authority_col},"
        f" file name: {unique_authority_filename}"
    )
    write_excel(
        pd.DataFrame(df_authority.Name.unique()),
        unique_authority_filename,
        "unique_" + authority_type.lower(),
    )

    # sort by index (names of pers) and then by count (number of occurrences)
    df_authority = df_authority.reset_index(drop=True)
    df_authority = df_authority.set_index("Name")
    df_authority = df_authority.sort_values(
        by=["Name", "Count"], ascending=[True, False]
    )
    df_authority = drop_col_if_exists(df_authority, "index")
    write_excel(
        df_authority, authority_occurrences_filename, authority_type + "_report"
    )

    df = df.set_index("UNITID")
    collection.full_catalog = df

    return collection


def rename_header_back(df):
    df_final = df.rename(columns=final_fields_back_mapper)
    return df_final


def order_columns(full_catalog):
    full_catalog = full_catalog[final_column_order]
    return full_catalog


def unify_columns_with_master_template(full_catalog):
    for field in final_column_order:
        if field not in list(full_catalog.columns):
            full_catalog[field] = ""
    return full_catalog


def create_final_file(collection):
    collection.full_catalog = rename_header_back(collection.full_catalog)
    collection.full_catalog.index.name = "סימול"

    collection.full_catalog = unify_columns_with_master_template(
        collection.full_catalog
    )
    collection.full_catalog = order_columns(collection.full_catalog)
    return collection


def update_df_in_gdrive(collection, worksheet_name="קטלוג סופי", copy=False):
    credentials = get_google_drive_credentials()
    if worksheet_name == "קטלוג סופי":
        d2g.upload(
            collection.full_catalog.applymap(str),
            collection.google_sheet_file_id,
            worksheet_name,
            credentials=credentials,
            row_names=True,
        )
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(collection.google_sheet_file_id)
        if 'מספרי מערכת חסרים' in sh.worksheets():
            sh.del_worksheet('מספרי מערכת חסרים')
        if copy:
            client = connect_to_google_drive()
            spreadsheet = client.copy(
                collection.google_sheet_file_id,
                collection.collection_id + "_Final_to_Alma_" + collection.dt_now,
            )
            collection.google_sheet_file_id = spreadsheet.id
            collection.create_catalog_metadata_file()
    else:
        d2g.upload(
            collection.missing_records.applymap(str),
            collection.google_sheet_file_id,
            worksheet_name,
            credentials=credentials,
            row_names=True,
        )


# TODO
def add_MMSIDs_to_full_catalog(collection):
    file_path = collection.aleph_custom04_path / (
            collection.collection_id + "_alma_sysno.xlsx"
    )
    try:
        df_mmsid = pd.DataFrame(pd.ExcelFile(file_path).parse("Sheet1"))
    except:
        print(f"There is no file in path: {file_path}")

    return collection


def add_normal_dates_to_section_record(df, collection_id):
    df = df.replace(r"^\s*$", np.nan, regex=True)
    if not column_exists(df, "DATE_START") and not column_exists(df, "DATE_START"):
        df["DATE_START"] = ''
        df["DATE_END"] = ''
    if pd.isnull(df.loc[collection_id, "DATE_START"]) and pd.isnull(
            df.loc[collection_id, "DATE_END"]
    ):
        date = df.loc[collection_id, "DATE"]
        pattern = re.compile(r"\d{4}")
        years = re.findall(pattern, date)
        years = sorted([int(year) for year in years])
        df.loc[collection_id, "DATE_START"] = years[0]
        df.loc[collection_id, "DATE_END"] = years[1]

    return df


def fill_default_ACCESSRESTIRCT(df):
    """
        Function adds default value to ACCESSRESTRICT - by condition:
        if LEVEL = תיק or LEVEL = פריט and the value in NaN,
        then fill in אין מגבלות פרטיות.

        All records of level file and item need to have a mandatory Access restrict value.

    :param df: original
    :return:
    """

    mask = pd.isna(df["ACCESSRESTRICT"]) & (
            (df["LEVEL"] == "תיק") | (df["LEVEL"] == "פריט")
    )
    df.loc[df[mask].index, "ACCESSRESTRICT"] = "אין מגבלות פרטיות"
    return df


def check_date_columns(df):
    mask = (
            (df["DATE_START"] == "")
            | (df["DATE_END"] == "")
            | (df["DATE_START"].isna())
            | (df["DATE_END"].isna())
    )
    test_df = df[mask]
    if len(test_df) != 0:
        for index, row in test_df.iterrows():
            if row["DATE"] == "":
                sys.stderr(f"[ERROR]  No DATE Values! Please check data at index: {index}")
            else:
                try:
                    early_date, late_date = extract_years_from_text(row["DATE"])
                except:
                    sys.stderr.write(f"Problem with index {index}")

                if early_date is not None and late_date is not None:
                    df.loc[index, "DATE_START"] = early_date
                    df.loc[index, "DATE_END"] = late_date
    return df


def check_cataloging_date(df: pd.DataFrame) -> pd.DataFrame:
    """

    :param df:
    :return:
    """

    mask = df['CATALOGING_DATE'].apply(pd.to_datetime, errors='coerce').isnull().any()
    print(df.loc[:, mask])

    return df


def main():
    start_time = timeit.default_timer()

    """ get branch and  collection ID to work on and create a Collection instance """
    # CMS, branch, collection_id = get_branch_colletionID()
    # collection = Collection(CMS, branch, collection_id)

    collection = retrieve_collection()

    """ initialize logger for the logging file for that collection"""
    initialize_logger(collection.branch, collection.collection_id)
    logger = logging.getLogger(__name__)
    logger.info(
        f"\n Starting new preprocess of {collection.collection_id}, at: {datetime.now()}"
    )

    logger.info(
        f"[HEADERS] Dropping columns not in mapping for {collection.collection_id} Catalog, at: {datetime.now()}"
    )
    collection.full_catalog = drop_cols_not_in_mapping(collection.full_catalog)

    collection = clean_tables(collection)
    if hasattr(collection, "full_catalog"):
        collection.full_catalog = clean_catalog(collection.full_catalog)

    logger.info(
        f"[HEADERS] Checking that mandatory columns exists in table for {collection.collection_id}(full_catalog)."
    )
    if "FIRST_CREATOR_PERS" in list(collection.full_catalog.columns):
        check_mandatory_cols_v2(collection.full_catalog.reset_index())
    elif "COMBINED_CREATORS" in list(collection.full_catalog.columns):
        check_mandatory_cols_v1(collection.full_catalog.reset_index())
    elif "ADD_CREATORS" in list(collection.full_catalog.columns):
        collection.full_catalog = split_creators_by_type(
            collection.full_catalog, "ADD_CREATORS"
        )

    logger.info(
        f"[LEVEL] Mapping Level values of {collection.collection_id} from hebrew to english."
    )
    collection.full_catalog = map_level_to_eng(collection.full_catalog)

    logger.info(f"[UNITID] checking for duplicate values, at: {datetime.now()}")
    collection.full_catalog = check_unitid(collection.full_catalog)

    assert collection.full_catalog.index.name == "UNITID"

    collection.full_catalog = create_ROOT_id(collection.full_catalog)

    logger.info(f"[ACCESSRESTRICT] add default value for ACCESSRESTIRCT field")
    collection.full_catalog = fill_default_ACCESSRESTIRCT(collection.full_catalog)

    if "TO_DELETE" in list(collection.full_catalog.columns):
        logger.info(
            "[TO_DELETE] Changing the ROOTID to collectionID for records which are about to be deleted"
        )
        collection.full_catalog.loc[
            collection.full_catalog["TO_DELETE"] == "כן", "ROOTID"
        ] = collection.collection_id

    logger.info("[UNITITLE] Cleaning records title")
    collection.full_catalog = clean_record_title(collection.full_catalog)

    logger.info("[DATES] Adding normal date to Section Record")
    collection.full_catalog = add_normal_dates_to_section_record(
        collection.full_catalog, collection.collection_id
    )

    logger.info("[DATES] Validating dates")
    collection.full_catalog = check_date_columns(collection.full_catalog)

    logger.info(
        f"[COMBINED_CREATORS] CREATING COMBINED CREATORS for {collection.collection_id} , at: {datetime.now()}"
    )
    collection = clean_creators(collection)

    logger.info(
        f"[COMBINED_CREATORS] Splitting COMBINED_CREATORS into COMBINED_CREATORS_PERS"
        f"and COMBINED_CREATORS_CORPS columns according to roles"
    )
    collection.full_catalog = split_creators_by_type(
        collection.full_catalog, "COMBINED_CREATORS"
    )

    collection = create_authorities_report(collection, "PERS")
    collection = create_authorities_report(collection, "CORPS")
    collection = create_authorities_report(collection, "GEO")
    collection = create_authorities_report(collection, "WORKS")

    logger.info(f"[ARCHIVAL_MATERIAL] Starting to work on ARCHIVAL_MATERIAL column")
    collection.full_catalog = check_values_against_cvoc(
        collection.full_catalog,
        "ARCHIVAL_MATERIAL",
        Authority_instance.arch_mat_search_dict,
    )
    logger.info(f"[ARCHIVAL_MATERIAL] Creating Archival Material Match File")
    create_match_file(
        collection,
        Authority_instance.df_arch_mat_auth,
        authority_Excelfile(collection.full_catalog, "ARCHIVAL_MATERIAL"),
        "ARCHIVAL_MATERIAL",
    )

    logger.info(f"[MEDIUM_FORMAT] Starting to work on MEDIUM_FORMAT column")
    collection.full_catalog = check_values_against_cvoc(
        collection.full_catalog,
        "MEDIUM_FORMAT",
        Authority_instance.media_format_mapping_dict,
    )
    logger.info(f"[MEDIUM_FORMAT] Creating Media/Format Match File")
    create_match_file(
        collection,
        Authority_instance.df_media_format_auth,
        authority_Excelfile(collection.full_catalog, "MEDIUM_FORMAT"),
        "MEDIUM_FORMAT",
    )

    # logger.info(f"[DATE_CATALOGING] Checking and Validating DATE_CATALOGING column")
    # collection.full_catalog = check_cataloging_date(collection.full_catalog)

    logger.info("Final file: creating final file")
    collection = create_final_file(collection)

    collection.full_catalog, df_alma, df_missing_records_in_alma = get_alma_sid(
        collection.aleph_custom04_path,
        collection.collection_id,
        collection.full_catalog,
    )

    if df_missing_records_in_alma is not None:
        logger.error("Not all records have MMS ID - please create alma records for missing MMS IDs!")

        collection.missing_records = drop_col_if_exists(df_missing_records_in_alma.reset_index().set_index("סימול"),
                                                        '001')
        update_df_in_gdrive(collection, worksheet_name="מספרי מערכת חסרים", copy=False)

    logger.info(
        f"updating the preprocessed DataFrame in Google Sheets - "
        f"as final copy: {collection.collection_id}_Final_to_alma_{collection.dt_now}"
    )
    update_df_in_gdrive(collection, copy=True)

    collection.temp_preprocess_file()

    export_entire_catalog(collection, collection.full_catalog, stage="FINAL")

    elapsed = timeit.default_timer() - start_time
    logger.info(f"Execution Time: {elapsed}")

    # collection = add_MMSIDs_to_full_catalog(collection)
    collection.temp_preprocess_file(stage="PRE")


if __name__ == "__main__":
    main()
