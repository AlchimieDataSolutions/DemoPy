import adsToolBox as ads
import os

source_dir = ""
dest_dir = "file/file_handler/"

files = [".xml", ".csv", ".gif", ".zip", ".png", ".pdf", ".py", ".txt", ".jpg"]

os.makedirs(dest_dir, exist_ok=True)

logger = ads.Logger(ads.Logger.DEBUG, "AdsLogger")
ads.set_timer(True)

file_handler = ads.FileHandler(logger)

special_characters_text = """
Voici quelques caractères spéciaux :
- Accents : é, è, ê, ë, à, â, ä, î, ï, ô, ö, ù, ü, ñ, ç, œ
- Caractères non-latins : привет, 你好, こんにちは, здравствуйте, مرحبا
- Symboles : @, €, #, &, %, ©, ™, →, ±, ∆, ∑, ∞, ≠, √, ∫, ≈, £, ¥
- Emojis : 😊, 😂, 🥺, ❤️, 👍, 👑, 🌍, 🍕, 🏀
- Caractères arabes : العربية, ١٢٣٤٥, أ
- Caractères cyrilliques : А, Б, В, Г, Д, Ж, З, И, Й, К
- Divers : ¿, ¡, ©, ®, ‰, ∅, ¶, ′, ″, ⅛, ⅓, ⅔, ⅘, ≡, ⊗
"""

file_path = os.path.join(dest_dir, "file.txt")
# Ici nous gardons les caractères spéciaux
file_handler.write_file(file_path, special_characters_text, "w", False)

path, extension = file_path.split('.')
file_path = path + 'clean' + extension
# Ici, non (attention à écrire en binaire lorsque qu'on veut nettoyer et inversement
file_handler.write_file(file_path, special_characters_text, "wb", True)

# De manière générale, si vous n'avez pas besoin de vérifier quelque chose dans le fichier, écrivez en binaire

# Si on veut se connecter à un partage smb, il faut définir FileHander comme suit:

file_handler = ads.FileHandler(logger, {"server": "", "username": "", "password": ""})