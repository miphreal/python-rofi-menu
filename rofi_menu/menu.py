from __future__ import annotations

import asyncio
import json
import inspect
import sys
from typing import (
    Any,
    Awaitable,
    Callable,
    Iterable,
    List,
    Mapping,
    NewType,
    Optional,
    Set,
    Union,
    cast,
)

from rofi_menu import constants
from rofi_menu.rofi_mode import RofiMode, get_rofi_mode

ItemId = NewType("ItemId", List[str])


class MetaStore:
    debug: bool
    raw_script_input: str
    rofi_version: str
    rofi_mode: RofiMode
    _state_manager: Mapping
    _meta: dict

    def __init__(
        self, raw_script_input, rofi_version: str = "1.5", debug: bool = False
    ):
        self.rofi_version = rofi_version
        self.rofi_mode = get_rofi_mode(rofi_version)
        self.debug = debug
        self.raw_script_input = raw_script_input
        self._meta = self.rofi_mode.parse_meta(raw_script_input)
        self._state_manager = self._meta

        if debug:
            debug_meta = json.dumps(self._meta, indent=2, sort_keys=True)
            self.log(f"* Parsed meta:\n{debug_meta}\n")

    @property
    def selected_id(self) -> Optional[ItemId]:
        return self._meta.get("id")

    @property
    def user_input(self):
        return self.raw_script_input if not self._meta else None

    def as_dict(self):
        return self._meta

    @property
    def state_manager(self):
        return self._state_manager

    @state_manager.setter
    def state_manager(self, data_manager: Mapping):
        self._state_manager = data_manager

    def get_state(self, item_id):
        return self._state_manager.get(".".join(item_id))

    def set_state(self, item_id, state):
        if state is not None:
            self._state_manager[".".join(item_id)] = state

    def log(self, message: str, offset: int = 0):
        if self.debug:
            if offset:
                sys.stderr.write(" " * offset)
            sys.stderr.write(message)
            sys.stderr.write("\n")
            sys.stderr.flush()


class Operation:
    def __init__(self, code, data=None):
        self.code = code
        self.data = data

    @classmethod
    def output_menu(cls, text: str):
        return cls(constants.OP_OUTPUT, text)

    @classmethod
    def back_to_parent_menu(cls):
        return cls(constants.OP_BACK_TO_PARENT_MENU)

    @classmethod
    def refresh_menu(cls):
        return cls(constants.OP_REFRESH_MENU)

    @classmethod
    def exit(cls):
        return cls(constants.OP_EXIT)


class Item:
    id: ItemId
    icon: Optional[str] = None
    text: Optional[str] = None
    searchable_text: Optional[str] = None
    nonselectable: Optional[bool] = False
    flags: Set
    parent_menu: Optional[Menu]

    on_select_action: Optional[
        Union[
            Callable[
                [MetaStore], Union[Awaitable[Optional[Operation]], Optional[Operation]]
            ]
        ]
    ] = None

    state: Any
    loaded: bool

    def __init__(self, text: str = None, **kwargs):
        self.id = cast(ItemId, kwargs.get("item_id"))

        # per menu-item state
        self.state = None
        self.loaded = False

        # render options
        self.text = text or self.text
        self.icon = kwargs.get("icon", self.icon)
        self.searchable_text = kwargs.get("searchable_text", self.searchable_text)
        self.nonselectable = kwargs.get("nonselectable", self.nonselectable)
        self.flags = kwargs.get("flags") or set()

        # filled after attaching to menu
        self.parent_menu = None

        # behavior
        self.on_select_action = kwargs.get("on_select_action", self.on_select_action)

    def clone(self):
        obj = self.__class__()
        obj.__dict__.update(self.__dict__)
        return obj

    async def build(
        self, parent_menu: Menu, item_id: Union[ItemId, str], meta: MetaStore
    ):
        """
        Build a menu item.

        It also links item to concreate menu, assigns an id and returns "bound" element.
        """
        obj = self.clone()
        obj.id = obj.id or (
            item_id if isinstance(item_id, list) else [*parent_menu.id, item_id]
        )
        obj.parent_menu = parent_menu
        return obj

    async def load(self, meta: MetaStore):
        self.state = meta.get_state(self.id)

    async def store(self, meta: MetaStore):
        meta.set_state(self.id, self.state)

    async def pre_render(self, meta: MetaStore):
        if not self.loaded:
            await self.load(meta)

    async def render(self, meta: MetaStore):
        return self.text if self.text is not None else "[UNDEFINED]"

    async def post_render(self, meta: MetaStore):
        pass

    async def handle_render(self, meta: MetaStore):
        await self.pre_render(meta)
        text = await self.render(meta)
        await self.post_render(meta)
        return text

    async def pre_select(self, meta: MetaStore):
        if not self.loaded:
            await self.load(meta)

    async def _call_on_select_callback(self, meta: MetaStore):
        if not self.on_select_action:
            return None

        ret = self.on_select_action(meta)
        if ret and inspect.isawaitable(ret):
            return await ret
        return ret

    async def on_select(self, meta: MetaStore):
        ret = await self._call_on_select_callback(meta)
        return ret or Operation.refresh_menu()

    async def post_select(self, meta: MetaStore):
        await self.store(meta)

    async def handle_select(self, meta: MetaStore):
        await self.pre_select(meta)
        op = await self.on_select(meta)
        await self.post_select(meta)
        return op


