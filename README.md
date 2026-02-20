# DemoPy

Ce projet est un ensemble de scripts démontrant différentes fonctionnalités en Python, notamment des pipelines de données, des configurations d'environnement, des tests unitaires et des outils de log et de chronométrage.

## Table des Matières

- [Installation](#installation)
- [Usage](#usage)
    - [Pipeline de Données](#pipeline-de-donnees)
    - [Configuration d'Environnement](#configuration-d-environnement)
    - [Tests Unitaires](#tests-unitaires)
    - [Logger et Timer](#logger-et-timer)
- [Tests](#tests)
- [Contribution](#contribution)
- [Licence](#licence)
- [Contact](#contact)

## Installation

Pour installer les dépendances de votre projet, exécutez :

```bash
pip install -r requirements.txt
```

Vous pouvez également utiliser un environnement virtuel :

```bash
python -m venv env
source env/bin/activate  # Sur Windows: .\env\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Configuration d'Environnement

Utiliser cette méthode pour gérer les configurations d'environnement.

```python
import adsToolBox as ads
from pathlib import Path

script_name = Path(__file__).name
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")
env = ads.Env(logger, file=None)
```

### Démonstrations

Dans les dossiers connexion, dataframe, file, logger, mail, operations et pipeline se trouvent des scripts qui illustrent des
traitement génériques, utilisant pour la plupart la librairie adsToolBox.

## Contribution

Pour contribuer à ce projet :

1. Forkez le projet
2. Créez votre branche de fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Commitez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez votre branche (`git push origin feature/AmazingFeature`)
5. Ouvrez un pull request

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE.md pour plus de détails.

## Contact

Pour toute question, veuillez contacter :

Antoine Ducoulombier - antoine.ducoulombier@alchimiedatasolutions.com  
Matthieu Vannin - matthieu.vannin@alchimiedatasolutions.com
