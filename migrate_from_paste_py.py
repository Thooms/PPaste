"""This script is intended to migrate pastes from the paste-py format
to ours."""

import sys
import os
import re

import ppaste_lib


if __name__ == '__main__':
    folders = sys.argv[1:] # folder we will look into
    output = 'ppaste_new_pastes'

    files = []

    for folder in folders:
        for d, _, f in os.walk(folder):
            files.extend(map(lambda path: os.path.join(d, path), f))

    files = list(filter(lambda f: not (re.search(r'meta$', f)), files))

    for f in files:
        original_id = f.split('/')[-1]
        content = open(f, 'r').read()
        hl = re.search(r'V(\w+)', open('{}.meta'.format(f), 'r').read()).group(0)[1:]
        p = ppaste_lib.Paste(
            'Imported paste (original ID: {})'.format(original_id),
            content,
            hl,
            is_private=True
        )
        p.save()
        print('Successfully imported paste {}, new ID: {}'.format(original_id, p.name))
