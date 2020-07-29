import collections.abc
import hashlib
import json
import os
import pathlib
import sys


class FileSession(collections.abc.MutableMapping):

    def __init__(self, cache_folder: str = "~/.cache/rofi-menu"):
        self._cache_folder = cache_folder
        self._filename = self._generate_filename()
        self._session = {}

    def _generate_filename(self):
        session_id_hash = hashlib.sha256()
        session_id_hash.update(os.getlogin().encode('utf-8'))
        session_id_hash.update(sys.argv[0].encode('utf-8'))
        filename = session_id_hash.hexdigest() + '.json'

        return pathlib.Path(self._cache_folder).expanduser() / filename

    async def load(self):
        if self._filename.exists():
            with open(self._filename, 'rt') as f:
                self._session = json.load(f)

    async def save(self):
        if not self._filename.parent.exists():
            self._filename.parent.mkdir(parents=True)
        with open(self._filename, 'wt') as f:
            json.dump(self._session, f)

    def __getitem__(self, item):
        return self._session[item]

    def __setitem__(self, item, value):
        self._session[item] = value

    def __delitem__(self, item):
        del self._session[item]

    def __iter__(self):
        return iter(self._session)

    def __len__(self):
        return len(self._session)
