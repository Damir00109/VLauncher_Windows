import os
from pathlib import Path
from typing import Callable, Dict, Optional, Set, Tuple

import httpx
import minecraft_launcher_lib

from launcher.config import API_BASE
from launcher.utils import file_sha256


def _neoforge_mod_loader():
    return minecraft_launcher_lib.mod_loader.get_mod_loader("neoforge")


def _forge_mod_loader():
    return minecraft_launcher_lib.mod_loader.get_mod_loader("forge")


def _parse_forge_loader_version(mc_version: str, loader_version: str) -> str:
    loader_version = (loader_version or "").strip()
    if not loader_version:
        full = minecraft_launcher_lib.forge.find_forge_version(mc_version)
        if full and full.startswith(f"{mc_version}-"):
            return full[len(mc_version) + 1:]
        return ""
    if loader_version.startswith(f"{mc_version}-"):
        return loader_version[len(mc_version) + 1:]
    if loader_version.startswith(f"{mc_version}-forge-"):
        return loader_version[len(mc_version) + len("-forge-"):]
    return loader_version


def _resolve_forge_version(mc_version: str, loader_version: str, minecraft_dir: Path) -> str:
    try:
        mod_loader = _forge_mod_loader()
        lv = _parse_forge_loader_version(mc_version, loader_version) or mod_loader.get_latest_loader_version(mc_version)
        return mod_loader.get_installed_version(mc_version, lv)
    except Exception:
        pass
    full = loader_version or minecraft_launcher_lib.forge.find_forge_version(mc_version) or ""
    if full:
        try:
            return minecraft_launcher_lib.forge.forge_to_installed_version(full)
        except ValueError:
            return full
    installed = {v.get("id") for v in minecraft_launcher_lib.utils.get_installed_versions(str(minecraft_dir))}
    matches = sorted(vid for vid in installed if "forge" in vid.lower() and mc_version in vid)
    return matches[-1] if matches else mc_version


def _resolve_neoforge_version(mc_version: str, loader_version: str, minecraft_dir: Path) -> str:
    loader_version = (loader_version or "").strip()
    try:
        mod_loader = _neoforge_mod_loader()
        lv = loader_version or mod_loader.get_latest_loader_version(mc_version)
        return mod_loader.get_installed_version(mc_version, lv)
    except Exception:
        pass
    installed = {v.get("id") for v in minecraft_launcher_lib.utils.get_installed_versions(str(minecraft_dir))}
    if loader_version:
        candidate = f"neoforge-{loader_version}"
        if candidate in installed:
            return candidate
    prefix = "neoforge-"
    matches = sorted(vid for vid in installed if vid.startswith(prefix))
    return matches[-1] if matches else mc_version


def resolve_launch_version(mc_version: str, loader: str, loader_version: str, minecraft_dir: Path) -> str:
    loader = (loader or "vanilla").lower()
    loader_version = (loader_version or "").strip()
    if loader == "vanilla":
        return mc_version
    if loader == "forge":
        return _resolve_forge_version(mc_version, loader_version, minecraft_dir)
    if loader == "neoforge":
        return _resolve_neoforge_version(mc_version, loader_version, minecraft_dir)
    if loader == "fabric":
        installed = {v.get("id") for v in minecraft_launcher_lib.utils.get_installed_versions(str(minecraft_dir))}
        if loader_version:
            for candidate in (
                f"fabric-loader-{loader_version}-{mc_version}",
                f"fabric-loader-{loader_version}-{mc_version}-0",
            ):
                if candidate in installed:
                    return candidate
        for entry in minecraft_launcher_lib.utils.get_installed_versions(str(minecraft_dir)):
            vid = str(entry.get("id", ""))
            if mc_version in vid and "fabric" in vid.lower():
                return vid
    return mc_version


