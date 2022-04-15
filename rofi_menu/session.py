from __future__ import annotations

import abc
import collections.abc
import getpass
import hashlib
import json
import pathlib
import sys
import typing

from rofi_menu.menu import MetaStore


def session_middleware(session: BaseSession, clear_session: bool = True):
    """Handle loading and persisting session."""

    def wrap_middleware(func):
        async def wrapper(**kwargs):
            meta: MetaStore = kwargs["meta"]
            meta.state_manager = session

            meta.log("=> [session middleware] Loading session...")
            await session.load()

            meta.log(f"=> [session middleware] Session data: {session._session}")

            if clear_session and meta.raw_script_input is None:
                meta.log("=> [session middleware] New rofi session has started.")
                # First run of the script (no passed params) => we can start new session
                session.clear()

            try:
                await func(**kwargs)
            finally:
                meta.log("=> [session middleware] Saving session...")
                await session.save()
                meta.log("=> [session middleware] Session saved")

        return wrapper

    return wrap_middleware


class BaseSession(collections.abc.MutableMapping):
    def __init__(self):
        self._session = {}

    @abc.abstractmethod
    async def load(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def save(self) -> None:
        raise NotImplementedError

    def __getitem__(self, item: str) -> typing.Any:
        return self._session[item]

    def __setitem__(self, item: str, value: typing.Any) -> None:
        self._session[item] = value

    def __delitem__(self, item: str) -> None:
        del self._session[item]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self._session)

    def __len__(self) -> int:
        return len(self._session)


class InMemorySession(BaseSession):
    """Short living session."""

    async def load(self) -> None:
        pass

    async def save(self) -> None:
        pass


class FileSession(BaseSession):
    """Long living session that survives between script executions."""

    def __init__(self, cache_folder: str = "~/.cache/rofi-menu"):
        super().__init__()
        self._cache_folder = cache_folder
        self._filename = self._generate_filename()

    def _generate_filename(self) -> pathlib.Path:
        session_id_hash = hashlib.sha256()
        session_id_hash.update(getpass.getuser().encode("utf-8"))
        session_id_hash.update(sys.argv[0].encode("utf-8"))
        filename = session_id_hash.hexdigest() + ".json"

        return pathlib.Path(self._cache_folder).expanduser() / filename

    async def load(self) -> None:
        if self._filename.exists():
            with open(self._filename, "rt") as f:
                self._session = json.load(f)

    async def save(self) -> None:
        if not self._filename.parent.exists():
            self._filename.parent.mkdir(parents=True)
        with open(self._filename, "wt") as f:
            json.dump(self._session, f)
