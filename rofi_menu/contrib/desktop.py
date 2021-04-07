import configparser
import pathlib
import re

from rofi_menu.contrib.shell import ShellItem
from rofi_menu.menu import Menu


# Desktop Entry spec (.desktop files)
# https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html


class DesktopItem(ShellItem):
    # See https://specifications.freedesktop.org/desktop-entry-spec/latest/ar01s07.html
    # for the desktop entry params that the `exec` may contain.
    re_exec_params = re.compile(r"%\w")

    def __init__(
        self,
        app=None,
        app_name_format=None,
        command_format=None,
        trim_exec_desktop_entry_params=True,
        terminal_exec=None,
        **kwargs
    ):
        app = app or {"name": "Undefined", "exec": "echo OK", "comment": None}
        text = self._format_text(app, app_name_format)
        command = self._format_command(
            app, command_format, trim_exec_desktop_entry_params, terminal_exec
        )
        kwargs.setdefault("icon", app.get("icon"))
        kwargs.setdefault("searchable_text", app.get("comment"))
        super().__init__(text=text, command=command, **kwargs)

    def _format_text(self, app, text_format):
        return (text_format or "{name}").format(**app)

    def _format_command(
        self, app, command_format, trim_exec_desktop_entry_params, terminal_exec
    ):
        command = (command_format or "{exec}").format(**app)
        if trim_exec_desktop_entry_params:
            command = self.re_exec_params.sub("", command).strip()

        if app.get("terminal") and terminal_exec:
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

    def lookup_for_applications(self, meta):
        for location in self._lookup_directores:
            for item in pathlib.Path(location).glob("**/*.desktop"):
                desktop_file = configparser.RawConfigParser(strict=False)
                desktop_file.read(item)
                if "Desktop Entry" in desktop_file:
                    section = desktop_file["Desktop Entry"]
                    app = {
                        "type": section["Type"],
                        "name": section["Name"],
                        "generic_name": section.get("Generic Name"),
                        "comment": section.get("Comment"),
                        "keywords": section.get("Keywords", "").split(";"),
                        "categories": section.get("Categories", "").split(";"),
                        "path": section.get("Path"),
                        "exec": section.get("Exec"),
                        "url": section.get("URL"),
                        "icon": section.get("Icon"),
                        "terminal": section.get("Terminal") == "true",
                        "hidden": section.get("Hidden") == "true",
                    }

                    yield app

    async def generate_menu_items(self, meta):
        apps = self.lookup_for_applications(meta)
        if self._sort_menu:
            apps = sorted(apps, key=lambda item: item["name"])

        return [
            DesktopItem(
                app,
                app_name_format=self._app_name_format,
                command_format=self._command_format,
                trim_exec_desktop_entry_params=self._trim_exec_desktop_entry_params,
                terminal_exec=self._terminal_exec,
            )
            for app in apps
            if not app["hidden"] and app["type"] == "Application"
        ]
