import subprocess
from typing import Callable, Dict, List, Optional, Sequence

import httpx
import minecraft_launcher_lib
from PyQt6.QtCore import QThread, pyqtSignal, QRect
from PyQt6.QtGui import QImage, QPixmap, QPainter
from PyQt6.QtWidgets import QWidget

from launcher.api import api_request, refresh_session
from launcher.config import instances_dir, minecraft_dir, extract_texture_host
from launcher.install import (
    enabled_optional_mod_relpaths,
    install_minecraft_stack,
    purge_locked_extras,
    sync_optional_mods,
    sync_profile_files,
)
from launcher.profile_settings import get_enabled_optional_mod_ids
from launcher.jvm_args import merge_jvm_args
from launcher.patcher import patch_authlib
from launcher.subprocess_io import decode_subprocess_bytes
from launcher.submodules.packs_selector_service import launch_packs_selector
from launcher.utils import make_install_callback


class SessionRefreshWorker(QThread):
    ok_signal = pyqtSignal(dict)
    fail_signal = pyqtSignal()

    def __init__(self, refresh_token: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.refresh_token = refresh_token
        self.setObjectName("SessionRefreshWorker")

    def run(self):
        ok, data = refresh_session(self.refresh_token)
        if ok and data:
            self.ok_signal.emit(data)
        else:
            self.fail_signal.emit()


class SkinHeadWorker(QThread):
    ready_signal = pyqtSignal(QPixmap)

    def __init__(self, skin_url: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.skin_url = skin_url
        self.setObjectName("SkinHeadWorker")

    def run(self):
        try:
            if not self.skin_url:
                self.ready_signal.emit(QPixmap())
                return
            r = httpx.get(self.skin_url, timeout=15)
            r.raise_for_status()
            img = QImage.fromData(r.content)
            if img.isNull():
                self.ready_signal.emit(QPixmap())
                return
            size = 48
            head = QImage(size, size, QImage.Format.Format_ARGB32)
            head.fill(0)
            painter = QPainter(head)
            painter.drawImage(QRect(0, 0, size, size), img, QRect(8, 8, 8, 8))
            if img.height() >= 64 and img.width() >= 64:
                painter.drawImage(QRect(0, 0, size, size), img, QRect(40, 8, 8, 8))
            painter.end()
            self.ready_signal.emit(QPixmap.fromImage(head))
        except Exception:
            self.ready_signal.emit(QPixmap())


class UpdateCheckWorker(QThread):
    update_signal = pyqtSignal(object)
    up_to_date_signal = pyqtSignal()
    no_releases_signal = pyqtSignal(str)
    fail_signal = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("UpdateCheckWorker")

    def run(self):
        try:
            from launcher.updates import check_for_update

            result = check_for_update()
            if result.status == "update" and result.info is not None:
                self.update_signal.emit(result.info)
            elif result.status == "current":
                self.up_to_date_signal.emit()
            elif result.status == "no_releases":
                self.no_releases_signal.emit(result.message or "Нет релизов")
            else:
                self.fail_signal.emit(result.message or "Ошибка проверки")
        except Exception as exc:
            self.fail_signal.emit(str(exc))


class PrepareLaunchWorker(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    ready_signal = pyqtSignal(dict)
    failed_signal = pyqtSignal(str)

    def __init__(
        self,
        profile_id: str,
        token: str,
        username: str,
        user_uuid: str,
        ram_mb: int,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.profile_id = profile_id
        self.token = token
        self.username = username
        self.user_uuid = user_uuid
        self.ram_mb = ram_mb
        self._stop = False
        self._install_max = 100
        self._install_value = 0
        self.setObjectName("PrepareLaunchWorker")

    def request_stop(self):
        self._stop = True

    def log(self, msg: str):
        self.log_signal.emit(msg)

    def _stopped(self) -> bool:
        return self._stop

    def _on_install_max(self, value: int):
        self._install_max = max(1, int(value))
        self._install_value = 0
        self.progress_signal.emit(0, self._install_max)

    def _on_install_progress(self, value: int):
        self._install_value = int(value)
        self.progress_signal.emit(self._install_value, self._install_max)

    def _on_sync_progress(self, current: int, total: int, path: str):
        self.status_signal.emit(path)
        self.progress_signal.emit(current, total)

    def run(self):
        try:
            if self._stopped():
                return
            detail = api_request("GET", f"/launcher/game-profiles/{self.profile_id}", auth=self.token)
            if not detail:
                self.failed_signal.emit("Не удалось загрузить профиль с сервера")
                return
            slug = detail["slug"]
            mc_dir = minecraft_dir()
            instance_dir = instances_dir() / slug
            instance_dir.mkdir(parents=True, exist_ok=True)
            version = detail["minecraftVersion"]
            loader = detail.get("loader", "vanilla")
            loader_version = detail.get("loaderVersion", "")

            self.log(f"=== Профиль: {detail.get('name')} ({version}, {loader}) ===")
            self.log(f"[PATH] Клиент/libraries → {mc_dir}")
            self.log(f"[PATH] gameDirectory → {instance_dir}")

            callback = make_install_callback(
                self.log,
                self.status_signal.emit,
                self._on_install_max,
                self._on_install_progress,
            )
            launch_version, did_install = install_minecraft_stack(
                version,
                loader,
                mc_dir,
                self.log,
                loader_version,
                callback=callback,
                stop_check=self._stopped,
            )
            if self._stopped():
                return

            self.log("[PATCH] authlib после установки...")
            patch_authlib(extract_texture_host(), self.log, refresh_backup=did_install)
            self.log(f"[INSTALL] Версия для запуска: {launch_version}")

            enabled_optional = get_enabled_optional_mod_ids(
                self.profile_id,
                detail.get("optionalMods") or [],
            )
            if detail.get("optionalMods"):
                self.log(f"[OPTS] Применение опциональных модов ({len(enabled_optional)} вкл.)...")
                sync_optional_mods(
                    self.profile_id,
                    detail,
                    instance_dir,
                    enabled_optional,
                    self.log,
                )
                if self._stopped():
                    return

            manifest = detail.get("manifest") or {}
            local_hashes: Dict[str, str] = {}
            if manifest:
                self.log(f"[SYNC] Загрузка {len(manifest)} защищённых файлов в {instance_dir}...")
                local_hashes = sync_profile_files(
                    self.profile_id,
                    detail,
                    instance_dir,
                    self.log,
                    self._on_sync_progress,
                )
                if self._stopped():
                    return
                keep_optional = enabled_optional_mod_relpaths(detail, enabled_optional)
                purge_locked_extras(instance_dir, detail, self.log, keep_relpaths=keep_optional)
                if self._stopped():
                    return
                verify = api_request(
                    "POST",
                    f"/launcher/game-profiles/{self.profile_id}/verify",
                    {"accessToken": self.token, "files": local_hashes},
                    auth=self.token,
                )
                if verify and not verify.get("valid", True):
                    invalid = ", ".join(verify.get("invalid", []))
                    self.failed_signal.emit(f"Проверка целостности не пройдена: {invalid}")
                    return
                self.log("[OK] Целостность файлов подтверждена")

            config = api_request(
                "GET",
                f"/launcher/minecraft/launch-config?profileId={self.profile_id}",
                auth=self.token,
            )
            api_jvm = config.get("jvmArgs", []) if config else []
            all_jvm = merge_jvm_args(api_jvm, self.ram_mb, extra=["-Drealms.environment=LOCAL"])

            self.ready_signal.emit({
                "version": launch_version,
                "minecraft_dir": str(mc_dir),
                "game_dir": str(instance_dir),
                "jvm_args": all_jvm,
                "username": self.username,
                "uuid": self.user_uuid,
                "token": self.token,
            })
        except Exception as e:
            if not self._stopped():
                self.failed_signal.emit(str(e))


class LaunchWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)

    def __init__(self, launch_opts: Dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.launch_opts = launch_opts
        self.process = None
        self._stop = False
        self.setObjectName("LaunchWorker")

    def run(self):
        try:
            opts = {
                "username": self.launch_opts["username"],
                "uuid": self.launch_opts["uuid"],
                "token": self.launch_opts["token"],
                "jvmArguments": self.launch_opts["jvm_args"],
                "launcherName": "Launcher",
                "launcherVersion": "1.0",
                "gameDirectory": self.launch_opts["game_dir"],
            }
            cmd = minecraft_launcher_lib.command.get_minecraft_command(
                self.launch_opts["version"],
                self.launch_opts["minecraft_dir"],
                opts,
            )
            self.process = subprocess.Popen(
                cmd,
                cwd=self.launch_opts["game_dir"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            while not self._stop:
                if self.process.poll() is not None:
                    remaining = self.process.stdout.read()
                    if remaining:
                        for line in remaining.splitlines():
                            self.log_signal.emit(decode_subprocess_bytes(line).rstrip("\r\n"))
                    break
                line = self.process.stdout.readline()
                if not line:
                    break
                self.log_signal.emit(decode_subprocess_bytes(line).rstrip("\r\n"))
            code = self.process.wait() if self.process else -1
            self.finished_signal.emit(code if not self._stop else -1)
        except Exception as e:
            self.log_signal.emit(f"!!! Ошибка запуска: {e}")
            self.finished_signal.emit(-1)

    def stop(self):
        self._stop = True
        if self.process and self.process.poll() is None:
            self.process.kill()


class PacksSelectorLaunchWorker(QThread):
    ok_signal = pyqtSignal()
    closed_signal = pyqtSignal()
    failed_signal = pyqtSignal(str)

    def __init__(
        self,
        slug: str,
        minecraft_version: str,
        loader: str,
        packs: Sequence[str],
        log: Optional[Callable[[str], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.slug = slug
        self.minecraft_version = minecraft_version
        self.loader = loader
        self.packs: List[str] = list(packs)
        self._log = log
        self.process: Optional[subprocess.Popen] = None
        self._stop = False
        self.setObjectName("PacksSelectorLaunchWorker")

    def request_stop(self) -> None:
        self._stop = True
        if self.process and self.process.poll() is None:
            self.process.kill()

    def run(self):
        started = False
        try:
            self.process = launch_packs_selector(
                self.slug,
                self.minecraft_version,
                self.loader,
                self.packs,
                log=self._log,
                update=False,
            )
            started = True
            self.ok_signal.emit()
            while not self._stop and self.process.poll() is None:
                self.msleep(200)
            if not self._stop and self.process.poll() is None:
                self.process.wait()
        except Exception as exc:
            self.failed_signal.emit(str(exc))
        finally:
            if started:
                self.closed_signal.emit()


class NewsCoverWorker(QThread):
    ready_signal = pyqtSignal(QPixmap)

    def __init__(self, image_url: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.image_url = image_url
        self.setObjectName("NewsCoverWorker")

    def run(self):
        try:
            if self.isInterruptionRequested():
                return
            response = httpx.get(self.image_url, timeout=15.0, follow_redirects=True)
            response.raise_for_status()
            if self.isInterruptionRequested():
                return
            img = QImage.fromData(response.content)
            self.ready_signal.emit(QPixmap.fromImage(img) if not img.isNull() else QPixmap())
        except Exception:
            self.ready_signal.emit(QPixmap())


class ImageLoadWorker(QThread):
    ready_signal = pyqtSignal(QPixmap)

    def __init__(self, image_url: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.image_url = image_url
        self.setObjectName("ImageLoadWorker")

    def run(self):
        try:
            if self.isInterruptionRequested():
                return
            response = httpx.get(self.image_url, timeout=15.0, follow_redirects=True)
            response.raise_for_status()
            if self.isInterruptionRequested():
                return
            img = QImage.fromData(response.content)
            self.ready_signal.emit(QPixmap.fromImage(img) if not img.isNull() else QPixmap())
        except Exception:
            self.ready_signal.emit(QPixmap())


class NewsListWorker(QThread):
    ok_signal = pyqtSignal(str, list)
    disabled_signal = pyqtSignal()
    fail_signal = pyqtSignal(str)

    def __init__(self, limit: int = 8, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.limit = limit
        self.setObjectName("NewsListWorker")

    def run(self):
        try:
            from launcher.news_api import fetch_news_article, fetch_news_list, get_launcher_news_api_url

            api_url = get_launcher_news_api_url()
            if not api_url:
                self.disabled_signal.emit()
                return
            items = fetch_news_list(api_url, limit=self.limit)
            enriched: List[Dict] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                slug = str(item.get("slug") or "").strip()
                merged = dict(item)
                if slug:
                    try:
                        full = fetch_news_article(api_url, slug)
                        if isinstance(full, dict):
                            merged["text"] = full.get("text") or ""
                            if full.get("image"):
                                merged["image"] = full.get("image")
                    except Exception:
                        merged.setdefault("text", "")
                enriched.append(merged)
            self.ok_signal.emit(api_url, enriched)
        except Exception as exc:
            self.fail_signal.emit(str(exc))
