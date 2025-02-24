from CommonLib import *

batch_size = 1_000

schema = 'dbo'
table = 'insert_test'

query = f"""
SELECT
    c.COLUMN_NAME AS ColumnName,
    t.NAME AS DataType,
    c.CHARACTER_MAXIMUM_LENGTH AS MaxLength,
    c.NUMERIC_PRECISION AS NumericPrecision,
    c.NUMERIC_SCALE AS NumericScale
FROM INFORMATION_SCHEMA.COLUMNS c
JOIN sys.types t ON c.DATA_TYPE = t.name
WHERE c.TABLE_NAME = '{table}' AND c.TABLE_SCHEMA = '{schema}'
ORDER BY c.ORDINAL_POSITION;
"""

res = list(source_mssql.sqlQuery(query))[0]
cols = [elem[0] for elem in res]
cols_def = [
    f"{elem[1]}(MAX)" if elem[2] == -1 else f"{elem[1]}({elem[2]})"
    if elem[2] and elem[1] not in {"text", "ntext", "xml"} # pas de longueur à définir dans ces cas
    else elem[1]
    for elem in res
]

# Déclarer une destination
destination = {
    'name': 'test',
    'db': source_mssql,
    'table': 'insert_test_copy',
    'schema': 'dbo',
    'cols': cols, # Les colonnes à créer
    'cols_def': cols_def # Les types des colonnes
}

# Déclaration du pipeline
pipe = ads.pipeline({
    'db_source': source_pg, # La source du pipeline
    'query_source': query, # pas utile ici
    'db_destination': destination, # La destination du pipeline
    'batch_size': batch_size
}, logger)

pipe.create_destination_table(drop=True) # Cette méthode s'occupe de créer la table de destination

query = f"""
SELECT
    c.COLUMN_NAME AS ColumnName,
    t.NAME AS DataType,
    c.CHARACTER_MAXIMUM_LENGTH AS MaxLength,
    c.NUMERIC_PRECISION AS NumericPrecision,
    c.NUMERIC_SCALE AS NumericScale
FROM INFORMATION_SCHEMA.COLUMNS c
JOIN sys.types t ON c.DATA_TYPE = t.name
WHERE c.TABLE_NAME = '{table}_copy' AND c.TABLE_SCHEMA = '{schema}'
ORDER BY c.ORDINAL_POSITION;
"""
print(list(source_mssql.sqlQuery(query))[0])

logger.info("Fin de la démonstration")

# Dans ce script, nous avons crée la table de destination automatiquement sans faire de requête à la main