import argparse
import logging
import re

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
from pygments.formatters.html import HtmlFormatter
from pygments import highlight

import ppaste_lib


app = Flask(__name__)


log_handler = logging.StreamHandler()
log_formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
log_handler.setFormatter(log_formatter)

LOGGER = logging.getLogger()
LOGGER.addHandler(log_handler)
LOGGER.setLevel(logging.INFO)


LEXERS = sorted(get_all_lexers(), key=lambda l: l[0].lower())


def highlight_paste(paste, hl_lines):
    '''Use pygments to syntax highlight a paste, returns by the way the CSS'''
    lexer = get_lexer_by_name(paste.hl_alias)
    formatter = HtmlFormatter(linenos=True, cssclass='source', hl_lines=hl_lines)
    return (
        highlight(paste.content, lexer, formatter),
        formatter.get_style_defs('.source')
    )


def parse_hl(hl):
    """
    Parse the hl arg of the query string into a list of line's number.

    hl is a string representing a list of number or range separated by space.
    A range is two numbers separated by a '-' (Example: '40-43')

    Example: parse_hl('1 2 3 40-43') == [1, 2, 3, 40, 41, 42, 43]
    """

    if hl is None:
        return []

    if not re.match(r"\d+|(\d+-\d+)( \d+|(\d+-\d+))*", hl):
        abort(400)

    lines = []
    for raw_query in hl.split(' '):
        if '-' in raw_query:  # Add the range into the lines list
            i = raw_query.index('-')
            lines.extend(range(int(raw_query[:i]), int(raw_query[i + 1:]) + 1))
        else:
            lines.append(int(raw_query))
    return lines


@app.route('/')
def home():
    return render_template('home.html', lexers=LEXERS)


@app.route('/submit', methods=['POST'])
def submit():
    paste = ppaste_lib.Paste(
        title=request.form.get('title'),
        content=request.form.get('pastecontent'),
        hl_alias=request.form.get('hl'),
        is_private=True if request.form.get('privatepaste') else False
    )
    try:
        paste.save()
        return redirect(url_for('view_paste', paste_name=paste.name))
    except ppaste_lib.PPasteException as e:
        LOGGER.error(e)
        abort(500)


@app.route('/paste/<string:paste_name>', methods=['GET'])
def view_paste(paste_name=''):
    if not paste_name:
        redirect(url_for('home'))

    hl_lines = parse_hl(request.args.get('ln'))
    try:
        paste = ppaste_lib.PasteManager.fetch_paste(paste_name)
        highlighted_content, css = highlight_paste(paste, hl_lines)
        return render_template(
            'paste.html',
            paste=paste,
            content=highlighted_content,
            css=css,
            raw_url=url_for('view_paste_raw', paste_name=paste_name)
        )
    except ppaste_lib.PPasteException as e:
        LOGGER.error(e)
        abort(500)


@app.route('/paste/<string:paste_name>/raw', methods=['GET'])
def view_paste_raw(paste_name=''):
    if not paste_name:
        redirect(url_for('home'))

    try:
        paste = ppaste_lib.PasteManager.fetch_paste(paste_name)
        resp = make_response(paste.content, 200)
        resp.headers['Content-Type'] = 'text/plain'
        return resp
    except ppaste_lib.PPasteException as e:
        LOGGER.error(e)
        abort(500)


@app.route('/pastes', methods=['GET'])
def list_pastes():
    try:
        pastes = ppaste_lib.PasteManager.fetch_public_pastes()
        return render_template('pastes.html', pastes=pastes)
    except ppaste_lib.PPasteException as e:
        LOGGER.error(e)
        abort(500)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='PPaste - The only pastebin you need <3'
    )

    parser.add_argument(
        '--port',
        type=int,
        nargs=1,
        help='The port on which to listen (default: 4242)',
        default=4242
    )

    args = parser.parse_args()
    port = args.port if isinstance(args.port, int) else args.port[0]

    app.run(port=port)
