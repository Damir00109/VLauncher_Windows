import threading
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, QTimer, QSize, QPoint, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QIcon, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from launcher.api import api_request, refresh_session
from launcher.config import APP_NAME, HWID, INSTANCES_DIR, extract_texture_host
from launcher.launcher_settings import get_keep_launcher_visible
from launcher.patcher import patch_authlib
from launcher.profile_settings import get_ram_mb
from launcher.realms_proxy import start_realms_proxy
from launcher.session import clear_session_file, load_session, save_session
from launcher.submodules import ensure_packs_selector
from launcher.ui.general_settings_page import GeneralSettingsPage
from launcher.ui.news_panel import NewsPanel
from launcher.ui.packs_manager_page import PacksManagerPage
from launcher.ui.profile_background_layer import ProfileBackgroundController
from launcher.ui.profile_cards_panel import ProfileCardsPanel
from launcher.ui.icons import load_svg_icon
from launcher.ui.theme import (
    LAUNCH_BUTTON_STYLE,
    LAUNCH_RUNNING_BUTTON_STYLE,
    LOGIN_BUTTON_STYLE,
    STOP_BUTTON_STYLE,
)
from launcher.ui.widgets import create_panel
from launcher.ui.window_shell import LauncherShell, ChromeTextButton, ProfileChipButton, WindowControlButton
from launcher.workers import (
    LaunchWorker,
    NewsListWorker,
    PacksSelectorLaunchWorker,
    PrepareLaunchWorker,
    SessionRefreshWorker,
    SkinHeadWorker,
)


ICON_BUTTON_SIZE = 52
MAIN_LOGIN = 0
MAIN_LAUNCHER = 1


PROFILE_AVATAR_SIZE = 26
PROFILE_AVATAR_RADIUS = 7


def _round_avatar_pixmap(pixmap: QPixmap, size: int = PROFILE_AVATAR_SIZE, radius: int = PROFILE_AVATAR_RADIUS) -> QPixmap:
    scaled = pixmap.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    rounded = QPixmap(size, size)
    rounded.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()
    return rounded


