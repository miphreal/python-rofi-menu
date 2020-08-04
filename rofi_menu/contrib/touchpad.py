import asyncio
import re

from rofi_menu.contrib.shell import ShellItem


class TouchpadItem(ShellItem):
    shell_cmd_device_id = (
        rf'$(xinput list | grep -Po "Touchpad.*id=\d+" | grep -Po "\d+")'
    )
    re_enabled_device = re.compile(r"Device Enabled.*:\t1")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.detached = False
        self.show_output = False

    def get_icon(self, is_touchpad_enabled: bool):
        return "input-touchpad-symbolic" if is_touchpad_enabled else "touchpad-disabled-symbolic"

    @property
    def command(self):
        action = "enable" if self.state else "disable"
        return rf"xinput {action} " + self.shell_cmd_device_id

    async def load(self, meta):
        proc = await asyncio.create_subprocess_shell(
            rf"xinput list-props " + self.shell_cmd_device_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        data = (await proc.stdout.read()).decode("utf-8")
        self.state = bool(self.re_enabled_device.search(data))
        self.icon = self.get_icon(is_touchpad_enabled=self.state)

    async def render(self, *args, **kwargs):
        state_on = '<span background="green"><b>ON</b></span>'
        state_off = '<span background="gray"><b>OFF</b></span>'
        return f"Touchpad [{self.state and state_on or state_off}]"

    async def on_select(self, *args, **kwargs):
        self.state = not self.state
        return await super().on_select(*args, **kwargs)
