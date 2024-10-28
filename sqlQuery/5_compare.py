from CommonLib import *
import polars as pl

rows = [(f'Name {i}', f'email{i}@example.com') for i in range(5)]
print(source_pg.insertBulk('insert_test', ['name', 'email'], rows))

rejects = pipePgToSqlServer.run()
print(f"Rejets : {rejects}")

# Les deux tables devraient être égales donc

query = "SELECT * FROM insert_test;"
data = list(source_pg.sqlQuery(query))[0]
df_pg = pl.DataFrame(data, orient="row", strict=False)

data = list(source_mssql.sqlQuery(query))[0]
df_mssql = pl.DataFrame(data, orient='row', strict=False)

data = list(source_pg.sqlQuery('''SELECT tenantname, taille, unite, fichier FROM onyx_qs."diskcheck" LIMIT 5'''))[0]
df_other = pl.DataFrame(data, schema=["tenantname", "taille", "unite", "fichier"], orient='row', strict=False)

if df_pg.equals(df_mssql):
    logger.warning("Les deux tables sont identiques !")
else:
    logger.error("Les deux tables ne sont pas identiques ! :(")

if df_pg.equals(df_other):
    logger.error("Ces deux là ne devraient pas être identiques ! :(")
else:
    logger.warning("Ces deux tables là ne sont pas les mêmes !")


logger.info("Fin de la démonstration")