class MainWindow(QMainWindow):
    packs_bootstrap_log = pyqtSignal(str)

    PAGE_MAIN = 0
    PAGE_GENERAL_SETTINGS = 1
    PAGE_PACKS_MANAGER = 2

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(1000, 700)
        self.resize(1100, 720)

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.profile: Optional[Dict] = None
        self.game_profiles: List[Dict] = []
        self.prepare_worker: Optional[PrepareLaunchWorker] = None
        self.launch_worker: Optional[LaunchWorker] = None
        self.refresh_worker: Optional[SessionRefreshWorker] = None
        self.skin_worker: Optional[SkinHeadWorker] = None
        self.packs_worker: Optional[PacksSelectorLaunchWorker] = None
        self.news_worker: Optional[NewsListWorker] = None
        self._pending_launch_profile: Optional[Dict] = None
        self._shutting_down = False
        self._progress_status = ""
        self._progress_last_value = -1
        self._progress_last_max = 0
        self._progress_indeterminate = False
        self._game_running = False
        self._progress_log_idle_ms = 4000
        self._progress_log_idle_timer = QTimer(self)
        self._progress_log_idle_timer.setSingleShot(True)
        self._progress_log_idle_timer.timeout.connect(self._on_log_idle)

        self._setup_ui()
        self.packs_bootstrap_log.connect(self.log)
        start_realms_proxy(self.log)
        patch_authlib(extract_texture_host(), self.log)
        self.log(f"{APP_NAME} готов к работе")
        self._start_packs_selector_bootstrap()
        self._start_saved_session()

    def _start_packs_selector_bootstrap(self) -> None:
        def _run() -> None:
            try:
                ensure_packs_selector(self.packs_bootstrap_log.emit, update=True)
            except Exception as exc:
                self.packs_bootstrap_log.emit(f"[PACKS] Подготовка при старте: {exc}")

        threading.Thread(target=_run, daemon=True, name="packs-bootstrap").start()

    def _setup_ui(self):
        self.shell = LauncherShell(APP_NAME, self)
        self.shell.title_bar.minimize_clicked.connect(self.showMinimized)
        self.shell.title_bar.close_clicked.connect(self.close)
        self.shell.title_bar.back_clicked.connect(self._show_main_page)

        self.btn_reload = WindowControlButton("reload.svg", parent=self.shell.title_bar)
        self.btn_reload.setToolTip("Обновить сборки и новости")
        self.btn_reload.setEnabled(False)
        self.btn_reload.setVisible(False)
        self.btn_reload.clicked.connect(self.refresh_all)
        self.shell.title_bar.add_trailing_widget(self.btn_reload)

        self.btn_logs = ChromeTextButton("Логи", parent=self.shell.title_bar)
        self.btn_logs.clicked.connect(self._open_logs)
        self.shell.title_bar.add_trailing_widget(self.btn_logs)

        self.btn_profile = ProfileChipButton(self.shell.title_bar)
        self.btn_profile.setVisible(False)
        self.btn_profile.clicked.connect(self._show_profile_menu)
        self.shell.title_bar.add_trailing_widget(self.btn_profile)

        self.stack = QStackedWidget()
        self.shell.set_content(self.stack)
        self.setCentralWidget(self.shell)
        self.profile_bg = ProfileBackgroundController(
            self.shell.frame,
            self.shell.frame.content_host,
            self.shell.title_bar,
        )

        self.main_page = QWidget()
        main = QVBoxLayout(self.main_page)
        main.setContentsMargins(0, 0, 0, 0)

        self.main_inner_stack = QStackedWidget()
        main.addWidget(self.main_inner_stack)
        self.main_inner_stack.currentChanged.connect(self._update_profile_background_viewport)

        self._build_login_page()
        self._build_launcher_page()

        self.console = QTextEdit()
        self.console.setFont(QFont("Consolas", 10))
        self.console.setReadOnly(True)

        self.general_settings_page = GeneralSettingsPage(self.console, on_back=self._show_main_page)
        self.packs_manager_page = PacksManagerPage(
            on_back=self._show_main_page,
            on_open_manager=self._open_packs_selector,
            log=self.log,
        )
        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.general_settings_page)
        self.stack.addWidget(self.packs_manager_page)
        self.stack.setCurrentIndex(self.PAGE_MAIN)
        self.stack.currentChanged.connect(self._on_stack_page_changed)

        for page in (
            self.main_page,
            self.login_page,
            self.launcher_page,
            self.general_settings_page,
            self.packs_manager_page,
        ):
            page.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._update_auth_ui()
        self._on_stack_page_changed(self.stack.currentIndex())

    def _on_stack_page_changed(self, index: int) -> None:
        self.shell.title_bar.set_back_visible(index != self.PAGE_MAIN)
        self.shell.title_bar.set_title(APP_NAME)
        self._update_profile_background_viewport()

    def _update_profile_background_viewport(self) -> None:
        on_login = (
            self.stack.currentIndex() == self.PAGE_MAIN
            and self.main_inner_stack.currentIndex() == MAIN_LOGIN
        )
        logged_in = bool(self.access_token and self.refresh_token)
        self.profile_bg.set_viewport_active(logged_in and not on_login)

    def _build_login_page(self) -> None:
        self.login_page = QWidget()
        outer = QVBoxLayout(self.login_page)
        outer.setContentsMargins(24, 16, 24, 24)
        outer.addStretch(1)

        card, card_layout = create_panel()
        card.setMaximumWidth(380)
        card_layout.setSpacing(14)

        title = QLabel(APP_NAME)
        title_font = QFont()
        title_font.setPointSize(26)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#f4f7ff;background:transparent;")
        card_layout.addWidget(title)

        subtitle = QLabel("Войдите, чтобы продолжить")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color:#8b97ad;background:transparent;margin-bottom:6px;")
        card_layout.addWidget(subtitle)

        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Логин")
        self.login_edit.setMinimumHeight(44)
        card_layout.addWidget(self.login_edit)

        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Пароль")
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setMinimumHeight(44)
        card_layout.addWidget(self.pass_edit)

        self.btn_login = QPushButton("Войти")
        self.btn_login.setMinimumHeight(46)
        self.btn_login.setStyleSheet(LOGIN_BUTTON_STYLE)
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self.do_login)
        self.login_edit.returnPressed.connect(self.pass_edit.setFocus)
        self.pass_edit.returnPressed.connect(self.do_login)
        card_layout.addWidget(self.btn_login)

        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch(1)
        self.main_inner_stack.addWidget(self.login_page)

    def _build_launcher_page(self) -> None:
        self.launcher_page = QWidget()
        launcher = QVBoxLayout(self.launcher_page)
        launcher.setContentsMargins(0, 0, 0, 0)
        launcher.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setSpacing(14)

        profiles_box, pl = create_panel("Сборки")

        self.profile_cards = ProfileCardsPanel(
            on_packs=self._open_packs_manager_for,
        )
        self.profile_cards.setMinimumHeight(280)
        self.profile_cards.selection_changed.connect(self._update_launcher_controls)
        self.profile_cards.clear()
        pl.addWidget(self.profile_cards, stretch=1)
        self.profile_bg.attach_cards_panel(self.profile_cards)
        content_row.addWidget(profiles_box, stretch=3)

        news_box, news_layout = create_panel("Новости")
        self.news_panel = NewsPanel()
        self.news_panel.set_disabled("Войдите, чтобы видеть новости")
        news_layout.addWidget(self.news_panel, stretch=1)
        content_row.addWidget(news_box, stretch=2)
        launcher.addLayout(content_row, stretch=1)

        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("color:#9aa8c0;background:transparent;")
        launcher.addWidget(self.progress_label)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(ICON_BUTTON_SIZE)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        bottom_row.addWidget(self.progress_bar, stretch=1)

        self.btn_launch = QPushButton("ИГРАТЬ")
        self.btn_launch.setStyleSheet(LAUNCH_BUTTON_STYLE)
        self.btn_launch.setMinimumHeight(ICON_BUTTON_SIZE)
        self.btn_launch.setEnabled(False)
        self.btn_launch.clicked.connect(self.do_launch)
        bottom_row.addWidget(self.btn_launch, stretch=1)

        self.btn_stop = QPushButton()
        self.btn_stop.setFixedSize(ICON_BUTTON_SIZE, ICON_BUTTON_SIZE)
        self.btn_stop.setIcon(load_svg_icon("stop.svg"))
        self.btn_stop.setIconSize(QSize(22, 22))
        self.btn_stop.setStyleSheet(STOP_BUTTON_STYLE)
        self.btn_stop.setToolTip("Остановить игру")
        self.btn_stop.setVisible(False)
        self.btn_stop.clicked.connect(self._stop_game)
        bottom_row.addWidget(self.btn_stop)

        launcher.addLayout(bottom_row)

        self.main_inner_stack.addWidget(self.launcher_page)

    def _open_packs_manager_for(self, gp: Dict) -> None:
        if not self.access_token:
            QMessageBox.warning(self, "Паки", "Сначала войдите")
            return
        instance_dir = INSTANCES_DIR / str(gp["slug"])
        optional_mods: List[Dict] = []
        detail = api_request(
            "GET",
            f"/launcher/game-profiles/{gp['id']}",
            auth=self.access_token,
        )
        if detail:
            optional_mods = detail.get("optionalMods") or []
        self.packs_manager_page.open_for_profile(gp, instance_dir, optional_mods=optional_mods)
        self.packs_manager_page.set_managers_enabled(True)
        self.stack.setCurrentIndex(self.PAGE_PACKS_MANAGER)

    def _open_packs_manager(self) -> None:
        gp = self.selected_game_profile()
        if not gp:
            QMessageBox.warning(self, "Паки", "Выберите сборку")
            return
        self._open_packs_manager_for(gp)

    def _show_profile_menu(self) -> None:
        menu = QMenu(self)
        logout_action = menu.addAction("Выйти")
        logout_action.triggered.connect(self.do_logout)
        anchor = self.btn_profile.mapToGlobal(QPoint(0, self.btn_profile.height()))
        menu_width = menu.sizeHint().width()
        anchor.setX(anchor.x() + self.btn_profile.width() - menu_width)
        menu.exec(anchor)

    def _set_profile_button_text(self, name: str, loading: bool = False) -> None:
        if not name:
            self.btn_profile.setText("")
            self.btn_profile.setToolTip("Профиль")
            return
        if loading:
            self.btn_profile.setText("…")
            self.btn_profile.setToolTip(name)
            return
        metrics = QFontMetrics(self.btn_profile.font())
        label = metrics.elidedText(name, Qt.TextElideMode.ElideRight, 108)
        self.btn_profile.setText(label)
        self.btn_profile.setToolTip(name)

    def _set_profile_button_icon(self, pixmap: Optional[QPixmap]) -> None:
        if pixmap is None or pixmap.isNull():
            self.btn_profile.setIcon(QIcon())
            return
        self.btn_profile.setIcon(QIcon(_round_avatar_pixmap(pixmap)))

    def _show_main_page(self):
        self.stack.setCurrentIndex(self.PAGE_MAIN)

    def _instance_dir_for_selected_profile(self) -> Optional[Path]:
        gp = self.selected_game_profile()
        if not gp:
            return None
        return INSTANCES_DIR / str(gp["slug"])

    def _open_logs(self):
        self.stack.setCurrentIndex(self.PAGE_GENERAL_SETTINGS)

    def log(self, text: str):
        self.console.append(text)
        self._touch_progress_activity()

    def _touch_progress_activity(self) -> None:
        if not self.progress_bar.isVisible() or self._progress_last_max <= 0:
            return

        if self._progress_indeterminate:
            self._progress_indeterminate = False
            self.progress_bar.setRange(0, self._progress_last_max)
            self.progress_bar.setValue(self._progress_last_value)
            self._update_progress_label()

        self._progress_log_idle_timer.start(self._progress_log_idle_ms)

    def _update_progress_label(self) -> None:
        base = self._progress_status or "Загрузка"
        if self._progress_indeterminate:
            self.progress_label.setText(f"{base}...")
            return
        pct = int(self._progress_last_value / self._progress_last_max * 100) if self._progress_last_max else 0
        self.progress_label.setText(f"{base} — {pct}%")

    def _update_auth_ui(self):
        logged_in = bool(self.access_token and self.refresh_token)
        if logged_in:
            self.main_inner_stack.setCurrentIndex(MAIN_LAUNCHER)
            self.btn_reload.setVisible(True)
            self.btn_profile.setVisible(True)
            if self.profile:
                name = str(self.profile.get("name", ""))
                self._set_profile_button_text(name)
                self._load_skin_head(str(self.profile.get("skinUrl", "")))
            self._update_launcher_controls()
        else:
            self.main_inner_stack.setCurrentIndex(MAIN_LOGIN)
            self._set_profile_button_text("")
            self._set_profile_button_icon(None)
            self.btn_reload.setEnabled(False)
            self.btn_reload.setVisible(False)
            self.btn_profile.setVisible(False)
        self._update_profile_background_viewport()

    def _update_launcher_controls(self):
        logged_in = bool(self.access_token and self.refresh_token)
        has_profile = bool(self.selected_game_profile())
        self.btn_reload.setEnabled(logged_in)
        if self._game_running:
            self.btn_launch.setText("ЗАПУЩЕНО")
            self.btn_launch.setEnabled(False)
            self.btn_launch.setStyleSheet(LAUNCH_RUNNING_BUTTON_STYLE)
            self.btn_stop.setVisible(get_keep_launcher_visible())
        else:
            self.btn_launch.setText("ИГРАТЬ")
            self.btn_launch.setStyleSheet(LAUNCH_BUTTON_STYLE)
            self.btn_launch.setEnabled(logged_in and has_profile)
            self.btn_stop.setVisible(False)
        self.profile_cards.set_actions_enabled(logged_in)
        self.packs_manager_page.set_managers_enabled(logged_in and has_profile)

    def _worker_running(self, worker: Optional[QThread]) -> bool:
        try:
            return worker is not None and worker.isRunning()
        except RuntimeError:
            return False

    def _stop_worker(self, worker: Optional[QThread], stop_method: Optional[str] = None, timeout_ms: int = 5000):
        if worker is None:
            return
        try:
            running = worker.isRunning()
        except RuntimeError:
            return
        if not running:
            return
        if stop_method and hasattr(worker, stop_method):
            getattr(worker, stop_method)()
        elif hasattr(worker, "request_stop"):
            worker.request_stop()
        if not worker.wait(timeout_ms):
            worker.terminate()
            worker.wait(3000)

    def _retire_worker(self, attr: str, stop_method: Optional[str] = None, timeout_ms: int = 5000):
        worker = getattr(self, attr, None)
        if worker is not None:
            self._stop_worker(worker, stop_method, timeout_ms)
            setattr(self, attr, None)

    def shutdown_workers(self):
        self._shutting_down = True
        self._retire_worker("launch_worker", "stop", 5000)
        self._retire_worker("prepare_worker", "request_stop", 180000)
        self._retire_worker("refresh_worker", None, 10000)
        self._retire_worker("skin_worker", None, 5000)
        self._retire_worker("packs_worker", "request_stop", 120000)
        self._retire_worker("news_worker", None, 5000)

    def _open_packs_selector(self, pack_type: str):
        gp = self.selected_game_profile()
        if not gp:
            QMessageBox.warning(self, "Паки", "Выберите игровой профиль")
            return
        if not self.access_token:
            QMessageBox.warning(self, "Паки", "Сначала войдите")
            return

        mc_version = str(gp.get("minecraftVersion", "")).strip()
        loader = str(gp.get("loader", "")).strip()
        if not mc_version or not loader:
            QMessageBox.warning(
                self,
                "Паки",
                "Для этой сборки не указана версия Minecraft или модлоадер.\n"
                "Обратитесь к администратору сервера.",
            )
            return

        self.profile_cards.set_actions_enabled(False)
        self._retire_worker("packs_worker", "request_stop", 3000)
        self.packs_worker = PacksSelectorLaunchWorker(
            str(gp["slug"]),
            mc_version,
            loader,
            [pack_type],
            log=self.log,
            parent=self,
        )
        self.packs_worker.ok_signal.connect(self._on_packs_selector_ok)
        self.packs_worker.closed_signal.connect(self._on_packs_selector_closed)
        self.packs_worker.failed_signal.connect(self._on_packs_selector_failed)
        self.packs_worker.finished.connect(self.packs_worker.deleteLater)
        self.packs_worker.start()

    def _on_packs_selector_ok(self):
        self._update_launcher_controls()
        self.log("[PACKS] Окно выбора паков открыто")

    def _on_packs_selector_closed(self):
        self.packs_manager_page.refresh_lists()
        self._update_launcher_controls()
        self.log("[PACKS] Список паков обновлён")

    def _on_packs_selector_failed(self, message: str):
        self._update_launcher_controls()
        self.log(f"[PACKS] Ошибка: {message}")
        QMessageBox.critical(self, "Паки", message)

    def _load_skin_head(self, skin_url: str):
        self._retire_worker("skin_worker", None, 5000)
        name = str(self.profile.get("name", "")) if self.profile else ""
        self._set_profile_button_text(name, loading=True)
        self._set_profile_button_icon(None)
        self.skin_worker = SkinHeadWorker(skin_url, self)
        self.skin_worker.ready_signal.connect(self._on_skin_head_ready)
        self.skin_worker.finished.connect(self.skin_worker.deleteLater)
        self.skin_worker.start()

    def _on_skin_head_ready(self, pixmap: QPixmap):
        name = str(self.profile.get("name", "")) if self.profile else ""
        self._set_profile_button_text(name)
        self._set_profile_button_icon(None if pixmap.isNull() else pixmap)

    def _apply_session(self, access_token: str, refresh_token: str, profile: Optional[Dict], login: str = ""):
        self.access_token = access_token
        self.refresh_token = refresh_token
        if profile:
            self.profile = profile
        if refresh_token:
            save_session(refresh_token, login or (profile or {}).get("name", ""))
        self._update_auth_ui()
        self.load_game_profiles()
        self.load_news()

    def load_news(self):
        self.news_panel.set_loading()
        self._retire_worker("news_worker", None, 3000)
        self.news_worker = NewsListWorker(limit=8, parent=self)
        self.news_worker.ok_signal.connect(self._on_news_loaded)
        self.news_worker.disabled_signal.connect(self._on_news_disabled)
        self.news_worker.fail_signal.connect(self._on_news_failed)
        self.news_worker.finished.connect(self.news_worker.deleteLater)
        self.news_worker.start()

    def _on_news_loaded(self, api_url: str, articles: List[Dict]):
        self.news_panel.set_articles(articles)

    def _on_news_disabled(self):
        self.news_panel.set_disabled()

    def _on_news_failed(self, message: str):
        self.news_panel.set_error("Не удалось загрузить новости")
        self.log(f"[NEWS] {message}")

    def _clear_session(self, notify: bool = False):
        self.access_token = None
        self.refresh_token = None
        self.profile = None
        clear_session_file()
        self.profile_cards.clear()
        self.profile_bg.clear()
        self.news_panel.set_disabled("Войдите, чтобы видеть новости")
        self.pass_edit.clear()
        self._update_auth_ui()
        if notify:
            self.log("Сессия завершена")

    def _start_saved_session(self):
        session = load_session()
        token = session.get("refreshToken")
        if not token:
            return
        self.log("Восстановление сессии...")
        self._retire_worker("refresh_worker", None, 3000)
        self.refresh_worker = SessionRefreshWorker(str(token), self)
        self.refresh_worker.ok_signal.connect(self._on_startup_refresh_ok)
        self.refresh_worker.fail_signal.connect(self._on_startup_refresh_fail)
        self.refresh_worker.finished.connect(self.refresh_worker.deleteLater)
        self.refresh_worker.start()

    def _on_startup_refresh_ok(self, data: Dict):
        session = load_session()
        login = session.get("login", "")
        refresh = session.get("refreshToken") or self.refresh_token or ""
        self._apply_session(data.get("accessToken", ""), refresh, data.get("profile"), str(login))
        self.log("Сессия восстановлена")

    def _on_startup_refresh_fail(self):
        self._clear_session()
        self.log("Сохранённая сессия недействительна")

    def selected_game_profile(self) -> Optional[Dict]:
        return self.profile_cards.selected_profile()

    def refresh_all(self):
        if not self.access_token:
            return
        self.load_game_profiles()
        self.load_news()

    def load_game_profiles(self):
        data = api_request("GET", "/launcher/game-profiles", auth=self.access_token)
        self.game_profiles = data.get("profiles", []) if data else []
        if not self.game_profiles:
            self.profile_cards.set_profiles([])
            self.profile_bg.clear()
            self.btn_launch.setEnabled(False)
            return
        self.profile_cards.set_profiles(self.game_profiles)
        self.profile_bg.preload_backgrounds(self.game_profiles)
        self.profile_bg.sync_selection(animate=False)
        self._update_launcher_controls()

    def do_login(self):
        login = self.login_edit.text().strip()
        password = self.pass_edit.text().strip()
        if not login or not password:
            QMessageBox.warning(self, "Вход", "Логин и пароль обязательны")
            return
        self.btn_login.setEnabled(False)
        self.log("Вход в аккаунт...")
        data = api_request("POST", "/launcher/auth/login", {"login": login, "password": password, "hwid": HWID})
        self.btn_login.setEnabled(True)
        if not data:
            QMessageBox.critical(self, "Ошибка входа", "Неверный логин или пароль.\nПроверьте данные и попробуйте снова.")
            return
        self._apply_session(
            data.get("accessToken", ""),
            data.get("refreshToken", ""),
            data.get("profile"),
            login,
        )
        self.pass_edit.clear()
        self.log("Вход выполнен")

    def do_logout(self):
        if self.access_token or self.refresh_token:
            api_request("POST", "/launcher/auth/logout", {
                "accessToken": self.access_token,
                "refreshToken": self.refresh_token,
                "hwid": HWID,
            })
        self._clear_session(notify=True)

    def _refresh_tokens(self) -> bool:
        if not self.refresh_token:
            return False
        ok, data = refresh_session(self.refresh_token)
        if not ok or not data:
            self._clear_session()
            self.log("Сессия истекла — войдите снова")
            return False
        self.access_token = data.get("accessToken", self.access_token)
        if data.get("profile"):
            self.profile = data["profile"]
        self._update_auth_ui()
        return True

    def do_launch(self):
        if self._game_running:
            return
        gp = self.selected_game_profile()
        if not gp:
            QMessageBox.warning(self, "Запуск", "Выберите игровой профиль")
            return
        if not self.access_token or not self.profile:
            QMessageBox.warning(self, "Запуск", "Сначала войдите")
            return
        self.btn_launch.setEnabled(False)
        self._show_progress_indeterminate("Обновление токена...")
        self._pending_launch_profile = gp
        self._retire_worker("prepare_worker", "request_stop", 3000)
        self._retire_worker("refresh_worker", None, 3000)
        self.refresh_worker = SessionRefreshWorker(self.refresh_token or "", self)
        self.refresh_worker.ok_signal.connect(self._on_prelaunch_refresh_ok)
        self.refresh_worker.fail_signal.connect(self._on_prelaunch_refresh_fail)
        self.refresh_worker.finished.connect(self.refresh_worker.deleteLater)
        self.refresh_worker.start()

    def _on_prelaunch_refresh_ok(self, data: Dict):
        self.access_token = data.get("accessToken", self.access_token)
        if data.get("profile"):
            self.profile = data["profile"]
        gp = self._pending_launch_profile
        if not gp:
            self._reset_progress()
            return
        self._show_progress_determinate(0, 100, "Подготовка...")
        self._retire_worker("prepare_worker", "request_stop", 3000)
        ram_mb = get_ram_mb(str(gp["id"]), int(gp.get("ramMb", 2048)))
        self.prepare_worker = PrepareLaunchWorker(
            gp["id"],
            self.access_token or "",
            self.profile.get("name", "") if self.profile else "",
            self.profile.get("uuid", "") if self.profile else "",
            ram_mb,
            self,
        )
        self.prepare_worker.log_signal.connect(self.log)
        self.prepare_worker.status_signal.connect(self._on_prepare_status)
        self.prepare_worker.progress_signal.connect(self._on_prepare_progress)
        self.prepare_worker.ready_signal.connect(self._start_game)
        self.prepare_worker.failed_signal.connect(self._prepare_failed)
        self.prepare_worker.finished.connect(self._on_prepare_finished)
        self.prepare_worker.start()

    def _on_prepare_finished(self):
        if self.sender() is self.prepare_worker:
            self.prepare_worker = None

    def _on_prelaunch_refresh_fail(self):
        self._clear_session()
        self._reset_progress()
        QMessageBox.warning(self, "Запуск", "Сессия истекла. Войдите снова.")

    def _activate_progress_ui(self) -> None:
        self.btn_launch.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)

    def _show_progress_indeterminate(self, label: str) -> None:
        self._progress_log_idle_timer.stop()
        self._progress_indeterminate = True
        self._progress_last_value = -1
        self._progress_last_max = 0
        self._activate_progress_ui()
        self.progress_bar.setRange(0, 0)
        self.progress_label.setText(label)

    def _show_progress_determinate(self, value: int, maximum: int, label: str) -> None:
        self._progress_indeterminate = False
        self._progress_last_value = value
        self._progress_last_max = maximum
        self._progress_status = label
        self._activate_progress_ui()
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)
        self.progress_label.setText(label)
        self._progress_log_idle_timer.start(self._progress_log_idle_ms)

    def _on_log_idle(self) -> None:
        if not self.progress_bar.isVisible():
            return
        if self.progress_bar.maximum() == 0:
            return
        if self._progress_indeterminate:
            return
        self._progress_indeterminate = True
        self.progress_bar.setRange(0, 0)
        self._update_progress_label()

    def _on_prepare_status(self, text: str):
        self._progress_status = text
        self._touch_progress_activity()
        if not self._progress_indeterminate:
            self._update_progress_label()

    def _on_prepare_progress(self, value: int, maximum: int):
        self._progress_last_value = value
        self._progress_last_max = maximum
        if not self._progress_indeterminate:
            self.progress_bar.setRange(0, maximum)
            self.progress_bar.setValue(value)
            self._update_progress_label()

    def _reset_progress(self):
        self._progress_log_idle_timer.stop()
        self._progress_indeterminate = False
        self._progress_last_value = -1
        self._progress_last_max = 0
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)
        self.btn_launch.setVisible(True)
        self._update_launcher_controls()

    def _prepare_failed(self, msg: str):
        self._reset_progress()
        self.log(f"!!! {msg}")
        QMessageBox.critical(self, "Запуск", msg)

    def _start_game(self, opts: Dict):
        self._reset_progress()
        self._retire_worker("launch_worker", "stop", 3000)
        self.launch_worker = LaunchWorker(opts, self)
        self.launch_worker.log_signal.connect(self.log)
        self.launch_worker.finished_signal.connect(self._launch_finished)
        self.launch_worker.finished.connect(self.launch_worker.deleteLater)
        self.launch_worker.start()
        if get_keep_launcher_visible():
            self._game_running = True
            self._update_launcher_controls()
        else:
            self.hide()

    def _stop_game(self):
        if not self._game_running or not self.launch_worker:
            return
        reply = QMessageBox.question(
            self,
            "Остановка игры",
            "Завершить Minecraft принудительно?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.launch_worker.stop()

    def _launch_finished(self, code: int):
        restore_window = not get_keep_launcher_visible()
        self._game_running = False
        self._reset_progress()
        self.log(f"=== Minecraft завершился с кодом {code} ===")
        self.launch_worker = None
        if restore_window:
            self.show()
            self.raise_()
            self.activateWindow()

    def closeEvent(self, event):
        if self._shutting_down:
            event.accept()
            return
        busy = self._worker_running(self.prepare_worker) or self._worker_running(self.launch_worker)
        if busy:
            reply = QMessageBox.question(
                self,
                "Выход",
                "Идёт установка или игра. Прервать и закрыть лаунчер?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        self.shutdown_workers()
        event.accept()
