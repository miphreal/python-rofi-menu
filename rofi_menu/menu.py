import asyncio

from rofi_menu import constants, rofi_mode


class MetaStore:
    def __init__(self, selected_item):
        self.raw_input = selected_item
        self._meta = rofi_mode.parse_meta(selected_item)

    @property
    def selected_id(self):
        return self._meta.get("id")

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

    def __init__(self, text=None, *, flags=None):
        self.text = text or self.text
        self.flags = flags or set()

        # filled after attaching to menu
        self.id = None
        self.parent_menu = None
        self.state = None

        self.loaded = False

    def clone(self):
        obj = self.__class__()
        obj.__dict__.update(self.__dict__)
        return obj

    async def bind(self, menu, item_id, meta):
        """Link item to concreate menu, assign an id and return "bound" element."""
        obj = self.clone()
        obj.id = item_id
        obj.parent_menu = menu
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

    async def on_select(self, item_id, meta):
        return Operation(constants.OP_REFRESH_MENU)

    async def post_select(self, meta):
        await self.store(meta)

    async def handle_select(self, item_id, meta):
        await self.pre_select(meta)
        op = await self.on_select(item_id, meta)
        await self.post_select(meta)
        return op


class BackItem(Item):
    text = ".."

    async def on_select(self, item_id, meta):
        return Operation(constants.OP_BACK_TO_PARENT_MENU)


class ExitItem(Item):
    async def on_select(self, item_id, meta):
        return Operation(constants.OP_EXIT)


class NestedMenu(Item):
    def __init__(self, text=None, menu=None, *, flags=None):
        super().__init__(text, flags=flags)
        self.sub_menu = menu or Menu()

    async def bind(self, menu, item_id, meta):
        """
        Link item to concreate menu, assign an id, initiate linking for submenu
        and return "bound" element.
        """
        obj = self.clone()
        obj.id = item_id
        obj.parent_menu = menu
        obj.sub_menu = await self.sub_menu.bind(prefix_path=item_id, meta=meta)
        return obj

    async def on_select(self, item_id, meta):
        if item_id == self.id:
            return Operation(constants.OP_OUTPUT, await self.sub_menu.render(meta))

        await self.sub_menu.pre_select(meta)
        op = await self.sub_menu.on_select(item_id, meta)
        await self.sub_menu.post_select(meta)

        if op.code == constants.OP_REFRESH_MENU:
            return Operation(constants.OP_OUTPUT, await self.sub_menu.render(meta))

        if op.code == constants.OP_BACK_TO_PARENT_MENU:
            return Operation(constants.OP_OUTPUT, await self.parent_menu.render(meta))

        return op


class Menu:
    prompt = "menu"
    items = ()

    def __init__(self, prompt=None, items=None):
        self.prompt = prompt or self.prompt
        self.items = items or self.items

    def clone(self):
        obj = self.__class__()
        obj.__dict__.update(self.__dict__)
        return obj

    async def bind(self, prefix_path, meta):
        """Link all nested items to the current menu and return "bound" element."""
        items = await self.generate_menu_items(prefix_path=prefix_path, meta=meta)
        # generate bound items
        obj = self.clone()
        obj.items = await asyncio.gather(*[
            item.bind(menu=obj, item_id=[*prefix_path, str(item_identity)], meta=meta)
            for item_identity, item in items
        ])
        return obj

    async def generate_menu_items(self, prefix_path, meta):
        return enumerate(self.items)

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
        pass

    async def handle_render(self, meta):
        await self.pre_render(meta)
        text = await self.render(meta)
        await self.post_render(meta)
        return text

    async def pre_select(self, meta):
        pass

    async def on_select(self, item_id, meta):
        for item in self.items:
            if item.id == item_id[: len(item.id)]:
                op = await item.handle_select(item_id, meta)

                if op.code == constants.OP_REFRESH_MENU:
                    return Operation(constants.OP_OUTPUT, await self.render(meta))

                return op

        return Operation(constants.OP_OUTPUT, await self.render(meta))

    async def post_select(self, meta):
        pass

    async def handle_select(self, item_id, meta):
        await self.pre_select(meta)
        op = await self.on_select(item_id, meta)
        await self.post_select(meta)
        return op
