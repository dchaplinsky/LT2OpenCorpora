#!/usr/bin/env python
import argparse
import logging
import sys
import shutil
import os.path
import requests
from tempfile import NamedTemporaryFile
from collections import Counter
sys.path.insert(0, ".")

from lt2opencorpora.convert import (
    Dictionary, doubleform_signal)


REPEATED_FORMS = Counter()


def log_doubleform(sender, tags_signature):
    REPEATED_FORMS.update({tags_signature: 1})


def download_to_tmp(url):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        cont_type = r.headers.get("content-type")

        suffix = ".txt"
        if cont_type == "application/x-bzip2":
            suffix = ".bz2"
        elif cont_type in ("application/gzip", "application/x-gzip"):
            suffix = ".gzip"

        with NamedTemporaryFile(suffix=suffix, delete=False) as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

        return f.name


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert LT dict to OpenCorpora format.')
    parser.add_argument(
        'in_file', help='input file/url (txt gzipped/bzipped txt)')
    parser.add_argument(
        'out_file', help='XML to save OpenCorpora dictionary to')
    parser.add_argument(
        '--debug',
        help="Output debug information and collect some useful stats",
        action='store_true')
    parser.add_argument(
        '--mapping', help="File with tags, their relationsheeps and meanigns",
        default='')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        doubleform_signal.connect(log_doubleform)

    if args.in_file.startswith(("http://", "https://")):
        args.in_file = download_to_tmp(args.in_file)

    if not os.path.exists(args.in_file):
        exit("In file doesn't exists or cannot be downloaded")

    d = Dictionary(args.in_file, mapping=args.mapping)
    d.export_to_xml(args.out_file)

    if args.debug:
        logging.debug("=" * 50)
        for term, cnt in REPEATED_FORMS.most_common():
            logging.debug(u"%s: %s" % (term, cnt))
