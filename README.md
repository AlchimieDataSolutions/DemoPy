# DemoPy

Scripts d'illustration de la librairie
[`adstoolbox`](https://pypi.org/project/adstoolbox/) — un script par
fonctionnalité, commenté ligne à ligne, avec les subtilités et les pièges.

Chaque script est autonome et exécutable seul. Les commentaires font partie de
la démonstration : lisez-les autant que vous exécutez le code.

- **Version de la librairie ciblée** : `2026.09.02`
- **Python** : `>= 3.10`

## Table des matières

- [Installation](#installation)
- [Cœur et extras](#cœur-et-extras)
- [Index des scripts](#index-des-scripts)
- [Configuration](#configuration)
- [Ordre d'exécution](#ordre-dexécution)
- [Contribution](#contribution)
- [Licence](#licence)
- [Contact](#contact)

## Installation

```bash
python -m venv venv
source venv/bin/activate          # Windows : .\venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` installe `adstoolbox[all]`, soit toutes les dépendances
optionnelles — nécessaire pour exécuter **tous** les scripts du dépôt.
Comptez environ 480 Mo.

Pour n'installer que le nécessaire, référez-vous à la colonne **Extra** de
l'[index des scripts](#index-des-scripts) :

```bash
pip install "adstoolbox[pgsql]"        # les scripts marqués pgsql
pip install "adstoolbox[files,git]"    # plusieurs extras d'un coup
```

Les guillemets sont nécessaires sous `zsh`, qui interprète les crochets.

## Cœur et extras

Depuis la version `2026.09.02`, les dépendances d'`adstoolbox` sont
**optionnelles**. `pip install adstoolbox` n'installe qu'un cœur léger
(environ 20 Mo) ; les autres modules demandent un extra.

Les modules sont chargés paresseusement : `import adsToolBox` n'importe aucune
dépendance tierce, et une dépendance absente ne casse pas l'import du package.
L'erreur survient au premier usage du symbole, et nomme l'extra :

```
ImportError: DbPgsql requiert une dépendance non installée (No module named 'psycopg2').
Installez-la avec : pip install "adstoolbox[pgsql]".
```

| Extra | Débloque |
|---|---|
| *(aucun)* | `Logger`, `Env`, `MailReader`, `OdooConnector`, `timer`, `get_timer`, `set_timer`, `now`, `set_timezone`, `retry_on_failure`, `get_public_ip` |
| `dataframe` | `DataFactory`, `Pipeline`, `DataComparator` (installe `polars`) |
| `mssql` | `DbMssql` |
| `mysql` | `DbMysql` |
| `pgsql` | `DbPgsql` |
| `files` | `FileHandler` |
| `git` | `GitHandler` |
| `google` | `GoogleCalendarConnector` |
| `cdc` | `ChangeDataCapture` |
| `all` | tout |

Les extras de bases de données incluent `polars` : `adstoolbox[pgsql]` suffit
pour utiliser `Pipeline` avec PostgreSQL, sans ajouter `[dataframe]`.

**Piège** : un extra qui n'existe pas ne provoque pas d'erreur, seulement un
avertissement, et rien n'est installé.

```
$ pip install "adstoolbox[pymssql]"
WARNING: adstoolbox 2026.9.2 does not provide the extra 'pymssql'
```

Le nom correct est `mssql`. Les neuf extras valides sont ceux du tableau
ci-dessus. `installation/extras.py` démontre tout ceci et s'exécute avec le
cœur seul.

## Index des scripts

La colonne **Extra** indique ce qu'il faut avoir installé. Les scripts sans
extra tournent avec `pip install adstoolbox` nu.

### Installation et modèle de dépendances

| Script | Extra | Sujet |
|---|---|---|
| `installation/extras.py` | — | Cœur, extras, chargement paresseux, messages d'erreur, cas Polars/AVX2 |

### Logs, chronométrage, retry, environnement

| Script | Extra | Sujet |
|---|---|---|
| `logger/logger.py` | `pgsql` | Niveaux, `insert=False`, insertion en base, `disable`/`enable`, `disabled()`, `log_close`, `job_key` |
| `logger/timer.py` | `pgsql` | `@timer`, `set_timer`/`get_timer`, `set_timezone`, `now`, perte d'introspection |
| `logger/retry.py` | — | `retry_on_failure` : reconnexion, `retryable_exceptions`, `retry_count=0` |
| `logger/env.py` | — | `Env` : recherche automatique du `.env`, les trois façons de lire une variable |

### Connexions

| Script | Extra | Sujet |
|---|---|---|
| `connexion/db.py` | `mssql`, `mysql`, `pgsql` | Cycle de vie d'une connexion, clés par backend, reconnexion implicite |
| `connexion/odoo.py` | — | `OdooConnector` en XML-RPC : `desc`, `get`, `put`, domaines Odoo |
| `connexion/googleCalendar.py` | `google` | OAuth2, `scopes`, `get_events`, `save_events_to_csv` |

### Opérations sur les bases

| Script | Extra | Sujet |
|---|---|---|
| `operations/sql_simple.py` | `pgsql` | `sql_exec`, `sql_scalaire`, `find_text_anywhere` |
| `operations/read.py` | `pgsql` | `sql_query`, lecture par batchs, `return_columns` |
| `operations/insert.py` | `pgsql` | Les six méthodes : `insert`, `insert_many`, `insert_bulk` et les trois `upsert` |
| `operations/polymorphisme.py` | `mssql`, `mysql`, `pgsql` | `DataFactory` comme interface commune, et ce qui reste spécifique |
| `operations/compare.py` | `mysql`, `pgsql` | `DataComparator`, écarts de représentation entre backends |

### Pipelines et CDC

| Script | Extra | Sujet |
|---|---|---|
| `pipeline/pipeline.py` | `mysql`, `pgsql` | **Script de référence** : configuration complète, résultats de `run()` |
| `pipeline/pipeline_sources.py` | `pgsql` | Sources non-SQL : tableau en mémoire, API REST |
| `pipeline/pipeline_upsert.py` | `pgsql` | `operation_type='upsert'`, `conflict_cols`, `insert_method` |
| `pipeline/pipeline_hash.py` | `mysql`, `pgsql` | Déduplication par empreinte de ligne |
| `pipeline/pipeline_schema.py` | `mysql`, `pgsql` | `cols_def`, `create_destination_table`, `sql_defs_to_polars_schema` |
| `pipeline/cdc.py` | `cdc` | `ChangeDataCapture`, modes `append`/`scd1`/`scd2`/`scd4` |

Les configurations CDC complètes sont dans `pipeline/cdc_use.md`, à côté du
script.

### Fichiers

| Script | Extra | Sujet |
|---|---|---|
| `file/transfer_file.py` | `files` | `transfer_file`, `fastcheck`, `transform`, checksum, `wait_for_file` |
| `file/operation_file.py` | `files`, `pgsql` | Existence, listage, attente, `disk_check` |
| `file/create_read_csv.py` | `dataframe`, `files` | CSV avec Polars, en local et via `FileHandler` |
| `file/git_handler.py` | `git` | `check_permissions`, `clone_or_update`, `setup_virtualenv` |

### Dataframes, mail, divers

| Script | Extra | Sujet |
|---|---|---|
| `dataframe/polars_essentials.py` | `dataframe` | Tri, déduplication, jointures, valeurs nulles, transformations |
| `mail/mail.py` | `files` | `MailReader` : IMAP, `oauth2`/`credentials`, pièces jointes |
| `get_api_data.py` | — | Classe `NxOnyxApi`, utilisée par `pipeline/pipeline_sources.py` |
| `utils.py` | — | Jeu de données partagé, construit à la demande par `build_data()` |

## Configuration

Les scripts lisent leurs paramètres depuis un `.env` à la racine, chargé
automatiquement par `ads.Env` qui remonte l'arborescence depuis le script
appelant. Voir `logger/env.py` pour le détail.

```dotenv
# PostgreSQL — requis par la majorité des scripts
PG_DWH_DB=
PG_DWH_USER=
PG_DWH_PWD=
PG_DWH_PORT=5432
PG_DWH_HOST=

# MySQL — pipeline, compare, polymorphisme, db
MYSQL_DWH_DB=
MYSQL_DWH_USER=
MYSQL_DWH_PWD=
MYSQL_DWH_PORT=3306
MYSQL_DWH_HOST=

# SQL Server — db, polymorphisme
MSSQL_DWH_DB=
MSSQL_DWH_USER=
MSSQL_DWH_PWD=
MSSQL_DWH_PORT=1433
MSSQL_DWH_HOST=

# CDC (pipeline/cdc.py) — alimente la chaîne SQLAlchemy vers SQL Server
AFT_DB=
AFT_USER=
AFT_PWD=
AFT_PORT=1433
AFT_HOST=

# Odoo (connexion/odoo.py)
ODOO_URL=
ODOO_DB=
ODOO_USER=
ODOO_PWD=

# API (pipeline/pipeline_sources.py via get_api_data.py)
API_DOMAIN=
API_USER=
API_PASSWORD=
TENANT_ID=

# GitHub (file/git_handler.py)
GITHUB_TOKEN=
GITHUB_REPO=DemoPy
GITHUB_BRANCH=

# Messagerie (mail/mail.py) — mode oauth2
MAIL=
MAIL_URL=
MAIL_CLIENT_ID=
MAIL_CLIENT_SECRET=
MAIL_FROM=
# Messagerie — mode credentials
MAIL_LOGIN=
MAIL_PWD=
```

`connexion/googleCalendar.py` ne passe pas par le `.env` : il attend un
fichier `credentials.json` téléchargé depuis la console Google, et crée
lui-même son `token.json` à la première connexion.

## Ordre d'exécution

Les scripts `operations/` et `pipeline/` partagent la table `insert_test`.
Lancez **`pipeline/pipeline.py` en premier** : c'est lui qui la crée et la
remplit dans les deux bases. `operations/insert.py`, `operations/read.py` et
`operations/compare.py` la supposent existante — `operations/insert.py`
commence même par un `TRUNCATE`.

`pipeline/pipeline_schema.py` et `pipeline/pipeline_hash.py` appellent
`create_destination_table(drop=True)` sur cette même table : ils la
**recréent** avec leur propre `cols_def`. Après les avoir exécutés, relancez
`pipeline/pipeline.py` avant de revenir aux scripts `operations/`, sinon les
types de colonnes ne correspondent plus à ce que `utils.build_data()` fournit.

## Contribution

1. Forkez le projet.
2. Créez votre branche (`git checkout -b feature/AmazingFeature`).
3. Commitez vos changements (`git commit -m 'Add some AmazingFeature'`).
4. Poussez la branche et ouvrez une Pull Request.

Pour ajouter un script de démonstration :

- un script par fonctionnalité, exécutable seul ;
- l'extra requis en première ligne, sous la forme `# adstoolbox[pgsql]`, en
  n'utilisant que les neuf noms valides ;
- les paramètres passés **nommés**, même quand ils valent le défaut, pour que
  chaque option reste visible ;
- une ligne dans l'[index des scripts](#index-des-scripts) ;
- les commentaires expliquent les subtilités et les pièges, pas seulement ce
  que fait le code.

Si le script utilise `utils.py`, qui vit à la racine, il faut ajouter la
racine au chemin — sinon `python operations/monscript.py` échoue avec
`ModuleNotFoundError: No module named 'utils'` :

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import utils  # noqa: E402
```

## Licence

Distribué sous licence MIT, comme `adstoolbox`.

## Contact

- Olivier Siguré — <olivier.sigure@alchimiedatasolutions.com>
- Matthieu Vannin — <matthieu.vannin@alchimiedatasolutions.com>
- Antoine Ducoulombier — <antoine.ducoulombier@alchimiedatasolutions.com>
- Pierre Baux — <pierre.baux@alchimiedatasolutions.com>
