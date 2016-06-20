from flask import Flask, render_template, request, redirect, url_for, abort, make_response
import os
import random
import string
from pygments.lexers import get_all_lexers, get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments import highlight
import json
import logging

app = Flask(__name__)

# Logging

log_handler = logging.StreamHandler()
log_formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
log_handler.setFormatter(log_formatter)

LOGGER = logging.getLogger()
LOGGER.addHandler(log_handler)
LOGGER.setLevel(logging.INFO)

# Custom exception

class PPasteException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# Pastes management

ALPHABET = list(string.ascii_uppercase) + list(map(str, range(1, 10)))
PASTE_NAME_LEN = 6
PASTE_LOCATION = os.path.join(os.getcwd(), 'pastes')

def rand_name():
    return ''.join(random.choice(ALPHABET) for _ in range(PASTE_NAME_LEN))

def check_pastes_directory():
    if not os.path.isdir(PASTE_LOCATION):
        raise PPasteException('Pastes directory ({}) does not exist'.format(PASTE_LOCATION))

def register_paste(paste_data):
    '''Saves a paste into the filesystem. Raise an error if not possible.'''

    check_pastes_directory()

    paste_path = os.path.join(PASTE_LOCATION, paste_data['name'])

    if os.path.exists(paste_path):
        raise PPasteException('Paste file ({}) already exists'.format(paste_path))

    try:
        json.dump(paste_data, open(paste_path, 'w'))
    except OSError as e:
        raise PPasteException('Cannot register paste - {}'.format(e))

def fetch_paste(name):
    '''Fetches a paste by name in the filesystem.'''

    check_pastes_directory()

    paste_path = os.path.join(PASTE_LOCATION, name)

    if not os.path.exists(paste_path):
        raise PPasteException('Paste file ({}) does not exists'.format(paste_path))

    try:
        return json.load(open(paste_path, 'r'))
    except OSError as e:
        raise PPasteException('Cannot register paste - {}'.format(e))

def fetch_pastes_list():
    '''Fetch the list of pastes.'''

    check_pastes_directory()

    return (
        {'name': f}
        for f in os.listdir(PASTE_LOCATION)
    )

# Syntax highlighting management

LEXERS = sorted(get_all_lexers(), key=lambda l: l[0].lower())

def highlight_paste(paste):
    lexer = get_lexer_by_name(paste['hl_alias'])
    formatter = HtmlFormatter(linenos=True, cssclass='source')
    return highlight(paste['content'], lexer, formatter), formatter.get_style_defs('.source')

# Routing and logic

@app.route("/")
def home():
    return render_template('home.html', lexers=LEXERS)

@app.route('/submit', methods=['POST'])
def submit():
    data = {
        'title': request.form['title'],
        'content': request.form['pastecontent'],
        'hl_alias': request.form['hl'],
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
    except PPasteException:
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

if __name__ == "__main__":
    app.run()
