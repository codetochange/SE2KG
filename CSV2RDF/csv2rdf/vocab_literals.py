#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
'''
Create a flat RDF vocabulary from literal RDF values
'''
import argparse

import logging

import sys
from rdflib import *
from rdflib.namespace import SKOS
from slugify import slugify

log = logging.getLogger(__name__)


def create_unused_uri(uri, used_uris):
    """
    Create a new URI by appending a number to the end
    """
    orig_uri = uri
    i = 1

    while uri in used_uris:
        uri = "{uri}_{index}".format(uri=uri, index=i)
        i += 1

    log.warning('Changing duplicate URI: %s --> %s' % (orig_uri, uri))

    return URIRef(uri)


def vocabularize(graph, namespace, property, target_property, target_class, literal_lang='fi'):
    """
    Transform literal values into a RDF flat RDF vocabulary. Splits values by '/'.

    :return:
    """

    output = Graph()
    vocab = Graph()
    used_uris = {}

    log.debug('Starting vocabulary creation')

    for (sub, obj) in graph.subject_objects(property):
        for value in [occ.strip().lower() for occ in str(obj).split('/')]:

            slug = slugify(value)
            if not slug:
                log.warning('Skipping item with empty slugified value: %s' % value)
                continue

            new_obj = namespace[slug]
            if new_obj in used_uris and used_uris.get(new_obj) != value:
                new_obj = create_unused_uri(new_obj, used_uris)

            if new_obj not in used_uris:
                used_uris.update({new_obj: value})
                log.debug('Found new vocabulary item: %s' % value)

            output.add((sub, target_property, new_obj))
            vocab.add((new_obj, RDF.type, target_class))
            vocab.add((new_obj, SKOS.prefLabel, Literal(value, lang=literal_lang)))

    log.debug('Vocabulary creation finished')
    return output, vocab


def main(args):
    """
    Main function for running via the command line.

    `args` is the list of command line arguments.
    """
    argparser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')

    argparser.add_argument("input", help="Input RDF data file")
    argparser.add_argument("output", help="Output RDF data file")
    argparser.add_argument("output_vocab", help="Output RDF vocabulary file")
    argparser.add_argument("property", metavar="SOURCE_PROPERTY", help="Property used in input file")
    argparser.add_argument("tproperty", metavar="TARGET_PROPERTY", help="Target property for output file")
    argparser.add_argument("tclass", metavar="TARGET_CLASS", help="Target class for target property values")
    argparser.add_argument("tnamespace", metavar="TARGET_NAMESPACE", help="Namespace for target values")
    argparser.add_argument("--remove", dest='remove', action='store_true', default=False,
                           help="Remove original property triples")
    argparser.add_argument("--format", default='turtle', type=str, help="Format of RDF files [default: turtle]")
    argparser.add_argument("--mapping", metavar='FILE', type=str,
                           help="File containing value mappings (Not implemented)")

    args = argparser.parse_args()

    ns_target = Namespace(args.tnamespace)
    input_graph = Graph().parse(args.input, format=args.format)

    log.debug('Parsed input file')

    annotations, vocabulary = vocabularize(input_graph, Namespace(ns_target), URIRef(args.property),
                                           URIRef(args.tproperty), URIRef(args.tclass))

    annotations.serialize(format=args.format, destination=args.output)
    vocabulary.serialize(format=args.format, destination=args.output_vocab)

    log.debug('Serialized output files')


if __name__ == '__main__':
    logging.basicConfig(filename='vocab.log', filemode='a', level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    main(sys.argv)
