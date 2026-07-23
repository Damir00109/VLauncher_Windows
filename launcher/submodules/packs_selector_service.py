import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence

from launcher.config import (
    PACKS_SELECTOR_NAME,
    PACKS_SELECTOR_REPO,
    instances_dir,
    packs_selector_dir,
)
from launcher.submodules.manager import SubmoduleManager
from launcher.utils import find_runtime_python, is_frozen_app

PACKS_SELECTOR_PORT = 8765

_PACKS_ALIASES = {
    "resourcepacks": "resourcepack",
    "resourcepack": "resourcepack",
    "textures": "resourcepack",
    "shaderpacks": "shader",
    "shader": "shader",
    "shaders": "shader",
    "mods": "mod",
    "mod": "mod",
}


def normalize_pack_types(packs: Iterable[str]) -> List[str]:
    result: List[str] = []
    for item in packs:
        key = item.strip().lower()
        mapped = _PACKS_ALIASES.get(key)
        if mapped and mapped not in result:
            result.append(mapped)
    return result


def packs_selector_ready() -> bool:
    root = packs_selector_dir().resolve()
    return (root / "packs_selector.py").is_file() and (root / "web" / "index.html").is_file()


def _deps_installed(python: Path) -> bool:
    # Dev: same interpreter — fast local check without spawning.
    if not is_frozen_app():
        try:
            if python.resolve() == Path(sys.executable).resolve():
                return (
                    importlib.util.find_spec("eel") is not None
                    and importlib.util.find_spec("requests") is not None
                )
        except OSError:
            pass
    try:
        result = subprocess.run(
            [str(python), "-c", "import eel, requests"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _install_deps(root: Path, log: Optional[Callable[[str], None]] = None) -> None:
    python = find_runtime_python()
    if _deps_installed(python):
        return
    req = root / "requirements.txt"
    if req.is_file():
        if log:
            log(f"[PACKS] pip install -r {req.name} ({python})")
        cmd = [str(python), "-m", "pip", "install", "-r", str(req)]
    else:
        if log:
            log(f"[PACKS] pip install eel requests ({python})")
        cmd = [str(python), "-m", "pip", "install", "eel", "requests"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "pip install failed").strip()
        raise RuntimeError(detail)


def ensure_packs_selector(
    log: Optional[Callable[[str], None]] = None,
    *,
    update: bool = True,
    verbose: bool = True,
) -> Path:
    mgr = SubmoduleManager()
    root = mgr.ensure_repo(
        PACKS_SELECTOR_REPO,
        PACKS_SELECTOR_NAME,
        update=update,
        log=log if verbose else None,
    )

    if not packs_selector_ready():
        raise FileNotFoundError(
            f"Packs-Selector скачан, но неполный: {root}\n"
            f"Ожидаются packs_selector.py и web/index.html"
        )

    _install_deps(root, log if verbose else None)
    if log and verbose:
        log(f"[PACKS] Готов: {root}")
    return root


def instance_game_path(slug: str) -> Path:
    return (instances_dir() / slug).resolve()


def _require_launch_params(minecraft_version: str, loader: str) -> tuple[str, str]:
    version = (minecraft_version or "").strip()
    loader_name = (loader or "").strip().lower()
    if not version:
        raise ValueError("У игрового профиля не указана версия Minecraft")
    if not loader_name:
        raise ValueError("У игрового профиля не указан модлоадер")
    return version, loader_name


def build_launch_command(
    game_path: Path,
    minecraft_version: str,
    loader: str,
    packs: Sequence[str],
    *,
    port: int = PACKS_SELECTOR_PORT,
    quiet: bool = True,
    lock_filters: bool = True,
    launcher_mode: bool = True,
) -> List[str]:
    pack_types = normalize_pack_types(packs)
    if not pack_types:
        raise ValueError("Не указан тип паков")

    version, loader_name = _require_launch_params(minecraft_version, loader)

    cmd = [
        str(find_runtime_python()),
        "packs_selector.py",
        f"--game-path={game_path}",
        f"--mc-version={version}",
        f"-loader={loader_name}",
        f"-packs={','.join(pack_types)}",
        f"-port={port}",
    ]
    if launcher_mode:
        cmd.extend(["--launcher", "--shutdown-delay", "1"])
    if quiet:
        cmd.append("--quiet")
    if lock_filters:
        cmd.append("--lock-filters")
    return cmd


def launch_packs_selector(
    slug: str,
    minecraft_version: str,
    loader: str,
    packs: Sequence[str],
    log: Optional[Callable[[str], None]] = None,
    *,
    update: bool = False,
) -> subprocess.Popen:
    root = ensure_packs_selector(log, update=update, verbose=update)
    game_path = instance_game_path(slug)
    game_path.mkdir(parents=True, exist_ok=True)

    cmd = build_launch_command(game_path, minecraft_version, loader, packs)
    if log:
        version, loader_name = _require_launch_params(minecraft_version, loader)
        log(f"[PACKS] {version} / {loader_name} — {', '.join(normalize_pack_types(packs))} → {game_path}")

    return subprocess.Popen(
        cmd,
        cwd=str(root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