class Delimiter(Item):
    text = "<span foreground='gray' strikethrough='true'>          </span>"
    nonselectable = True


class BackItem(Item):
    text = ".."

    async def on_select(self, meta: MetaStore):
        return Operation.back_to_parent_menu()


class ExitItem(Item):
    async def on_select(self, meta: MetaStore):
        return Operation.exit()


class NestedMenu(Item):
    sub_menu: Menu

    def __init__(self, text: str = None, menu: Menu = None, **kwargs):
        super().__init__(text, **kwargs)
        self.sub_menu = menu or Menu()

    async def build(self, parent_menu: Menu, item_id, meta: MetaStore):
        """
        Build a menu item that can handle nested menu.

        It also links item to concreate menu, assigns an id, triggers
        building for submenu and return "bound" element.
        """
        obj = await super().build(parent_menu=parent_menu, item_id=item_id, meta=meta)

        latest_menu_id = meta.state_manager.get(constants.LAST_MENU_ID_STATE_KEY)
        is_active_menu = bool(
            # It was selected
            meta.selected_id
            and item_id == meta.selected_id[: len(item_id)]
            # or user entered some text
            or meta.user_input
            and latest_menu_id
            and item_id == latest_menu_id[: len(item_id)]
        )

        if is_active_menu:
            obj.sub_menu = await self.sub_menu.build(menu_id=obj.id, meta=meta)

        return obj

    async def handle_select(self, meta: MetaStore):
        if meta.selected_id == self.id:
            await self.pre_select(meta)
            op = await self.on_select(meta)
            await self.post_select(meta)

        else:
            op = await self.sub_menu.propagate_select(meta)

        if op.code == constants.OP_REFRESH_MENU:
            return Operation.output_menu(await self.sub_menu.handle_render(meta))

        if op.code == constants.OP_BACK_TO_PARENT_MENU:
            return Operation.output_menu(
                await cast(Menu, self.parent_menu).handle_render(meta),
            )

        return op

    async def on_select(self, meta: MetaStore):
        return Operation.output_menu(await self.sub_menu.handle_render(meta))

    async def propagate_user_input(self, meta: MetaStore):
        op = await self.sub_menu.propagate_user_input(meta)

        if op.code == constants.OP_REFRESH_MENU:
            return Operation.output_menu(await self.sub_menu.handle_render(meta))

        if op.code == constants.OP_BACK_TO_PARENT_MENU:
            return Operation.output_menu(
                await cast(Menu, self.parent_menu).handle_render(meta),
            )

        return op


