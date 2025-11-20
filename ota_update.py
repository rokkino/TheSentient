import os
import io
import zipfile
import shutil
import tempfile


REPO_RAW_VERSION_URL = "https://raw.githubusercontent.com/rokkino/TheSentient/main/version.txt"
REPO_ZIP_URL = "https://github.com/rokkino/TheSentient/archive/refs/heads/main.zip"


def read_local_version(version_file: str = "version.txt") -> str:
    try:
        with open(version_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "0.0.0"


def fetch_remote_version(session) -> str:
    resp = session.get(REPO_RAW_VERSION_URL, timeout=10)
    resp.raise_for_status()
    return resp.text.strip()


def version_tuple(v: str):
    parts = [p for p in v.strip().split(".") if p.isdigit()]
    return tuple(int(p) for p in parts[:4]) or (0,)


def is_remote_newer(local_v: str, remote_v: str) -> bool:
    return version_tuple(remote_v) > version_tuple(local_v)


def download_and_extract_zip(session, target_dir: str) -> str:
    resp = session.get(REPO_ZIP_URL, timeout=60)
    resp.raise_for_status()
    data = io.BytesIO(resp.content)
    with zipfile.ZipFile(data) as zf:
        tmp_dir = tempfile.mkdtemp(prefix="thesentient_update_")
        zf.extractall(tmp_dir)
        # Zip root is typically TheSentient-main
        entries = os.listdir(tmp_dir)
        if not entries:
            raise RuntimeError("Archivio vuoto")
        extracted_root = os.path.join(tmp_dir, entries[0])
        if not os.path.isdir(extracted_root):
            extracted_root = tmp_dir
        return extracted_root


def copy_tree(src_dir: str, dst_dir: str, preserve_files=None):
    if preserve_files is None:
        preserve_files = set()
    for root, dirs, files in os.walk(src_dir):
        rel = os.path.relpath(root, src_dir)
        dst_root = os.path.join(dst_dir, rel) if rel != "." else dst_dir
        os.makedirs(dst_root, exist_ok=True)
        for f in files:
            if f in preserve_files:
                continue
            src_path = os.path.join(root, f)
            dst_path = os.path.join(dst_root, f)
            shutil.copy2(src_path, dst_path)


