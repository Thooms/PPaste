import json
import os
import random
import string
import time


class PPasteException(Exception):
    '''Custom exception'''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class PasteManager:
    NAME_LEN = 6
    ALPHABET = list(string.ascii_uppercase) + list(string.digits)
    PASTE_LOCATION = os.path.join(os.getcwd(), 'pastes')

    def check_pastes_directory(f):
        '''
        Decorator that raises an exception if the pastes directory
        doesn't exists
        '''
        def wrapper(*args, **kwargs):
            if not os.path.isdir(PasteManager.PASTE_LOCATION):
                raise PPasteException(
                    'Pastes directory ({}) does not exist'.format(
                        PasteManager.PASTE_LOCATION))
            return f(*args, **kwargs)

        return wrapper

    def get_rand_paste_name():
        return ''.join(
            random.choice(PasteManager.ALPHABET)
            for _ in range(PasteManager.NAME_LEN)
        )

    def craft_paste_path(paste_name):
        return os.path.join(PasteManager.PASTE_LOCATION, paste_name)

    @check_pastes_directory
    def save_paste(paste):
        path = PasteManager.craft_paste_path(paste.name)

        if os.path.exists(path):
            raise PPasteException('Paste file {} already exists'.format(path))

        try:
            with open(path, 'w') as f:
                json.dump(paste.get_dict(), f)
        except OSError as e:
            raise PPasteException('Cannot write file {} - {}'.format(
                path,
                e
            ))

    @check_pastes_directory
    def fetch_paste(name):
        path = PasteManager.craft_paste_path(name)

        if not os.path.exists(path):
            raise PPasteException(
                'Paste file {} does not exists'.format(path))

        try:
            with open(path, 'r') as f:
                d = json.load(f)

                return Paste(
                    title=d['title'],
                    content=d['content'],
                    hl_alias=d['hl_alias'],
                    is_private=d['is_private'],
                    date=d['date'],
                    name=name,
                )
        except OSError as e:
            raise PPasteException('Cannot load file {} - {}'.format(
                path,
                e
            ))

    @check_pastes_directory
    def fetch_public_pastes():
        return sorted(
            filter(
                lambda p: not p.is_private,
                (PasteManager.fetch_paste(name)
                 for name
                 in os.listdir(PasteManager.PASTE_LOCATION))
            ),
            key=lambda p: -p.date
        )


class Paste:

    def __init__(self, title='', content='', hl_alias='',
                 is_private=False, name=None, date=None):
        self.title = title or ''
        self.content = content or ''
        self.hl_alias = hl_alias or 'Text only'
        self.is_private = is_private
        self.name = PasteManager.get_rand_paste_name() \
            if name is None else name
        self.date = int(time.time()) \
            if date is None else date

    def get_dict(self):
        return {
            'title': self.title,
            'content': self.content,
            'hl_alias': self.hl_alias,
            'is_private': self.is_private,
            'name': self.name,
            'date': self.date
        }

    @PasteManager.check_pastes_directory
    def save(self):
        PasteManager.save_paste(self)
