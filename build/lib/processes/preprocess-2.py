import sys
import time
import timeit

from VC_collections import marc
from VC_collections.logger import initialize_logger

sys.path.insert(
    1, "C:/Users/Yaelg/Google Drive/National_Library/Python/VC_Preprocessing"
)
from VC_collections.value import *

from VC_collections.authorities import *
from VC_collections.Collection import retrieve_collection


def is_collection_postprocess1(collection):
    try:
        return type(collection.df_final_data) == pd.DataFrame
    except:
        return False


def main():
    start_time = timeit.default_timer()
    collection = retrieve_collection()

    """ initialize logger for the logging file for that collection"""
    initialize_logger(collection.branch, collection.collection_id)
    logger = logging.getLogger(__name__)
    logger.info(
        f"\n Starting new preprocess of {collection.collection_id}, at: {datetime.now()}"
    )

    logger.info(
        f'\nStarting new preprocess {"/".join(str(sys.modules[__name__])[:-1].split("/")[-3:])} of '
        f"{collection.collection_id}, at: {datetime.now()}"
    )
    time.sleep(0.5)

    if is_collection_postprocess1(collection):
        pass
    else:
        logger.error(
            f"The {collection.collection_id} Catalog did not pass the preprocessing-1 pipe!"
            f"please run preprocess_1.py for this Catalog "
        )
        sys.exit()

    df = collection.df_final_data.T.drop_duplicates().T
    df.rename(columns={df.columns[0]: "mms_id"}, inplace=True)

    # create 351 (רמת תיאור)
    logger.info(f"[351] Creating  MARC 351 - LEVEL OF DESCRIPTION")
    collection.df_final_data = marc.create_MARC_351_LDR(collection.df_final_data)

    # create MARC 911 and 093 field for Call Number (סימול פרויקט)
    logger.info("[911/093] Creating 911/093 MARC field for Call Number")
    collection.df_final_data = marc.create_MARC_093(collection.df_final_data)
    collection.df_final_data.index = collection.df_final_data["093_1"].apply(
        lambda x: x[x.find("$$c") + 3: x.find("$$d")]
    )

    # # Add MMS id to catalog (מספר מערכת עלמא)
    # logger.info("[001] Add MMS id to catalog")
    # collection.df_final_data = drop_col_if_exists(collection.df_final_data, 'mms_id')
    # collection.df_final_data, df_alma = project.get_alma_sid(
    #     collection.aleph_custom04_path,
    #     collection.collection_id,
    #     collection.df_final_data,
    # )

    # create 008
    logger.info(f"[008] Creating  MARC 008 field")
    collection.df_final_data = marc.create_MARC_initial_008(collection.df_final_data)

    # create 520 (תיאור)
    logger.info(f"[520] Creating  MARC 520 - SCOPE AND CONTENT")
    collection.df_final_data = marc.create_MARC_520(collection.df_final_data)

    # create 245 (כותרת)
    logger.info(f"[245] Creating  MARC 245 - UNITITLE")
    collection.df_final_data = marc.create_MARC_245(collection.df_final_data)

    # create 110 and 100 (FIRST CREATORS CORPS and PERS) (יוצר ראשון - איש/ יוצר ראשון = מוסד)
    collection.df_final_data = marc.create_MARC_100_110(collection.df_final_data)

    # create 300 (EXTENT) (היקף)
    logger.info("[MARC 300] Creating  MARC 300 - EXTENT ")
    collection.df_final_data = marc.create_MARC_300(collection.df_final_data)

    # create 700 and 710 (added creators PERS and CORPS) (יוצרים נוספים - אישים/יוצרים נוספים - מוסד)
    collection.df_final_data = marc.create_MARC_700_710(collection.df_final_data)

    # create 655 (ARCHIVAL_MATERIAL) (סוג חומר)
    logger.info("[MARC 655] Creating  MARC 655 - ARCHIVAL MATERIAL ")
    collection.df_final_data = marc.create_marc_655(collection.df_final_data)

    # create 041 (LANGUAGE) (שפה)
    logger.info("[MARC 041] Creating  MARC 041 - LANGUAGE")
    collection.df_final_data = marc.create_MARC_041(collection.df_final_data)

    ####################################################
    ### CREATE  COPYRIGHT FIELDS WITH DEFAULT VALUES ###
    ### fields: 939, 903, 952
    ####################################################
    logger.info("[MARC 939, 903, 952] Creating default copyright fields")

    collection.df_final_data = marc.create_MARC_defualt_copyright(
        collection.df_final_data
    )

    # create 255 - scale field
    logger.info("[MARC 255] Creating  MARC 255 - SCALE")
    collection.df_final_data = marc.create_MARC_255(collection.df_final_data)

    # create 260 (DATE fields, and PUBLICATION_COUNTRY) (מדינת פרסום, תאריך מנורמל מוקדם, תאריך מנורמל מאוחר)
    logger.info("[MARC 260] Creating  MARC 260 $g $e - DATE (free text), and publication country."
                " Updates MARC 008")

    collection.df_final_data = marc.create_MARC_260(
        collection.df_final_data,
        "מדינת הפרסום/הצילום",
        ["תאריך מנורמל מוקדם", "תאריך מנורמל מאוחר", "תאריך חופשי"],
    )

    logger.info("[MARC 952] Creating MARC 952 - Privacy")
    collection.df_final_data = marc.create_MARC_952(collection.df_final_data)

    # add 597 (CREDIT)
    collection = marc.add_MARC_597(collection)
    logger.info("[MARC 597] Creating MARC 597 - CREDITS")

    # create 921, 933 (CATALOGUER, CATALOGING DATE)
    logger.info("[MARC 921/933] Creating MARC 921/933 - CATALOGUERS and CATALOGUING DATE")

    collection.df_final_data = marc.create_MARC_921_933(collection.df_final_data)

    # create 500 (NOTES) and other fields:
    logger.info("[MARC 500] Creating MARC 500 - NOTES")
    collection.df_final_data = marc.create_MARC_500(collection.df_final_data)
    collection.df_final_data = marc.create_MARC_500s_4collection(
        collection.df_final_data
    )

    # create 999 (Default values: NOULI, NOOCLC, ARCHIVE)
    logger.info(
        "[MARC 999] initializing MARC 999 with constant values: NOULI, NOOCLC, ARCHIVE"
    )
    collection.df_final_data = marc.create_MARC_999(collection.df_final_data)

    # create BAS=VIS, in alma BAS -> 906
    logger.info("[MARC 906] Adding BAS = VIS - in Alma 906")
    collection.df_final_data = marc.create_MARC_BAS(collection.df_final_data)

    # create FMT
    collection.df_final_data = marc.create_MARC_FMT(collection.df_final_data)

    # create OWN (Default value: NNL)
    logger.info(
        "[MARC 948] initializing MARC 948 - formerly Own with constant values: NNL"
    )
    collection.df_final_data = marc.create_MARC_948(collection.df_final_data)

    # create 773 (former LKR)
    logger.info("[MARC 773] Creating MARC 773 - the hierarchical link field")
    collection.df_final_data = marc.create_MARC_773(collection.df_final_data)

    # create 336
    logger.info("[MARC 336] Creating MARC RDA 336 ")

    collection.df_final_data, df_explode_336 = marc.create_MARC_336(
        collection.df_final_data
    )
    df2 = pd.concat([collection.df_final_data, df_explode_336], axis=1)

    # create 337 338
    logger.info("[MARC 337/338] Creating MARC RDA 337/338 ")
    collection.df_final_data = marc.create_MARC_337_338(collection.df_final_data)

    # create 534
    logger.info("[MARC 534] Creating MARC 534 - MEDIA FORMAT ")
    collection.df_final_data = marc.create_MARC_534(collection.df_final_data)

    # create MARC 590
    logger.info("[MARC 590] Creating MARC  590  - HIDDEN NOTES")
    collection.df_final_data = marc.create_MARC_590(collection.df_final_data)

    # create MARC 561
    logger.info("[MARC 561] Creating MARC  561 - Ownership and Custodial History")
    collection.df_final_data = marc.create_MARC_561(collection.df_final_data)

    collection.temp_preprocess_file(stage="POST")

    #  ADD 907 (#Rossetta link)
    logger.info("[MARC 907] Recreating MARC 907 - adding the Rossetta field, link to the digital object (if exists)")
    collection = marc.add_MARC_907(collection)

    # recreate 035 MARC field from the ROS\[collection_id]_907.xml file
    logger.info("[MARC 035] Recreating MARC 035 - for records which are migrated from Aleph")
    collection = marc.add_MARC_035(collection)

    # create MARC 650 for project branches
    logger.info("[MARC 650] create MARC 650 subject heading according to collection's branch")
    collection = marc.create_MARC_650_branch(collection)

    # create MARC Catalog
    marc.export_MARCXML_final_table(collection)
    collection.create_marc_seq_file()

    #

    ###############################################
    ### export final dataframe to check process ###
    ###############################################
    # collection.temp_preprocess_file(stage="POST")

    ###############################################
    ###      how much time the process ran?     ###
    ###############################################
    elapsed = timeit.default_timer() - start_time
    logger.info(f"Execution Time: {elapsed}")


if __name__ == "__main__":
    main()
