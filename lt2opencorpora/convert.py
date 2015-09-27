from __future__ import unicode_literals
import sys
import gzip
import os.path
import bz2file as bz2
import codecs
import logging

import xml.etree.cElementTree as ET

from unicodecsv import DictReader

# To add stats collection in inobstrusive way (that can be simply disabled)
from blinker import signal


sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
doubleform_signal = signal('doubleform-found')


def open_any(filename):
    """
    Helper to open also compressed files
    """
    if filename.endswith(".gz"):
        return gzip.open

    if filename.endswith(".bz2"):
        return bz2.BZ2File

    return open


class TagSet(object):
    """
    Class that represents LanguageTool tagset
    Can export it to OpenCorpora XML
    Provides some shorthands to simplify checks/conversions
    """
    def __init__(self, fname):
        self.all = []
        self.full = {}
        self.lt2opencorpora = {}

        with open(fname, "r") as fp:
            r = DictReader(fp)

            for tag in r:
                # lemma form column represents set of tags that wordform should
                # have to be threatened as lemma.
                tag["lemma form"] = filter(None, map(unicode.strip,
                                           tag["lemma form"].split(",")))

                tag["divide by"] = filter(
                    None, map(unicode.strip, tag["divide by"].split(",")))

                # opencopropra tags column maps LT tags to OpenCorpora tags
                # when possible
                tag["opencorpora tags"] = (
                    tag["opencorpora tags"] or tag["name"])

                # Helper mapping
                self.lt2opencorpora[tag["name"]] = tag["opencorpora tags"]

                # Parent column links tag to it's group tag.
                # For example parent tag for noun is POST tag
                # Parent for m (masculine) is gndr (gender group)
                if not hasattr(self, tag["parent"]):
                    setattr(self, tag["parent"], [])

                attr = getattr(self, tag["parent"])
                attr.append(tag["name"])

                # aux is our auxiliary tag to connect our group tags
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
    """
    Class that represents single word form.
    Initialized out of form and tags strings from LT dictionary.
    """
    def __init__(self, form, tags, tag_set):
        self.form, self.tags = form, tags

        self.tags = map(unicode.strip, self.tags.split(":"))
        self.used = False

        # tags signature is string made out of sorted list of wordform tags
        # This is a workout for rare cases when some wordform has
        # noun:m:v_naz and another has noun:v_naz:m
        self.tags_signature = ":".join(sorted(self.tags))

        # Here we are trying to determine exact part of speech for this
        # wordform
        pos_tags = filter(lambda x: x in tag_set.post, self.tags)
        self.pos = ""

        # And report cases when it's missing or wordform has more than two
        # pos tags assigned
        if len(pos_tags) == 0:
            logging.debug(
                "word form %s has no POS tag assigned" % self.form)
        elif len(pos_tags) == 1:
            self.pos = pos_tags[0]

            if pos_tags[0] != self.tags[0]:
                logging.debug(
                    "word form %s has strange POS tag %s instead of %s"
                    % (self.form, pos_tags[0], self.tags[0]))

            # Not yet clear if it'll be used or not
            # lemma_form_tags = [self.pos] + tag_set.full[self.pos]["lemma form"]

            # for splitter in tag_set.full[self.pos]["divide by"]:
            #     if splitter in self.tags:
            #         lemma_form_tags += [splitter]
            #         break

            # self.lemma_signature = (self.lemma,
            #                         tuple(lemma_form_tags))
        else:
            logging.debug(
                "word form %s has more than one POS tag assigned: %s"
                % (self.form, pos_tags))

    def __str__(self):
        return "<%s: %s>" % (self.form, self.tags_signature)

    def __unicode__(self):
        return self.__str__()


class Lemma(object):
    def __init__(self, word, lemma_form_tags, tag_set):
        self.word = word

        self.lemma_form = WordForm(word, lemma_form_tags, tag_set)
        self.pos = self.lemma_form.pos
        self.tag_set = tag_set
        self.forms = {}
        self.common_tags = None

        self.add_form(self.lemma_form)

    def __str__(self):
        return "%s" % self.lemma_form

    @property
    def lemma_signature(self):
        return (self.word,) + tuple(self.common_tags)

    def add_form(self, form):
        if self.common_tags is not None:
            self.common_tags = self.common_tags.intersection(form.tags)
        else:
            self.common_tags = set(form.tags)

        if (form.tags_signature in self.forms and
                form.form != self.forms[form.tags_signature][0].form):
            doubleform_signal.send(self, tags_signature=form.tags_signature)

            self.forms[form.tags_signature].append(form)

            logging.debug(
                "lemma %s got %s forms with same tagset %s: %s" %
                (self, len(self.forms[form.tags_signature]),
                 form.tags_signature,
                 ", ".join(map(lambda x: x.form,
                               self.forms[form.tags_signature]))))
        else:
            self.forms[form.tags_signature] = [form]

    def _add_tags_to_element(self, el, tags):
        if self.pos in tags:
            ET.SubElement(el, "g", v=self.tag_set.lt2opencorpora[self.pos])
            tags = set(tags) - set([self.pos])

        for tag in tags:
            # For rare cases when tag in the dict is not from tagset
            if tag in self.tag_set.lt2opencorpora:
                ET.SubElement(el, "g", v=self.tag_set.lt2opencorpora[tag])

    def export_to_xml(self, i, rev=1):
        lemma = ET.Element("lemma", id=str(i), rev=str(rev))
        common_tags = list(self.common_tags or set())

        if not common_tags:
            logging.debug(
                "Lemma %s has no tags at all" % self.lemma_form)

            return None

        l_form = ET.SubElement(lemma, "l", t=self.lemma_form.form.lower())
        self._add_tags_to_element(l_form, common_tags)

        for forms in self.forms.values():
            for form in forms:
                el = ET.Element("f", t=form.form.lower())
                lemma.append(el)

                self._add_tags_to_element(el,
                                          set(form.tags) - set(common_tags))

        return lemma


class Dictionary(object):
    def __init__(self, fname, mapping):
        if not mapping:
            mapping = os.path.join(os.path.dirname(__file__), "mapping.csv")

        self.tag_set = TagSet(mapping)
        self.lemmas = {}

        with open_any(fname)(fname, "r") as fp:
            current_lemma = None

            for i, line in enumerate(fp):
                line = unicode(line.decode('utf-8'))
                # Here we've found a new lemma, let's add old one to the list
                # and continue
                if not line.startswith("  "):
                    self.add_lemma(current_lemma)

                    current_lemma = Lemma(
                        *line.strip().split(" ", 1),
                        tag_set=self.tag_set)
                else:
                    # It's a form of current lemma
                    current_lemma.add_form(WordForm(
                        *line.strip().split(" ", 1),
                        tag_set=self.tag_set
                    ))

            self.add_lemma(current_lemma)

    def add_lemma(self, lemma):
        if lemma is not None:
            self.lemmas[lemma.lemma_signature] = lemma

    def export_to_xml(self, fname):
        root = ET.Element("dictionary", version="0.2", revision="1")
        tree = ET.ElementTree(root)
        root.append(self.tag_set.export_to_xml())
        lemmata = ET.SubElement(root, "lemmata")

        for i, lemma in enumerate(self.lemmas.values()):
            lemma_xml = lemma.export_to_xml(i + 1)
            if lemma_xml is not None:
                lemmata.append(lemma_xml)

        tree.write(fname, encoding="utf-8")
