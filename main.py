from flask import Flask, render_template, request, redirect, url_for, abort, make_response
import os
import random
import string

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

def register_paste(name, content, title):
    '''Saves a paste into the filesystem. Raise an error if not possible.'''

    if not os.path.isdir(PASTE_LOCATION):
        raise PPasteException('Pastes directory ({}) does not exist'.format(PASTE_LOCATION))

    paste_path = os.path.join(PASTE_LOCATION, name)

    if os.path.exists(paste_path):
        raise PPasteException('Paste file ({}) already exists'.format(paste_path))

    try:
        with open(paste_path, 'w') as f:
            f.write(content)
    except OSError(e):
        raise PPasteException('Cannot register paste - {}'.format(e))

def fetch_paste(name):
    '''Fetches a paste by name in the filesystem.'''

    if not os.path.isdir(PASTE_LOCATION):
        raise PPasteException('Pastes directory ({}) does not exist'.format(PASTE_LOCATION))

    paste_path = os.path.join(PASTE_LOCATION, name)

    if not os.path.exists(paste_path):
        raise PPasteException('Paste file ({}) does not exists'.format(paste_path))

    try:
        with open(paste_path, 'r') as f:
            content =  f.read()
        return content
    except OSError(e):
        raise PPasteException('Cannot register paste - {}'.format(e))

# Routing and logic

@app.route("/")
def home():
    return render_template('home.html')

@app.route('/submit', methods=['POST'])
def submit():
    title = request.form['title']
    content = request.form['pastecontent']
    paste_name = rand_name()
    try:
        register_paste(paste_name, content, title)
        return redirect(url_for('view_paste', paste_name=paste_name))
    except PPasteException:
        abort(500)

@app.route('/paste/<paste_name>', methods=['GET'])
def view_paste(paste_name=''):
    if not paste_name:
        redirect(url_for('home'))

    try:
        content = fetch_paste(paste_name)
        resp = make_response(content, 200)
        resp.headers['Content-Type'] = 'text/plain'
        return resp
    except PPasteException:
        abort(404)

if __name__ == "__main__":
    app.run()
