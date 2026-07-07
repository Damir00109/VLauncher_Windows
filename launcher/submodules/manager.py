import shutil
import subprocess
from pathlib import Path
from typing import Callable, List, Optional

from launcher.config import SUBMODULES_DIR
from launcher.submodules.git_portable import ensure_portable_git, find_git_executable


class SubmoduleManager:
    """Загрузка и обновление git-сабмодулей в test_launcher/submodules/."""

    def __init__(self, root: Optional[Path] = None):
        self.root = root or SUBMODULES_DIR
        self.root.mkdir(parents=True, exist_ok=True)

    def ensure_git(self, log: Optional[Callable[[str], None]] = None) -> Path:
        return ensure_portable_git(log=log)

    def git_ready(self) -> bool:
        return find_git_executable() is not None

    def list_checkout_dirs(self) -> List[Path]:
        if not self.root.exists():
            return []
        return sorted(p for p in self.root.iterdir() if p.is_dir() and not p.name.startswith("."))

    def _run_git(self, args: List[str], log: Optional[Callable[[str], None]] = None) -> None:
        git_exe = self.ensure_git(log)
        cmd = [str(git_exe), *args]
        if log:
            log(f"[GIT] {' '.join(args)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(detail or f"git {' '.join(args)} failed")

    def clone(
        self,
        url: str,
        name: str,
        *,
        branch: Optional[str] = None,
        log: Optional[Callable[[str], None]] = None,
    ) -> Path:
        dest = self.root / name
        if dest.exists():
            raise FileExistsError(f"Сабмодуль уже существует: {dest}")

        args = ["clone", "--depth", "1"]
        if branch:
            args.extend(["--branch", branch])
        args.extend([url, str(dest)])

        if log:
            log(f"[SUBMODULE] clone {url} → {dest}")
        self._run_git(args, log)
        return dest

    def pull(self, name: str, log: Optional[Callable[[str], None]] = None) -> Path:
        dest = self.root / name
        if not dest.is_dir():
            raise FileNotFoundError(f"Сабмодуль не найден: {dest}")
        self._run_git(["-C", str(dest), "pull", "--ff-only"], log)
        return dest

    def ensure_repo(
        self,
        url: str,
        name: str,
        *,
        branch: Optional[str] = None,
        update: bool = True,
        log: Optional[Callable[[str], None]] = None,
    ) -> Path:
        dest = self.root / name
        git_dir = dest / ".git"

        if dest.exists() and not git_dir.is_dir():
            if log:
                log(f"[SUBMODULE] Удаляю повреждённую папку {dest}")
            shutil.rmtree(dest)

        if not git_dir.is_dir():
            return self.clone(url, name, branch=branch, log=log)

        if update:
            try:
                self.pull(name, log=log)
            except RuntimeError as exc:
                if log:
                    log(f"[SUBMODULE] Обновление пропущено: {exc}")
        return dest
