from typing import Protocol, Optional


class RofiMode(Protocol):
    def render_menu(self, prompt: str, *items) -> str:
        ...

    def menu_prompt(self, text: str) -> str:
        ...

    def menu_enable_markup(self,) -> str:
        ...

    def menu_message(self, text: str) -> str:
        ...

    def menu_urgent(self, num: int) -> str:
        ...

    def menu_active(self, num: int) -> str:
        ...

    def menu_no_input(self, val: bool = True) -> str:
        ...

    def menu_item(
        self,
        text: str,
        icon: Optional[str] = None,
        searchable_text: Optional[str] = None,
        nonselectable: Optional[bool] = None,
        meta_data: Optional[dict] = None,
    ) -> str:
        ...

    def parse_meta(self, selected_item: str) -> dict:
        ...
