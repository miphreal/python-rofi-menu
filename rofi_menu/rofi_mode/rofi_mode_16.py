"""
Rofi script mode for version >=16
"""
import base64
import json
import os
from rofi_menu.menu import Operation
from typing import Optional


def render_menu(prompt: str, *items) -> str:
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


def menu_no_input(val: bool = True) -> str:
    return "\0no-custom\x1f" + ("true" if val else "false")


def menu_entry(text, **fields):
    if not fields:
        return text

    fields_data = "\x1f".join([f"{name}\x1f{val}" for name, val in fields.items()])
    return f"{text}\x00{fields_data}"


def menu_item(
    text: str,
    icon: Optional[str] = None,
    searchable_text: Optional[str] = None,
    nonselectable: Optional[bool] = None,
    meta_data: Optional[dict] = None,
) -> str:

    fields = {}

    if icon is not None:
        fields["icon"] = icon

    if searchable_text is not None:
        fields["meta"] = searchable_text

    if nonselectable is not None:
        fields["nonselectable"] = "true" if nonselectable else "false"

    info = base64.urlsafe_b64encode(json.dumps(meta_data).encode("utf-8")).decode(
        "utf-8"
    )
    fields["info"] = info

    return menu_entry(text, **fields)


def parse_meta(selected_item: str) -> dict:
    rofi_retv = os.getenv("ROFI_RETV")
    rofi_info = os.getenv("ROFI_INFO")

    if rofi_retv == "1":
        return json.loads(base64.urlsafe_b64decode(rofi_info))

    return {}
