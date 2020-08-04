import asyncio

from rofi_menu.constants import OP_EXIT, OP_OUTPUT
from rofi_menu.menu import Item, Operation


class ShellItem(Item):
    def __init__(self, text=None, command="echo OK", **kwargs):
        self._command = command
        self.show_output = kwargs.pop("show_output", False)
        self.detached = kwargs.pop("detached", True)
        super().__init__(text, **kwargs)

    @property
    def command(self):
        return self._command

    async def on_select(self, meta):
        command = f"nohup {self.command}" if self.detached else self.command
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=(
                asyncio.subprocess.PIPE
                if self.show_output
                else asyncio.subprocess.DEVNULL
            ),
            stderr=asyncio.subprocess.DEVNULL,
        )
        if self.show_output:
            data = await proc.stdout.read()
            return Operation(OP_OUTPUT, data.decode("utf-8"))
        return Operation(OP_EXIT)
