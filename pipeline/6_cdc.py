import adsToolBox as ads

logger = ads.Logger(ads.Logger.DEBUG, "adsLogger")
env = ads.env(logger, 'C:/Users/mvann/Desktop/ADS/Projects/Demo/.env')
ads.set_timer(True)

connection_string = f"mssql+pymssql://{env.AFT_USER}:{env.AFT_PWD}@{env.AFT_HOST}:{env.AFT_PORT}/{env.AFT_DB}"
config_json = """{
    "staging_area" : {
        "table" :         {"schema" : "nx_staging",  "name" : "AAA_test_pbx"},
        "pk_table" :      {"schema" : "nx_staging",  "name" : "AAA_test_pbx_pk"},
        "view" :          {"schema" : "nx_staging",  "name" : "v_AAA_test_pbx"},
        "cdc_table" :     {"schema" : "nx_cdc",      "name" : "AAA_test_pbx"}
    },
    "persistent_area" : {
        "table" :         {"schema" : "nx_business", "name" : "AAA_test_pbx"},
        "history_table" : {"schema" : "nx_business", "name" : "AAA_test_pbx_histo"},
        "view" :          {"schema" : "dbo",         "name" : "AAA_test_pbx"}
    },
    "mapping" : [
        {"position" :  1, "persistent_column" : "id",   "staging_column_or_expression" : "id",   "datatype" : "int",         "is_pk" : true,  "use_for_cdc" : false},
        {"position" :  2, "persistent_column" : "col1", "staging_column_or_expression" : "col1", "datatype" : "varchar(10)", "is_pk" : false, "use_for_cdc" : true },
        {"position" :  3, "persistent_column" : "col2", "staging_column_or_expression" : "col2", "is_pk" : false, "use_for_cdc" : true }
    ],
    "sync" : {
        "mode" : "scd2",
        "action_on_table" : {
            "truncate" : false,
            "delete_rows" : false,
            "delete_rows_condition" : null
        },
        "persistent_table_filter_expression" : null,
        "deleted_rows" : {
            "ignore" : false,
            "soft_delete" : false,
            "use_pk_table" : false
        },
        "technical_columns" : {
            "pk_hash" :           {"persistent_column" : "nx_pk_hash"},
            "row_hash" :          {"persistent_column" : "nx_row_hash"},
            "first_change_date" : {"persistent_column" : "nx_creation_date"},
            "last_change_date" :  {"persistent_column" : "nx_modification_date"},
            "is_active" :         {"persistent_column" : "nx_is_active"}
        },
        "distinct_rows" : false,
        "end_of_time_is_null" : true
    }
}"""

cdc = ads.ChangeDataCapture(config_json, connection_string, logger)
cdc.run()
