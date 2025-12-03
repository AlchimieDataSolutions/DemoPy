import warnings
warnings.simplefilter("ignore", FutureWarning)
from uuid import uuid4
from datetime import datetime, date, time

data = [
    [
        i, f"User{i}", f"C{i:03d}", f"Produit {i}", i*2, 1000000000000 + i, round(10.5 * i, 3), round(.5 * i, 2),
        round(1.0 + i * .1, 2), round(.5 + i * .05, 2), date(2025, 10, (i%28)+1),
        datetime(2025, 10, (i % 28)+1, 8+i%12, 0, 0),
        datetime(2025, 10, (i % 28)+1, 16, i % 60, 0),
        time(9+i%12, 30, 0), 1 if i % 2 == 0 else 0,
        str(uuid4())
    ]
    for i in range(1, 50_001)
]

# Pour récupérer l'ip publique de la machine, vous pouvez faire
# print(ads.get_public_ip(timeout=5))