class Menu:
    id: ItemId
    prompt: str = "menu"
    items: Iterable[Item] = ()
    allow_user_input: bool = False

    def __init__(
        self,
        prompt: str = None,
        items: Iterable[Item] = None,
        allow_user_input: bool = None,
        **kwargs,
    ):
        self.id = cast(ItemId, kwargs.get("menu_id"))
        self.prompt = prompt or self.prompt
        self.items = items or self.items
        self.allow_user_input = (
            allow_user_input if allow_user_input is not None else self.allow_user_input
        )

    def clone(self):
        obj = self.__class__()
        obj.__dict__.update(self.__dict__)
        return obj

    async def build(self, menu_id, meta: MetaStore):
        obj = self.clone()
        obj.id = menu_id
        obj.items = await obj.build_menu_items(meta=meta)

        if meta.debug:
            meta.log("[build menu]", offset=len(menu_id) - 1)
            for item in obj.items:
                meta.log(f"[item] {item.text} {item.id}", offset=len(item.id) - 1)

        return obj

    async def build_menu_items(self, meta: MetaStore):
        items = await self.generate_menu_items(meta=meta)
        return await asyncio.gather(
            *[
                item.build(
                    parent_menu=self,
                    item_id=item.id or [*self.id, str(item_index)],
                    meta=meta,
                )
                for item_index, item in enumerate(items)
            ]
        )

    async def generate_menu_items(self, meta: MetaStore):
        return self.items

    async def pre_render(self, meta: MetaStore):
        pass

    async def render(self, meta: MetaStore):
        rendered_items = await asyncio.gather(
            *[item.handle_render(meta) for item in self.items]
        )

        _rofi_menu = [
            meta.rofi_mode.menu_prompt(self.prompt),
            meta.rofi_mode.menu_enable_markup(),
            meta.rofi_mode.menu_no_input(not self.allow_user_input),
        ]

        for num, item in enumerate(self.items):
            if constants.FLAG_STYLE_ACTIVE in item.flags:
                _rofi_menu.append(meta.rofi_mode.menu_active(num))
            if constants.FLAG_STYLE_URGENT in item.flags:
                _rofi_menu.append(meta.rofi_mode.menu_urgent(num))

        shared_meta = meta.as_dict()
        _rofi_menu.extend(
            meta.rofi_mode.menu_item(
                text=text,
                icon=item.icon,
                searchable_text=item.searchable_text,
                nonselectable=item.nonselectable,
                meta_data={**shared_meta, "text": text, "id": item.id},
            )
            for text, item in zip(rendered_items, self.items)
        )

        return meta.rofi_mode.render_menu(*_rofi_menu)

    async def post_render(self, meta: MetaStore):
        meta.state_manager[constants.LAST_MENU_ID_STATE_KEY] = self.id

    async def handle_render(self, meta: MetaStore):
        await self.pre_render(meta)
        text = await self.render(meta)
        await self.post_render(meta)
        return text

    async def propagate_select(self, meta: MetaStore):
        item_id = cast(ItemId, meta.selected_id)

        for item in self.items:
            if item.id == item_id[: len(item.id)]:
                op = await item.handle_select(meta)

                if op.code == constants.OP_REFRESH_MENU:
                    return Operation.output_menu(await self.handle_render(meta))

                return op

        return Operation.output_menu(await self.handle_render(meta))

    async def propagate_user_input(self, meta: MetaStore) -> Operation:
        menu_id = meta.state_manager.get(constants.LAST_MENU_ID_STATE_KEY, None)

        op = Operation.refresh_menu()

        if menu_id is None or menu_id == self.id:
            # Found the target menu which should handle user input.
            op = await self.on_user_input(meta)

        else:
            # Need to propagate user input down the menu tree.
            for item in self.items:
                if isinstance(item, NestedMenu) and item.id == menu_id[: len(item.id)]:
                    op = await item.propagate_user_input(meta)
                    break

        if op.code == constants.OP_REFRESH_MENU:
            return Operation.output_menu(await self.handle_render(meta))

        return op

    async def on_user_input(self, meta: MetaStore):
        return Operation.refresh_menu()
