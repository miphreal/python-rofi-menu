import asyncio
import sys

from rofi_menu.constants import ROOT_MENU_ID, OP_EXIT, OP_OUTPUT
from rofi_menu.menu import MetaStore, Menu
from rofi_menu.session import FileSession, session_middleware


def _output_menu(data: str) -> None:
    sys.stdout.write(data)


async def main(menu: Menu, meta: MetaStore) -> None:
    menu = await menu.build(menu_id=[ROOT_MENU_ID], meta=meta)

    if meta.raw_script_input:
        if meta.selected_id:
            # User selected a menu item, so we'll need to find corresponding
            # menu item and delegate handling of selection.
            op = await menu.propagate_select(meta)
        else:
            # User entered a text and hasn't selected any menu item.
            op = await menu.propagate_user_input(meta)

        if op.code == OP_OUTPUT:
            _output_menu(op.data)

        elif op.code == OP_EXIT:
            exit(op.data or 1)

    else:
        _output_menu(await menu.handle_render(meta))


def run(menu: Menu, stateful: bool=True, middlewares=None) -> None:
    """Shortcut for running menu generation."""
    meta = MetaStore(sys.argv[1] if len(sys.argv) > 1 else None)

    middlewares = list(middlewares or [])
    if stateful:
        middlewares.append(session_middleware(FileSession()))

    handler = main
    for middleware in middlewares:
        handler = middleware(handler)

    asyncio.run(handler(menu=menu, meta=meta))