def install_minecraft_stack(
    version: str,
    loader: str,
    minecraft_dir: Path,
    log,
    loader_version: str = "",
    callback: Optional[Dict] = None,
    stop_check: Optional[Callable[[], bool]] = None,
) -> Tuple[str, bool]:
    if stop_check and stop_check():
        return resolve_launch_version(version, loader, loader_version, minecraft_dir), False
    minecraft_dir.mkdir(parents=True, exist_ok=True)
    cb = callback or {}
    installed = {v.get("id") for v in minecraft_launcher_lib.utils.get_installed_versions(str(minecraft_dir))}
    loader = (loader or "vanilla").lower()
    loader_version = (loader_version or "").strip()
    did_install = False

    if loader == "vanilla":
        if version not in installed:
            log(f"[INSTALL] Minecraft {version} → {minecraft_dir}")
            minecraft_launcher_lib.install.install_minecraft_version(version, str(minecraft_dir), callback=cb)
            did_install = True
    elif loader == "fabric":
        need_install = True
        if loader_version:
            need_install = f"fabric-loader-{loader_version}-{version}" not in installed
        else:
            need_install = not any(version in vid and "fabric" in vid.lower() for vid in installed)
        if need_install:
            log(f"[INSTALL] Fabric{f' {loader_version}' if loader_version else ''} → {minecraft_dir}")
            if loader_version:
                minecraft_launcher_lib.fabric.install_fabric(version, str(minecraft_dir), loader_version=loader_version, callback=cb)
            else:
                minecraft_launcher_lib.fabric.install_fabric(version, str(minecraft_dir), callback=cb)
            did_install = True
    elif loader == "forge":
        try:
            mod_loader = _forge_mod_loader()
            lv = _parse_forge_loader_version(version, loader_version) or mod_loader.get_latest_loader_version(version)
            launch_id = mod_loader.get_installed_version(version, lv)
            if launch_id not in installed:
                log(f"[INSTALL] Forge {lv} → {minecraft_dir}")
                log("[INSTALL] Запуск процессоров Forge (может занять несколько минут)...")
                mod_loader.install(version, str(minecraft_dir), loader_version=lv, callback=cb)
                did_install = True
        except Exception as exc:
            log(f"[INSTALL] Forge ошибка: {exc}")
    elif loader == "neoforge":
        try:
            mod_loader = _neoforge_mod_loader()
            lv = loader_version or mod_loader.get_latest_loader_version(version)
            launch_id = mod_loader.get_installed_version(version, lv)
            if launch_id not in installed:
                log(f"[INSTALL] NeoForge {lv} → {minecraft_dir}")
                mod_loader.install(version, str(minecraft_dir), loader_version=lv, callback=cb)
                did_install = True
        except Exception as exc:
            log(f"[INSTALL] NeoForge ошибка: {exc}")
    return resolve_launch_version(version, loader, loader_version, minecraft_dir), did_install


def _download_if_needed(
    dest: Path,
    url: str,
    expected_hash: str,
    rel_path: str,
    log,
) -> str:
    expected = (expected_hash or "").lower()
    if expected and dest.is_file():
        local_hash = file_sha256(dest)
        if local_hash == expected:
            log(f"[SYNC] актуален: {rel_path}")
            return local_hash

    dest.parent.mkdir(parents=True, exist_ok=True)
    log(f"[SYNC] загрузка: {rel_path}")
    r = httpx.get(url, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)
    actual_hash = file_sha256(dest)
    if expected and actual_hash != expected:
        raise RuntimeError(f"Хеш не совпал после загрузки: {rel_path}")
    return actual_hash


