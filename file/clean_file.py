import os
import adsToolBox as ads

script_name = os.path.basename(__file__)
logger = ads.Logger(ads.Logger.DEBUG, f"adsLogger - {script_name}")

fh = ads.FileHandler(logger)

raw = "file/file_raw.txt"
clean = "file/file_cleaned.txt"

special_characters_text = """Voici quelques caractères spéciaux :
- Accents : é, è, ê, ë, à, â, ä, î, ï, ô, ö, ù, ü, ñ, ç, œ
- Caractères non-latins : привет, 你好, こんにちは, здравствуйте, مرحبا
- Symboles : @, €, #, &, %, ©, ™, →, ±, ∆, ∑, ∞, ≠, √, ∫, ≈, £, ¥
- Emojis : 😊, 😂, 🥺, ❤️, 👍, 👑, 🌍, 🍕, 🏀
- Caractères arabes : العربية, ١٢٣٤٥, أ
- Caractères cyrilliques : А, Б, В, Г, Д, Ж, З, И, Й, К
- Divers : ¿, ¡, ©, ®, ‰, ∅, ¶, ′, ″, ⅛, ⅓, ⅔, ⅘, ≡, ⊗
"""

# Ici nous gardons les caractères spéciaux
fh.write_file(raw, special_characters_text, "w", False)

# Ici, non (attention à écrire en binaire lorsque qu'on veut nettoyer et inversement)
fh.write_file(clean, special_characters_text, "wb", True)

# De manière générale, si vous n'avez pas besoin de vérifier quelque chose dans le fichier, écrivez en binaire