import asyncio
from typing import Optional

from rofi_menu.constants import OP_EXIT, OP_OUTPUT
from rofi_menu.menu import Item, MetaStore, Operation


class ShellItem(Item):
    def __init__(self, text: Optional[str] = None, command: str = "echo OK", **kwargs):
        self._command = command
        self.show_output = kwargs.pop("show_output", False)
        self.detached = kwargs.pop("detached", True)
        super().__init__(text, **kwargs)

    @property
    def command(self):
        return self._command

    async def on_select(self, meta: MetaStore):
        command = f"nohup {self.command}" if self.detached else self.command

        meta.log(f"=> [shell item] Executing shell command: {command}")
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=(
                asyncio.subprocess.PIPE
                if self.show_output
                else asyncio.subprocess.DEVNULL
            ),
            stderr=asyncio.subprocess.DEVNULL,
        )
        if proc.stdout is not None:
            data = (await proc.stdout.read()).decode("utf-8")
            meta.log(f"=> [shell item] command output: {data}")
            return Operation(OP_OUTPUT, data)
        return Operation(OP_EXIT)
