import asyncio

from rofi_menu import constants, rofi_mode


class MetaStore:
    def __init__(self, raw_script_input):
        self.raw_script_input = raw_script_input
        self._meta = rofi_mode.parse_meta(raw_script_input)

    @property
    def selected_id(self):
        return self._meta.get("id")

    @property
    def user_input(self):
        return self.raw_script_input if not self._meta else None

    def get_state(self, item_id):
        return self._meta.get(".".join(item_id))

    def set_state(self, item_id, state):
        if state is not None:
            self._meta[".".join(item_id)] = state

    def as_dict(self):
        return self._meta


class Operation:
    def __init__(self, code, data=None):
        self.code = code
        self.data = data


class Item:
    icon = None
    text = None

    def __init__(self, text=None, **kwargs):
        self.id = kwargs.get("item_id")

        # per menu-item state
        self.state = None
        self.loaded = False

        # render options
        self.text = text or self.text
        self.icon = kwargs.get("icon", self.icon)
        self.flags = kwargs.get("flags") or set()

        # filled after attaching to menu
        self.parent_menu = None

    def clone(self):
        obj = self.__class__()
        obj.__dict__.update(self.__dict__)
        return obj

    async def build(self, parent_menu, item_id, meta):
        """
        Build a menu item.

        It also links item to concreate menu, assigns an id and returns "bound" element.
        """
        obj = self.clone()
        obj.id = obj.id or (item_id if isinstance(item_id, list) else [*parent_menu.id, item_id])
        obj.parent_menu = parent_menu
        return obj

    async def load(self, meta):
        self.state = meta.get_state(self.id)

    async def store(self, meta):
        meta.set_state(self.id, self.state)

    async def pre_render(self, meta):
        if not self.loaded:
            await self.load(meta)

    async def render(self, meta):
        return self.text if self.text is not None else "[UNDEFINED]"

    async def post_render(self, meta):
        pass

    async def handle_render(self, meta):
        await self.pre_render(meta)
        text = await self.render(meta)
        await self.post_render(meta)
        return text

    async def pre_select(self, meta):
        if not self.loaded:
            await self.load(meta)

    async def on_select(self, meta):
        return Operation(constants.OP_REFRESH_MENU)

    async def post_select(self, meta):
        await self.store(meta)

    async def handle_select(self, meta):
        await self.pre_select(meta)
        op = await self.on_select(meta)
        await self.post_select(meta)
        return op


class BackItem(Item):
    text = ".."

    async def on_select(self, meta):
        return Operation(constants.OP_BACK_TO_PARENT_MENU)


class ExitItem(Item):
    async def on_select(self, meta):
        return Operation(constants.OP_EXIT)


class NestedMenu(Item):
    def __init__(self, text=None, menu=None, **kwargs):
        super().__init__(text, **kwargs)
        self.sub_menu = menu or Menu()

    async def build(self, parent_menu, item_id, meta):
        """
        Build a menu item that can handle nested menu.

        It also links item to concreate menu, assigns an id, triggers
        building for submenu and return "bound" element.
        """
        obj = await super().build(parent_menu=parent_menu, item_id=item_id, meta=meta)
        obj.sub_menu = await self.sub_menu.build(menu_id=obj.id, meta=meta)
        return obj

    async def handle_select(self, meta):
        if meta.selected_id == self.id:
            await self.pre_select(meta)
            op = await self.on_select(meta)
            await self.post_select(meta)

        else:
            op = await self.sub_menu.propagate_select(meta)

        if op.code == constants.OP_REFRESH_MENU:
            return Operation(constants.OP_OUTPUT, await self.sub_menu.handle_render(meta))

        if op.code == constants.OP_BACK_TO_PARENT_MENU:
            return Operation(constants.OP_OUTPUT, await self.parent_menu.handle_render(meta))

        return op

    async def on_select(self, meta):
        return Operation(constants.OP_OUTPUT, await self.sub_menu.handle_render(meta))

    async def propagate_user_input(self, meta):
        op = await self.sub_menu.propagate_user_input(meta)

        if op.code == constants.OP_REFRESH_MENU:
            return Operation(constants.OP_OUTPUT, await self.sub_menu.handle_render(meta))

        if op.code == constants.OP_BACK_TO_PARENT_MENU:
            return Operation(constants.OP_OUTPUT, await self.parent_menu.handle_render(meta))

        return op


class Menu:
    prompt = "menu"
    items = ()

    def __init__(self, prompt=None, items=None, **kwargs):
        self.id = kwargs.get("menu_id")
        self.prompt = prompt or self.prompt
        self.items = items or self.items

    def clone(self):
        obj = self.__class__()
        obj.__dict__.update(self.__dict__)
        return obj

    async def build(self, menu_id, meta):
        obj = self.clone()
        obj.id = menu_id
        obj.items = await obj.build_menu_items(meta=meta)
        return obj

    async def build_menu_items(self, meta):
        items = await self.generate_menu_items(meta=meta)
        return await asyncio.gather(*[
            item.build(parent_menu=self, item_id=item.id or [*self.id, str(item_index)], meta=meta)
            for item_index, item in enumerate(items)
        ])

    async def generate_menu_items(self, meta):
        return self.items

    async def pre_render(self, meta):
        pass

    async def render(self, meta):
        rendered_items = await asyncio.gather(
            *[item.handle_render(meta) for item in self.items]
        )

        _rofi_menu = []
        for num, item in enumerate(self.items):
            if constants.FLAG_STYLE_ACTIVE in item.flags:
                _rofi_menu.append(rofi_mode.menu_active(num))
            if constants.FLAG_STYLE_URGENT in item.flags:
                _rofi_menu.append(rofi_mode.menu_urgent(num))

        common_meta = meta.as_dict()
        _rofi_menu.extend(
            rofi_mode.menu_item(
                text=text,
                icon=item.icon,
                meta_data={**common_meta, "text": text, "id": item.id},
            )
            for text, item in zip(rendered_items, self.items)
        )

        return rofi_mode.render_menu(self.prompt, *_rofi_menu)

    async def post_render(self, meta):
        if hasattr(meta, "session"):
            meta.session["last_active_menu"] = self.id

    async def handle_render(self, meta):
        await self.pre_render(meta)
        text = await self.render(meta)
        await self.post_render(meta)
        return text

    async def propagate_select(self, meta):
        item_id = meta.selected_id

        for item in self.items:
            if item.id == item_id[: len(item.id)]:
                op = await item.handle_select(meta)

                if op.code == constants.OP_REFRESH_MENU:
                    return Operation(constants.OP_OUTPUT, await self.handle_render(meta))

                return op

        return Operation(constants.OP_OUTPUT, await self.handle_render(meta))

    async def propagate_user_input(self, meta):
        menu_id = meta.session.get("last_active_menu") if hasattr(meta, "session") else None

        op = Operation(constants.OP_REFRESH_MENU)

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
            return Operation(constants.OP_OUTPUT, await self.handle_render(meta))

        return op

    async def on_user_input(self, meta):
        return Operation(constants.OP_REFRESH_MENU)
