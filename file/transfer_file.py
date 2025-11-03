import hashlib
import fsspec
import time

def compute_checksum(path: str, fs, algo: str = "md5") -> str:
    """Calcule le checksum (md5, sha1, sha256, ...) d'un fichier."""
    h = hashlib.new(algo)
    with fs.open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def transfer_file(src_path: str, dst_path: str, src_fs, dst_fs, checksum_algo="md5"):
    with src_fs.open(src_path, "rb") as src, dst_fs.open(dst_path, "wb") as dst:
        dst.write(src.read())

    src_hash = compute_checksum(src_path, src_fs, checksum_algo)
    dst_hash = compute_checksum(dst_path, dst_fs, checksum_algo)

    if src_hash != dst_hash:
        raise ValueError(f"Checksum mismatch ({src_hash} != {dst_hash})")
    print(f"Fichier transféré avec succès ({checksum_algo} OK).")

def transfer_with_retry(src_path, dst_path, src_fs, dst_fs, checksum_algo="md5", retries=3, delay=5):
    """Transfert avec retry automatique en cas d'échec."""
    for attempt in range(1, retries + 1):
        try:
            transfer_file(src_path, dst_path, src_fs, dst_fs, checksum_algo)
            return
        except Exception as e:
            if attempt < retries:
                print(f"Tentative {attempt} échouée: {e}. Nouvelle tentative dans {delay}s...")
                time.sleep(delay)
            else:
                print(f"Toutes les tentatives ont échoué ({retries}).")
                raise

if __name__ == "__main__":
    azure_options = {
        "account_name": "user",
        "account_key": "key",
    }

    smb_options = {
        "host": "host",
        "username": "user",
        "password": "password"
    }

    src_path = "az:source"
    dst_path = "smb:destination"

    src_fs = fsspec.filesystem("az", **azure_options)
    dst_fs = fsspec.filesystem("smb", **smb_options)

    transfer_with_retry(src_path, dst_path, src_fs, dst_fs, checksum_algo="sha256", retries=3, delay=5)
