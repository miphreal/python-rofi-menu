import asyncio
import sys
import os

from rofi_menu.constants import ROOT_MENU_ID, OP_EXIT, OP_OUTPUT
from rofi_menu.menu import MetaStore, Menu
from rofi_menu.session import FileSession, session_middleware


def _output_menu(data: str, meta: MetaStore) -> None:
    sys.stdout.write(data)

    if meta.debug:
        sys.stderr.write("{===== Menu output:\n")
        sys.stderr.writelines(f"{line!r}\n" for line in data.split("\n"))
        sys.stderr.write("\n}===== End menu output.\n")


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

        if meta.debug:
            sys.stderr.write(f"Result: {op.code}\n")

        if op.code == OP_OUTPUT:
            _output_menu(op.data, meta)

        elif op.code == OP_EXIT:
            exit(op.data or 1)

    else:
        _output_menu(await menu.handle_render(meta), meta)


def run(
    menu: Menu,
    stateful: bool = True,
    middlewares=None,
    rofi_version="1.6",
    debug: bool = False,
) -> None:
    """Shortcut for running menu generation."""
    if debug:
        sys.stderr.writelines(
            [
                f"\n\n=> Script call \n",
                f"* Configured to work with Rofi v{rofi_version}\n",
                f"* Debug mode: {debug}\n",
                f"* Stateful script mode: {stateful}\n",
                f"* Script params {sys.argv[1:]}\n",
                f"* Script envs:\n",
                f"\tROFI_OUTSIDE={os.getenv('ROFI_OUTSIDE')}\n",
                f"\tROFI_RETV={os.getenv('ROFI_RETV')}\n",
                f"\tROFI_INFO={os.getenv('ROFI_INFO')}\n",
            ]
        )

    meta = MetaStore(
        sys.argv[1] if len(sys.argv) > 1 else None,
        rofi_version=rofi_version,
        debug=debug,
    )

    middlewares = list(middlewares or [])
    if stateful:
        middlewares.append(session_middleware(FileSession()))

    handler = main
    for middleware in middlewares:
        handler = middleware(handler)

    asyncio.run(handler(menu=menu, meta=meta))
