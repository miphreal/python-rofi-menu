import asyncio
import sys

from rofi_menu.constants import ROOT_MENU_ID, OP_EXIT, OP_OUTPUT
from rofi_menu.menu import MetaStore


def _output_menu(data):
    sys.stdout.write(data)


async def main(menu, selected_item):
    meta = MetaStore(selected_item)

    menu = await menu.bind(meta=meta, prefix_path=[ROOT_MENU_ID])

    if selected_item:
        op = await menu.handle_select(meta.selected_id, meta)

        if op.code == OP_OUTPUT:
            return _output_menu(op.data)

        elif op.code == OP_EXIT:
            exit(op.data or 1)

    _output_menu(await menu.handle_render(meta))


def run(menu):
    asyncio.run(main(menu, sys.argv[1] if len(sys.argv) > 1 else None))
