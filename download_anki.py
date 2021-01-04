import json
import os
import re
from collections import namedtuple
from operator import attrgetter

import requests

DOWNLOAD_DIR = os.path.join(os.path.realpath(os.path.dirname(__file__)),
                            'downloads')

deck = namedtuple('deck', (
    'id',
    'title',
    'unknown',
    'unknown_maybe_ratings',
    'modified_at',
    'notes',
    'audio',
    'images',
))


if __name__ == "__main__":
    print("Downloading to {}".format(DOWNLOAD_DIR))

    if os.path.exists(DOWNLOAD_DIR) and os.path.isfile(DOWNLOAD_DIR):
        raise Exception("Download directory {} is a file".format(DOWNLOAD_DIR))
    elif not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    url = "https://ankiweb.net/shared/decks/Foundations%201"

    # Need to store cookies for CSRF challenge
    s = requests.Session()

    r = s.get(url)
    r.raise_for_status()

    m = re.search(r'shared\.files = (.*);$', r.text, flags=re.MULTILINE)
    if m is None:
        raise Exception("Failed to find file list")

    files = json.loads(m.group(1))
    decks = []
    for f in files:
        # (id, title, ?, ratings?, modified_epoch, notes, audio, images)
        decks.append(deck(*f))

    print("Found {} decks".format(len(decks)))

    week = input("What week are you interested in? ")
    week = int(week)

    to_download = []
    for d in decks:
        if "Week {}".format(week) in d.title:
            to_download.append(d)

    print("Downloading the following decks:")
    to_download = sorted(to_download, key=attrgetter('title'))
    for d in to_download:
        print("{}... ".format(d.title), end='')

        # prepare for download
        r = s.get('https://ankiweb.net/shared/info/{}'.format(d.id))
        m = re.search('name="k" value="(.*)"', r.text)
        if m is None:
            raise Exception("Failed to find CSRF token")

        # download
        r = s.post('https://ankiweb.net/shared/downloadDeck/{}'.format(d.id),
                   data={'k': m.group(1)},
                   stream=True)

        with open('{}.apkg'.format(d.title), 'wb') as f:
            for block in r.iter_content(1024):
                f.write(block)

        print("ok")

    print("Done!")
