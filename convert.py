import sys
import gzip
import codecs
import logging
import argparse

from itertools import ifilter
import xml.etree.cElementTree as ET

from unicodecsv import DictReader
from liquer import Q, register
from blinker import signal


sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
doubleform_signal = signal('doubleform-found')

is_iterable = lambda x: isinstance(x, (dict, list, tuple, set, frozenset))

register('has', lambda x, y: y in x)
register('ne', lambda x, y: x != y)
register('has_all',
         lambda x, y: all(map(lambda y_val: y_val in x,
                              y if is_iterable(y) else (y,))))

register('has_none',
         lambda x, y: all(map(lambda y_val: y_val not in x,
                              y if is_iterable(y) else (y,))))

register('has_any',
         lambda x, y: any(map(lambda y_val: y_val in x,
                              y if is_iterable(y) else (y,))))
register('has_not', lambda x, y: y not in x)


def open_any(filename):
    # No BZIP support because of problems with utf-8 in readlines
    # implementation
    if filename.endswith(".gz"):
        return gzip.open

    return open


class TagSet(object):
    def __init__(self, fname):
        self.all = []
        self.full = {}
        self.lt2opencorpora = {}

        with open(fname, "r") as fp:
            r = DictReader(fp)

            for tag in r:
                tag["lemma form"] = filter(None, map(unicode.strip,
                                           tag["lemma form"].split(",")))

                tag["opencorpora tags"] = (
                    tag["opencorpora tags"] or tag["name"])

                self.lt2opencorpora[tag["name"]] = tag["opencorpora tags"]

                if not hasattr(self, tag["parent"]):
                    setattr(self, tag["parent"], [])

                attr = getattr(self, tag["parent"])
                attr.append(tag["name"])

                if tag["parent"] != "aux":
                    self.all.append(tag["name"])

                self.full[tag["name"]] = tag

    def export_to_xml(self):
        grammemes = ET.Element("grammemes")
        for tag in self.full.values():
            grammeme = ET.SubElement(grammemes, "grammeme")
            if tag["parent"] != "aux":
                grammeme.attrib["parent"] = tag["parent"]
            name = ET.SubElement(grammeme, "name")
            name.text = tag["opencorpora tags"]

            alias = ET.SubElement(grammeme, "alias")
            alias.text = tag["name"]

            description = ET.SubElement(grammeme, "description")
            description.text = tag["description"]

        return grammemes


class WordForm(object):
    def __init__(self, raw, tag_set):
        raw = unicode(raw.decode('utf-8'))
        self.form, self.lemma, self.tags = raw.split(" ", 3)

        self.tags = map(unicode.strip, self.tags.split(u":"))
        self.used = False
        self.tags_signature = ":".join(sorted(self.tags))

        pos_tags = filter(lambda x: x in tag_set.post, self.tags)
        self.pos = ""
        self.lemma_signature = ""
        if len(pos_tags) == 0:
            logging.debug(
                u"word form %s has no POS tag assigned" % self.form)
        elif len(pos_tags) == 1:
            self.pos = pos_tags[0]
            self.lemma_signature = u"%s:%s" % (self.lemma, self.pos)
        else:
            logging.debug(
                u"word form %s has more than one POS tag assigned: %s"
                % (self.form, pos_tags))

    def __str__(self):
        return u"<%s: %s>: %s" % (self.lemma, self.form, self.tags_signature)


class Lemma(object):
    def __init__(self, word, pos, tag_set):
        self.word = word
        self.pos = pos
        self.tag_set = tag_set
        self.forms = {}

    def __str__(self):
        return u"<%s: %s>" % (self.word, self.pos)

    def add_form(self, form):
        if (form.tags_signature in self.forms and
                form.form != self.forms[form.tags_signature][0].form):
            doubleform_signal.send(self, tags_signature=form.tags_signature)

            self.forms[form.tags_signature].append(form)

            logging.debug(
                u"lemma %s got %s forms with same tagset %s: %s" %
                (self, len(self.forms[form.tags_signature]),
                 form.tags_signature,
                 u", ".join(map(lambda x: x.form,
                                self.forms[form.tags_signature]))))
        else:
            self.forms[form.tags_signature] = [form]

    def _add_tags_to_element(self, el, tags):
        for tag in tags:
            ET.SubElement(el, "g", v=self.tag_set.lt2opencorpora[tag])

    def export_to_xml(self, i, rev=1):
        lemma = ET.Element("lemma", id=str(i), rev=str(rev))
        lemma_tags = self.tag_set.full[self.pos]["lemma form"]

        for forms in self.forms.values():
            for form in forms:
                el = ET.Element("f", t=form.form.lower())
                if (form.form == self.word and
                        Q(tags__has_all=lemma_tags)(form)):
                    l_form = ET.SubElement(lemma, "l", t=form.form.lower())
                    self._add_tags_to_element(l_form, form.tags)
                    lemma.insert(0, el)
                else:
                    lemma.append(el)

                self._add_tags_to_element(el, form.tags)

        return lemma


class Dictionary(object):
    def __init__(self, fname, mapping):
        self.tag_set = TagSet(mapping)

        with open_any(fname)(fname, "r") as fp:
            dct = map(lambda r: WordForm(r, self.tag_set), fp.readlines())

        self.lemmas = {}

        for form in ifilter(Q(lemma_signature__ne=""), dct):
            lemma = self.lemmas.setdefault(form.lemma_signature,
                                           Lemma(form.lemma, form.pos,
                                                 self.tag_set))

            lemma.add_form(form)

    def export_to_xml(self, fname):
        root = ET.Element("dictionary", version="0.1", revision="1")
        tree = ET.ElementTree(root)
        root.append(self.tag_set.export_to_xml())
        lemmata = ET.SubElement(root, "lemmata")

        for i, lemma in enumerate(self.lemmas.values()):
            lemmata.append(lemma.export_to_xml(i + 1))

        tree.write(fname, encoding="utf-8")


if __name__ == '__main__':
    from collections import Counter
    REPEATED_FORMS = Counter()

    def log_doubleform(sender, tags_signature):
        global REPEATED_FORMS
        REPEATED_FORMS.update({tags_signature: 1})

    parser = argparse.ArgumentParser(
        description='Convert LT dict to OpenCorpora format.')
    parser.add_argument(
        'in_file', help='input file (txt or gzipped txt)')
    parser.add_argument(
        'out_file', help='XML to save OpenCorpora dictionary to')
    parser.add_argument(
        '--debug',
        help="Output debug information and collect some useful stats",
        action='store_true')
    parser.add_argument(
        '--mapping', help="File with tags, their relationsheeps and meanigns",
        default='mapping.csv')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        doubleform_signal.connect(log_doubleform)

    d = Dictionary(args.in_file, mapping=args.mapping)
    d.export_to_xml(args.out_file)

    if args.debug:
        logging.debug("=" * 50)
        for term, cnt in REPEATED_FORMS.most_common():
            logging.debug(u"%s: %s" % (term, cnt))