def sync_profile_files(
    profile_id: str,
    detail: Dict,
    game_dir: Path,
    log,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
) -> Dict[str, str]:
    manifest: Dict[str, str] = detail.get("manifest") or {}
    hashes: Dict[str, str] = {}
    base = f"{API_BASE}/launcher/game-profiles/{profile_id}/files"
    total = len(manifest)
    for index, rel_path in enumerate(manifest, start=1):
        rel_norm = rel_path.replace("\\", "/")
        dest = game_dir / rel_norm.replace("/", os.sep)
        url = f"{base}/{rel_norm}"
        if on_progress:
            on_progress(index, total, rel_norm)
        log(f"[SYNC] ({index}/{total}) {rel_norm}")
        hashes[rel_norm] = _download_if_needed(dest, url, manifest[rel_path], rel_norm, log)
    return hashes


def enabled_optional_mod_relpaths(detail: Dict, enabled_ids: Set[str]) -> Set[str]:
    """Пути включённых опциональных модов в mods/ — не удалять при очистке."""
    paths: Set[str] = set()
    for mod in detail.get("optionalMods") or []:
        mod_id = str(mod.get("id") or "")
        rel_path = str(mod.get("file") or "").replace("\\", "/")
        if mod_id in enabled_ids and rel_path:
            paths.add(f"mods/{Path(rel_path).name}")
    return paths


def purge_locked_extras(
    game_dir: Path,
    detail: Dict,
    log,
    keep_relpaths: Optional[Set[str]] = None,
) -> int:
    """Удаляет из защищённых папок файлы, которых нет в манифесте сервера."""
    manifest: Dict[str, str] = detail.get("manifest") or {}
    if not manifest:
        return 0

    locked_dirs = detail.get("lockedDirs") or ["mods", "config"]
    allowed = {p.replace("\\", "/") for p in manifest}
    keep = {p.replace("\\", "/") for p in (keep_relpaths or set())}
    removed = 0

    for folder in locked_dirs:
        folder = str(folder).strip().strip("/\\")
        if not folder:
            continue
        root = game_dir / folder.replace("/", os.sep)
        if not root.is_dir():
            continue
        for file_path in sorted(root.rglob("*"), reverse=True):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(game_dir).as_posix()
            if rel in allowed or rel in keep:
                continue
            try:
                file_path.unlink()
                removed += 1
                log(f"[SYNC] Удалён лишний файл: {rel}")
            except OSError as exc:
                log(f"[SYNC] Не удалось удалить {rel}: {exc}")

    if removed:
        log(f"[SYNC] Очистка защищённых папок: удалено {removed} файл(ов)")
    return removed


def sync_optional_mods(
    profile_id: str,
    detail: Dict,
    game_dir: Path,
    enabled_ids: Set[str],
    log,
) -> None:
    optional_mods = detail.get("optionalMods") or []
    if not optional_mods:
        return

    manifest: Dict[str, str] = detail.get("manifest") or {}
    required_mod_names = {
        Path(rel).name for rel in manifest if rel.replace("\\", "/").startswith("mods/")
    }
    mods_dir = game_dir / "mods"
    mods_dir.mkdir(parents=True, exist_ok=True)
    base = f"{API_BASE}/launcher/game-profiles/{profile_id}/files"

    for mod in optional_mods:
        mod_id = str(mod.get("id") or "")
        rel_path = str(mod.get("file") or "").replace("\\", "/")
        if not mod_id or not rel_path:
            continue
        filename = Path(rel_path).name
        target = mods_dir / filename
        label = mod.get("name") or mod_id

        if mod_id in enabled_ids:
            expected_hash = str(mod.get("sha256") or "")
            if expected_hash and target.is_file() and file_sha256(target) == expected_hash.lower():
                log(f"[OPTS] актуален: {label}")
                continue
            log(f"[OPTS] Включён мод: {label}")
            url = f"{base}/{rel_path}"
            r = httpx.get(url, timeout=120)
            r.raise_for_status()
            target.write_bytes(r.content)
            actual = file_sha256(target)
            if expected_hash and actual != expected_hash.lower():
                raise RuntimeError(f"Хеш не совпал после загрузки опционального мода: {label}")
        elif filename not in required_mod_names and target.is_file():
            log(f"[OPTS] Отключён мод: {label}")
            target.unlink()
