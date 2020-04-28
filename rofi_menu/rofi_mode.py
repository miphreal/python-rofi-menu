import base64
import json
from typing import Optional

from rofi_menu.constants import MENU_ITEM_META_DELIM


def render_menu(prompt: str, *items) -> str:
    items = [menu_prompt(prompt), menu_enable_markup(), *items]
    return "\n".join(items)


def menu_prompt(text: str) -> str:
    return f"\x00prompt\x1f{text}"


def menu_enable_markup() -> str:
    return "\0markup-rows\x1ftrue"


def menu_message(text: str) -> str:
    return f"\0message\x1f{text}"


def menu_urgent(num: int) -> str:
    return f"\0urgent\x1f{num}"


def menu_active(num: int) -> str:
    return f"\0active\x1f{num}"


def menu_icon(text: str, icon: str) -> str:
    return f"{text}\0icon\x1f{icon}"


##
# Extending rofi
# Add meta data along all menu items


def menu_item(
    text: str, icon: Optional[str] = None, meta_data: Optional[dict] = None
) -> str:
    meta = json.dumps(meta_data)
    meta = base64.urlsafe_b64encode(meta.encode()).decode("utf8")
    text_with_meta = f"{text}{MENU_ITEM_META_DELIM}{meta}"
    if icon is not None:
        return menu_icon(text_with_meta, icon)
    return text_with_meta


def parse_meta(selected_item: str) -> dict:
    meta = None

    if isinstance(selected_item, str):
        meta = selected_item.partition(MENU_ITEM_META_DELIM)[-1]

    if meta:
        return json.loads(base64.urlsafe_b64decode(meta))
    return {}
