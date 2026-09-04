"""
Jeu de données partagé par plusieurs démonstrations.

Ce module vit à la RACINE du dépôt. Les scripts en sous-dossier ne peuvent
donc pas faire `import utils` directement : lancés par
`python operations/insert.py`, leur sys.path[0] est `operations/`, pas la
racine. Ils doivent d'abord ajouter la racine au chemin :

    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import utils

Les données sont construites par une FONCTION, pas au niveau du module :
générer 50 000 lignes coûtait environ 4 secondes et 38 Mo à chaque import,
y compris pour les scripts qui n'en avaient pas besoin.
"""
from datetime import date, datetime, time
from uuid import uuid4

# Colonnes du jeu de données, dans l'ordre des valeurs produites.
COLS = [
    "id", "nom", "code", "produit", "quantite", "gros_entier",
    "montant", "remise", "taux", "coefficient", "jour",
    "horodatage", "horodatage_fin", "heure", "actif", "uuid",
]

# Types SQL correspondants, utilisables tels quels dans cols_def d'un
# Pipeline. Adaptez TIMESTAMP/DATETIME2 selon le backend de destination.
COLS_DEF = [
    "INT", "VARCHAR(50)", "VARCHAR(10)", "VARCHAR(50)", "INT", "BIGINT",
    "FLOAT", "FLOAT", "FLOAT", "FLOAT", "DATE",
    "TIMESTAMP", "TIMESTAMP", "TIME", "INT", "VARCHAR(36)",
]


def build_data(nb_lignes: int = 50_000) -> list[list]:
    """
    Construit le jeu de données de démonstration.

    Couvre volontairement des types variés (entiers, gros entiers, flottants,
    date, datetime, time, booléen encodé en 0/1, UUID en texte) pour
    éprouver l'inférence de schéma de Pipeline et les conversions Polars.

    :param nb_lignes: nombre de lignes à générer. Réduisez-le pour observer,
        augmentez-le pour tester les batchs.
    """
    return [
        [
            i,
            f"User{i}",
            f"C{i:03d}",
            f"Produit {i}",
            i * 2,
            1_000_000_000_000 + i,
            round(10.5 * i, 3),
            round(.5 * i, 2),
            round(1.0 + i * .1, 2),
            round(.5 + i * .05, 2),
            date(2025, 10, (i % 28) + 1),
            datetime(2025, 10, (i % 28) + 1, 8 + i % 12, 0, 0),
            datetime(2025, 10, (i % 28) + 1, 16, i % 60, 0),
            time(9 + i % 12, 30, 0),
            1 if i % 2 == 0 else 0,
            str(uuid4()),
        ]
        for i in range(1, nb_lignes + 1)
    ]

# Rétrocompatibilité : `utils.data` reste disponible mais n'est construit
# qu'au premier accès, grâce au __getattr__ de module (PEP 562) — le même
# mécanisme que celui qu'adsToolBox utilise pour ses propres modules.
def __getattr__(name: str) -> object:
    """Construit `data` à la demande."""
    if name == "data":
        valeur = build_data()
        globals()["data"] = valeur
        return valeur
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)