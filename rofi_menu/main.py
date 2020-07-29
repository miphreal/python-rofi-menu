import asyncio
import sys

from rofi_menu.constants import ROOT_MENU_ID, OP_EXIT, OP_OUTPUT
from rofi_menu.menu import MetaStore, Menu
from rofi_menu.session import FileSession


def _output_menu(data: str) -> None:
    sys.stdout.write(data)


async def main(menu: Menu, selected_item: str, session_store = None) -> None:
    session = FileSession() if session_store is None else session_store
    await session.load()

    if not selected_item:
        # first run of the script (no passed params) => we can start new session
        session.clear()
        await session.save()

    meta = MetaStore(selected_item, session=session)

    menu = await menu.bind(meta=meta, prefix_path=[ROOT_MENU_ID])

    if selected_item:
        if meta.selected_id:
            op = await menu.propagate_select(meta.selected_id, meta)
        else:
            last_selected_menu_id = session.get("last_selected_menu", None)
            op = await menu.propagate_user_input(last_selected_menu_id, meta.user_input, meta)

        if op.code == OP_OUTPUT:
            _output_menu(op.data)

        elif op.code == OP_EXIT:
            exit(op.data or 1)

    else:
        _output_menu(await menu.handle_render(meta))

    await session.save()


def run(menu: Menu) -> None:
    asyncio.run(main(menu, sys.argv[1] if len(sys.argv) > 1 else None))
