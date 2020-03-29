import base64
import json

from rofi_menu.constants import MENU_ITEM_META_DELIM


def render_menu(prompt, *items):
    items = [menu_prompt(prompt), menu_enable_markup(), *items]
    return "\n".join(items)


def menu_prompt(text):
    return f"\x00prompt\x1f{text}"


def menu_enable_markup():
    return "\0markup-rows\x1ftrue"


def menu_message(text):
    return f"\0message\x1f{text}"


def menu_urgent(num):
    return f"\0urgent\x1f{num}"


def menu_active(num):
    return f"\0active\x1f{num}"


##
# Extending rofi
# Add meta data along all menu items


def menu_item(text, meta_data=None):
    meta = json.dumps(meta_data)
    meta = base64.urlsafe_b64encode(meta.encode()).decode("utf8")
    return f"{text}{MENU_ITEM_META_DELIM}{meta}"


def parse_meta(selected_item):
    meta = None

    if isinstance(selected_item, str):
        meta = selected_item.partition(MENU_ITEM_META_DELIM)[-1]

    if meta:
        return json.loads(base64.urlsafe_b64decode(meta))
    return {}
