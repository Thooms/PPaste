import os
import random
import string
import json
import logging

from flask import (
    Flask,
    abort,
    make_response,
    redirect,
    render_template,
    request,
    url_for
)
from pygments.lexers import get_all_lexers, get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments import highlight


app = Flask(__name__)

# Logging configuration

log_handler = logging.StreamHandler()
log_formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
log_handler.setFormatter(log_formatter)

LOGGER = logging.getLogger()
LOGGER.addHandler(log_handler)
LOGGER.setLevel(logging.INFO)

# Pastes management configuration

ALPHABET = list(string.ascii_uppercase) + list(string.digits)
PASTE_NAME_LEN = 6
PASTE_LOCATION = os.path.join(os.getcwd(), 'pastes')

# Lexers configuration

LEXERS = sorted(get_all_lexers(), key=lambda l: l[0].lower())


def rand_name():
    '''Returns a random paste name'''
    return ''.join(random.choice(ALPHABET) for _ in range(PASTE_NAME_LEN))


class PPasteException(Exception):
    '''Custom exception'''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def check_pastes_directory(f):
    '''
    Decorator that raises an exception if the pastes directory
    doesn't exists
    '''
    def wrapper(*args, **kwargs):
        if not os.path.isdir(PASTE_LOCATION):
            raise PPasteException(
                'Pastes directory ({}) does not exist'.format(PASTE_LOCATION))
        return f(*args, **kwargs)

    return wrapper


@check_pastes_directory
def register_paste(paste_data):
    '''Saves a paste into the filesystem. Raise an error if not possible.'''

    paste_path = os.path.join(PASTE_LOCATION, paste_data['name'])

    if os.path.exists(paste_path):
        raise PPasteException(
            'Paste file ({}) already exists'.format(paste_path))

    try:
        json.dump(paste_data, open(paste_path, 'w'))
    except OSError as e:
        raise PPasteException('Cannot register paste - {}'.format(e))


@check_pastes_directory
def fetch_paste(name):
    '''Fetches a paste by name in the filesystem.'''

    paste_path = os.path.join(PASTE_LOCATION, name)

    if not os.path.exists(paste_path):
        raise PPasteException(
            'Paste file ({}) does not exists'.format(paste_path))

    try:
        return json.load(open(paste_path, 'r'))
    except OSError as e:
        raise PPasteException('Cannot register paste - {}'.format(e))


@check_pastes_directory
def fetch_pastes_list():
    '''Fetch the list of pastes.'''

    return (
        fetch_paste(f)
        for f in os.listdir(PASTE_LOCATION)
    )


def highlight_paste(paste):
    '''Use pygments to syntax highlight a paste, returns by the way the CSS'''
    lexer = get_lexer_by_name(paste['hl_alias'])
    formatter = HtmlFormatter(linenos=True, cssclass='source')
    return (
        highlight(paste['content'], lexer, formatter),
        formatter.get_style_defs('.source')
    )


@app.route('/')
def home():
    return render_template('home.html', lexers=LEXERS)


@app.route('/submit', methods=['POST'])
def submit():
    data = {
        'title': request.form.get('title'),
        'content': request.form.get('pastecontent'),
        'hl_alias': request.form.get('hl'),
        'name': rand_name()
    }

    try:
        register_paste(data)
        return redirect(url_for('view_paste', paste_name=data['name']))
    except PPasteException as e:
        LOGGER.error(e)
        abort(500)


@app.route('/paste/<string:paste_name>', methods=['GET'])
def view_paste(paste_name=''):
    if not paste_name:
        redirect(url_for('home'))

    try:
        paste = fetch_paste(paste_name)
        highlighted_content, css = highlight_paste(paste)
        return render_template(
            'paste.html',
            paste=paste,
            content=highlighted_content,
            css=css,
            raw_url=url_for('view_paste_raw', paste_name=paste_name)
        )
    except PPasteException as e:
        LOGGER.error(e)
        abort(500)


@app.route('/paste/<string:paste_name>/raw', methods=['GET'])
def view_paste_raw(paste_name=''):
    if not paste_name:
        redirect(url_for('home'))

    try:
        paste = fetch_paste(paste_name)
        resp = make_response(paste['content'], 200)
        resp.headers['Content-Type'] = 'text/plain'
        return resp
    except PPasteException as e:
        LOGGER.error(e)
        abort(500)


@app.route('/pastes', methods=['GET'])
def list_pastes():
    try:
        pastes = fetch_pastes_list()
        return render_template('pastes.html', pastes=pastes)
    except PPasteException as e:
        LOGGER.error(e)
        abort(500)

if __name__ == '__main__':
    app.run()
