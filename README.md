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

### Pipeline de Données

Le fichier `demo_pipeline_3_destinations.py` démontre comment créer et gérer des pipelines de données avec des destinations multiples.

```python
from demo_pipeline_3_destinations import main

main()
```

### Configuration d'Environnement

Utiliser le fichier `env.py` pour gérer les configurations d'environnement.

```python
import env

config = env.get_config()
print(config)
```

### Tests Unitaires

Le fichier `test.py` contient des exemples de tests unitaires pour votre projet. Utilisez `pytest` pour exécuter ces tests.

### Logger et Timer

Le fichier `demo_logger_timer.py` démontre l'utilisation des logs et des timers pour mesurer l'exécution du code.

```python
from demo_logger_timer import logger, timer

@timer
def sample_function():
    logger.info("Function executed")
    # Votre code ici

sample_function()
```

## Tests

Pour exécuter les tests unitaires :

```bash
pytest
```

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

Nom - [@VotrePseudo](https://twitter.com/votre_pseudo) - email@example.com

Lien du projet: https://github.com/votre_nom_d_utilisateur/DemoPy