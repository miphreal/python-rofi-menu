import os
import pathlib
import subprocess
import sys
import time

from PIL import Image, ImageChops
import pytest
from pyvirtualdisplay.smartdisplay import SmartDisplay
import pytesseract


@pytest.fixture(scope="session")
def display():
    try:
        with SmartDisplay(backend="xvfb") as disp:
            yield disp
    except:
        pass


class RofiInstance:
    def __init__(self, display, pytest_info, **kwargs):
        self.proc = run_rofi(**kwargs)
        self.display = display
        self.pytest_info = pytest_info

    def kill(self):
        self.proc.kill()

    def type(self, text: str):
        run_cmd(f'xdotool type {text}')

    def enter(self):
        run_cmd(f'xdotool key Return')

    @property
    def screenshot(self):
        return self.display.waitgrab()

    @property
    def text_ocr(self):
        return pytesseract.image_to_string(self.screenshot)

    def check_snapshot(self, title: str):
        current_snapshot = self.screenshot
        test_id = self.pytest_info.node.nodeid.rpartition('::')[-1]
        test_module_path = self.pytest_info.fspath
        snapshot_path = (
            pathlib.Path(test_module_path.dirpath()) /
            'snapshots' /
            test_module_path.basename[:-len(test_module_path.ext)] /
            f'{test_id} - {title}.png'
        )
        assert snapshot_path.exists() or os.getenv('REGENERATE_SNAPSHOTS', 'False').lower() == 'true'

        if snapshot_path.exists():
            snapshot = Image.open(snapshot_path)
            assert ImageChops.difference(current_snapshot, snapshot).getbbox() is None
        else:
            print(f"Saving snapshot for '{title}' step.")
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            current_snapshot.save(snapshot_path)


def run_async_cmd(cmd):
    print(f"Running async shell command: {cmd}")
    proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    time.sleep(0.5)  # give the process some time to startup
    return proc


def run_cmd(cmd):
    print(f"Running sync shell command: {cmd}")
    return subprocess.run(cmd, shell=True)


def run_rofi(script_bin, mode_name='menu', python_bin=sys.executable, rofi_bin='rofi', rofi_params=''):
    return run_async_cmd(f'{rofi_bin} {rofi_params} -show {mode_name} -modi "{mode_name}:{python_bin} {script_bin}"')

@pytest.fixture
def rofi_instance(tmp_path, display, request):
    script_bin = tmp_path / 'script.py'

    instance = None

    def _run(script_code: str, **kwargs):
        nonlocal instance
        if instance is not None:
            instance.kill()

        with script_bin.open('wt') as f:
            f.write(script_code)

        instance = RofiInstance(script_bin=script_bin, display=display, pytest_info=request, **kwargs)
        return instance

    try:
        yield _run
    except:
        if instance is not None:
            instance.kill()


def test_rofi(rofi_instance):
    rofi: RofiInstance = rofi_instance("""
import rofi_menu


class ProjectsMenu(rofi_menu.Menu):
    prompt = "Projects"
    items = [
        rofi_menu.BackItem(),
        rofi_menu.ShellItem("Project 1", "code-insiders ~/Develop/project1"),
        rofi_menu.ShellItem("Project 2", "code-insiders ~/Develop/project2"),
        rofi_menu.Delimiter(),
        rofi_menu.ShellItem("Project X", "code-insiders ~/Develop/projectx"),
    ]


class LogoutMenu(rofi_menu.Menu):
    prompt = "Logout"
    items = [
        rofi_menu.ShellItem("Yes", "i3-msg exit", flags={rofi_menu.FLAG_STYLE_URGENT}),
        rofi_menu.ExitItem("No", flags={rofi_menu.FLAG_STYLE_ACTIVE}),
    ]


class MainMenu(rofi_menu.Menu):
    prompt = "menu"
    items = [
        rofi_menu.TouchpadItem(),
        rofi_menu.NestedMenu("Projects >", ProjectsMenu()),
        rofi_menu.ShellItem(
            "Downloads (show size)", "du -csh ~/Downloads", show_output=True
        ),
        rofi_menu.NestedMenu("Second monitor", rofi_menu.SecondMonitorMenu()),
        rofi_menu.ShellItem("Lock screen", "i3lock -i ~/.config/i3/bg.png"),
        rofi_menu.ShellItem("Sleep", "systemctl suspend"),
        rofi_menu.NestedMenu("Logout", LogoutMenu()),
    ]


if __name__ == "__main__":
    rofi_menu.run(MainMenu(), rofi_version="1.6", debug=True)
    """)
    rofi.type('Projects')
    rofi.enter()
    print(rofi.text_ocr)

    rofi.check_snapshot('Projects view')

    assert "project x" in rofi.text_ocr.lower()
