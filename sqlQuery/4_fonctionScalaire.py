from CommonLib import *

source_pg.connect()

result = source_pg.sqlScalaire('''SELECT NOW()''')
print(result)
