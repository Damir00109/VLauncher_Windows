from pathlib import Path
from typing import List

RESOURCEPACKS_DIR = "resourcepacks"
SHADERPACKS_DIR = "shaderpacks"


def _safe_filename(name: str) -> str:
    cleaned = name.strip().replace("\\", "/")
    if not cleaned or "/" in cleaned or cleaned in (".", ".."):
        raise ValueError("Недопустимое имя файла")
    return cleaned


def list_installed_packs(instance_dir: Path, pack_dir: str) -> List[str]:
    folder = instance_dir / pack_dir
    if not folder.is_dir():
        return []
    return sorted(
        path.name
        for path in folder.iterdir()
        if path.is_file()
    )


def delete_installed_pack(instance_dir: Path, pack_dir: str, filename: str) -> Path:
    safe_name = _safe_filename(filename)
    target = (instance_dir / pack_dir / safe_name).resolve()
    root = (instance_dir / pack_dir).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError("Недопустимый путь к файлу")
    if not target.is_file():
        raise FileNotFoundError(f"Файл не найден: {safe_name}")
    target.unlink()
    return target
