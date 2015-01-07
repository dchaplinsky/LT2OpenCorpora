#!/usr/bin/env python
import os.path
import sys
import pydot
from unicodecsv import DictReader
import xml.etree.ElementTree as ET

sys.path.insert(0, ".")

import lt2opencorpora

if __name__ == '__main__':
    # TODO: argparse

    BASEPATH = os.path.dirname(lt2opencorpora.__file__)
    graph = pydot.Dot(graph_type='digraph')
    nodes_by_opencorpora = {}
    nodes_by_LT = {}

    tree = ET.parse(os.path.join(BASEPATH, 'open_corpora_tagset.xml'))
    root = tree.getroot()
    for child in root[0]:
        node = pydot.Node(
            "\n%s" % child.find("name").text, style="filled",
            fillcolor="blanchedalmond")
        node.ru_parent = child.attrib["parent"]
        node.parent = ""
        nodes_by_opencorpora[child.find("name").text] = node

    with open(os.path.join(BASEPATH, "mapping.csv"), "r") as fp:
        r = DictReader(fp)

        for tag in r:
            tag["opencorpora tags"] = (
                tag["opencorpora tags"] or tag["name"])

            name = "%s\n%s" % (tag["name"], tag["opencorpora tags"])

            if tag["opencorpora tags"] in nodes_by_opencorpora:
                node = nodes_by_opencorpora[tag["opencorpora tags"]]
                node.set_name(name)
                node.set_shape("doublecircle")
                node.set("fillcolor", "palegreen")
            else:
                name = "%s\n" % (tag["name"])
                node = pydot.Node(name, style="filled", fillcolor="skyblue")
                node.ru_parent = ""

            node.parent = tag["parent"]

            nodes_by_LT[tag["name"]] = node
            nodes_by_opencorpora[tag["opencorpora tags"]] = node

    for k, node in nodes_by_opencorpora.iteritems():
        graph.add_node(node)

        if node.parent and node.parent != "aux":
            graph.add_edge(pydot.Edge(node, nodes_by_LT[node.parent],
                           color="orange"))

        if node.ru_parent:
            graph.add_edge(
                pydot.Edge(node, nodes_by_opencorpora[node.ru_parent],
                           color="blue"))

    graph.write_png('mapping.png', prog="fdp")
