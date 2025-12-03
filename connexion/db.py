import utils
import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.Env(logger)

# Instanciation d'une connexion à une base PostgreSQL
source_pg = ads.DbPgsql({'database':env.PG_DWH_DB
                    , 'user':env.PG_DWH_USER
                    , 'password':env.PG_DWH_PWD
                    , 'port':env.PG_DWH_PORT
                    , 'host':env.PG_DWH_HOST}, logger, 1)
# Connexion
source_pg.connect()
# Déconnexion
source_pg.disconnect()

# Instanciation d'une connexion à une base MSSQL
source_mssql = ads.DbMssql({'database':env.MSSQL_DWH_DB
                    , 'user':env.MSSQL_DWH_USER
                    , 'password':env.MSSQL_DWH_PWD
                    , 'port':env.MSSQL_DWH_PORT
                    , 'host':env.MSSQL_DWH_HOST
                    , 'charset': 'UTF-8' # par défaut UTF-8
}, logger, 1)
# Connexion
source_mssql.connect()
# Déconnexion
source_mssql.disconnect()

# Instanciation d'une connexion à une base MySQL
source_mysql = ads.DbMysql({'database': env.MYSQL_DWH_DB
                    , 'user': env.MYSQL_DWH_USER
                    , 'password': env.MYSQL_DWH_PWD
                    , 'port': env.MYSQL_DWH_PORT
                    , 'host': env.MYSQL_DWH_HOST
}, logger, 1)
# Connexion
source_mysql.connect()
# Déconnexion
source_mysql.disconnect()