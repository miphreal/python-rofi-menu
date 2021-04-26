import configparser
import dataclasses
import pathlib
import re
from typing import List, Optional

from rofi_menu.contrib.shell import ShellItem
from rofi_menu.menu import Menu, MetaStore


@dataclasses.dataclass
class AppData:
    name: str
    keywords: List[str]
    categories: List[str]
    terminal: bool = False
    hidden: bool = False
    type: str = "Application"
    generic_name: Optional[str] = None
    comment: Optional[str] = None
    icon: Optional[str] = None
    path: Optional[str] = None
    exec: Optional[str] = None
    url: Optional[str] = None


# Desktop Entry spec (.desktop files)
# https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html


class DesktopItem(ShellItem):
    # See https://specifications.freedesktop.org/desktop-entry-spec/latest/ar01s07.html
    # for the desktop entry params that the `exec` may contain.
    re_exec_params = re.compile(r"%\w")

    def __init__(
        self,
        app: Optional[AppData] = None,
        app_name_format=None,
        command_format=None,
        trim_exec_desktop_entry_params=True,
        terminal_exec=None,
        **kwargs
    ):
        app = app or AppData(name="Undefined", keywords=[], categories=[])
        text = self._format_text(app, app_name_format)
        command = self._format_command(
            app, command_format, trim_exec_desktop_entry_params, terminal_exec
        )
        kwargs.setdefault("icon", app.icon)
        kwargs.setdefault("searchable_text", app.comment)
        super().__init__(text=text, command=command, **kwargs)

    def _format_text(self, app: AppData, text_format: str):
        return (text_format or "{app.name}").format(app=app)

    def _format_command(
        self,
        app: AppData,
        command_format: Optional[str],
        trim_exec_desktop_entry_params: bool,
        terminal_exec: Optional[str],
    ):
        command = (command_format or "{app.exec}").format(app=app)
        if trim_exec_desktop_entry_params:
            command = self.re_exec_params.sub("", command).strip()

        if app.terminal and terminal_exec:
            command = terminal_exec.format(command=command)

        return command


class DesktopMenu(Menu):
    def __init__(
        self,
        prompt=None,
        lookup_directories=None,
        app_name_format=None,
        command_format=None,
        trim_exec_desktop_entry_params=True,
        terminal_exec="gnome-terminal -- {command}",
        sort_menu=True,
        **kwargs
    ):
        self._lookup_directores = lookup_directories or [
            "/usr/share/applications",
            "/usr/local/share/applications",
            "~/.local/share/applications",
        ]
        self._app_name_format = app_name_format
        self._command_format = command_format
        self._trim_exec_desktop_entry_params = trim_exec_desktop_entry_params
        self._terminal_exec = terminal_exec
        self._sort_menu = sort_menu

        super().__init__(prompt=prompt, items=[], allow_user_input=False, **kwargs)

    def lookup_for_applications(self, meta: MetaStore):
        for location in self._lookup_directores:
            for item in pathlib.Path(location).glob("**/*.desktop"):
                desktop_file = configparser.RawConfigParser(strict=False)
                desktop_file.read(item)
                if "Desktop Entry" in desktop_file:
                    section = desktop_file["Desktop Entry"]
                    app = AppData(
                        type=section["Type"],
                        name=section["Name"],
                        generic_name=section.get("Generic Name"),
                        comment=section.get("Comment"),
                        keywords=section.get("Keywords", "").split(";"),
                        categories=section.get("Categories", "").split(";"),
                        path=section.get("Path"),
                        exec=section.get("Exec"),
                        url=section.get("URL"),
                        icon=section.get("Icon"),
                        terminal=section.get("Terminal") == "true",
                        hidden=section.get("Hidden") == "true",
                    )

                    yield app

    async def generate_menu_items(self, meta: MetaStore):
        apps = self.lookup_for_applications(meta)
        if self._sort_menu:
            apps = sorted(apps, key=lambda item: item.name)

        return [
            DesktopItem(
                app,
                app_name_format=self._app_name_format,
                command_format=self._command_format,
                trim_exec_desktop_entry_params=self._trim_exec_desktop_entry_params,
                terminal_exec=self._terminal_exec,
            )
            for app in apps
            if not app.hidden and app.type == "Application"
        ]
