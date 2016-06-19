from flask import Flask, render_template, request, redirect, url_for, abort, make_response
import os
import random
import string
import pygments.lexers
import json

app = Flask(__name__)

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
    except OSError(e):
        raise PPasteException('Cannot register paste - {}'.format(e))

def fetch_paste(name):
    '''Fetches a paste by name in the filesystem.'''

    check_pastes_directory()

    paste_path = os.path.join(PASTE_LOCATION, name)

    if not os.path.exists(paste_path):
        raise PPasteException('Paste file ({}) does not exists'.format(paste_path))

    try:
        return json.load(open(paste_path, 'r'))
    except OSError(e):
        raise PPasteException('Cannot register paste - {}'.format(e))

# Syntax highlighting management

LEXERS = sorted(pygments.lexers.get_all_lexers(), key=lambda l: l[0].lower())

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
    except PPasteException:
        abort(500)

@app.route('/paste/<paste_name>', methods=['GET'])
def view_paste(paste_name=''):
    if not paste_name:
        redirect(url_for('home'))

    try:
        paste = fetch_paste(paste_name)
        resp = make_response(paste['content'], 200)
        resp.headers['Content-Type'] = 'text/plain'
        return resp
    except PPasteException:
        abort(404)

if __name__ == "__main__":
    app.run()
