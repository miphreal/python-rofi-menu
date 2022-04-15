import asyncio
import os
import sys
from typing import Iterable, List, Optional, Union

from rofi_menu.constants import OP_EXIT, OP_OUTPUT, ROOT_MENU_ID
from rofi_menu.menu import Menu, MetaStore, Item, Delimiter, NestedMenu
from rofi_menu.session import FileSession, session_middleware


def _output_menu(data: str, meta: MetaStore) -> None:
    sys.stdout.write(data)

    meta.log("=> Menu output:")
    meta.log("".join(f"{line!r}\n" for line in data.split("\n")))


async def main(menu: Menu, meta: MetaStore) -> None:
    menu = await menu.build(menu_id=[ROOT_MENU_ID], meta=meta)

    if meta.raw_script_input:
        if meta.selected_id:
            # User selected a menu item, so we'll need to find corresponding
            # menu item and delegate handling of selection.
            meta.log(f"=> [rofi menu] User selected item: {meta.selected_id}")
            op = await menu.propagate_select(meta)
        else:
            # User entered a text and hasn't selected any menu item.
            meta.log(f"=> [rofi menu] User entered text: {meta.user_input}")
            op = await menu.propagate_user_input(meta)

        meta.log(f"=> [rofi menu result] Operation: {op.code}")
        meta.log(f"=> [rofi menu result] Data: {op.data!r}")

        if op.code == OP_OUTPUT:
            _output_menu(op.data, meta)

        elif op.code == OP_EXIT:
            # It'll take an effect on Rofi only if stdout is empty
            exit(op.data or 1)

    else:
        _output_menu(await menu.handle_render(meta), meta)


def run(
    menu: Menu,
    stateful: Union[bool, str] = True,
    middlewares=None,
    rofi_version="1.6",
    debug: bool = False,
) -> None:
    """Shortcut for running menu generation."""
    if debug:
        sys.stderr.writelines(
            [
                "\n\n",
                "================\n",
                "=> Script call =\n",
                "================\n",
                f"* Configured to work with Rofi v{rofi_version}\n",
                f"* Debug mode: {debug}\n",
                f"* Stateful script mode: {stateful}\n",
                f"* Script params {sys.argv[1:]}\n",
                f"* Script envs:\n",
                f"\tROFI_OUTSIDE={os.getenv('ROFI_OUTSIDE')}\n",
                f"\tROFI_RETV={os.getenv('ROFI_RETV')}\n",
                f"\tROFI_INFO={os.getenv('ROFI_INFO')}\n",
                f"\tROFI_DATA={os.getenv('ROFI_DATA')}\n",
            ]
        )

    meta = MetaStore(
        sys.argv[1] if len(sys.argv) > 1 else None,
        rofi_version=rofi_version,
        debug=debug,
    )

    middlewares = list(middlewares or [])
    if stateful:
        middlewares.append(
            session_middleware(FileSession(), clear_session=stateful != "lifetime")
        )

    handler = main
    for middleware in middlewares:
        handler = middleware(handler)

    asyncio.run(handler(menu=menu, meta=meta))


def build_spec_menu(spec: Iterable, prompt: Optional[str] = None) -> Menu:
    from rofi_menu import Item, ShellItem, BackItem, ExitItem

    items: List[Item] = []

    if isinstance(spec, dict):
        spec = spec.items()

    for item in spec:
        text, action, *rest = item
        kw = rest[0] if rest and isinstance(rest[0], dict) else {}

        if isinstance(action, str):
            if action == "..":
                items.append(BackItem(text))
            elif action in {"-", "--", "---"}:
                items.append(Delimiter())
            elif action == "exit":
                items.append(ExitItem(text))
            else:
                items.append(ShellItem(text=text, command=action, **kw))
        elif callable(action):
            items.append(Item(text=text, on_select_action=action, **kw))
        elif isinstance(action, Iterable):
            items.append(
                NestedMenu(
                    text=text, menu=build_spec_menu(spec=action, prompt=prompt), **kw
                )
            )

    return Menu(prompt=prompt, items=items)


def run_spec(spec: Iterable, prompt=None, **kwargs):
    run(menu=build_spec_menu(spec=spec, prompt=prompt), **kwargs)
