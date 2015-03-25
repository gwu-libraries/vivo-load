from __future__ import division
from SPARQLWrapper import SPARQLWrapper
import socket
import codecs
import os
import time
from namespace import ns_manager
from rdflib import Graph
import math


def serialize(graph, filepath, prefix, suffix=None, split_size=None):
    if split_size:
        split_num = int(math.ceil(len(graph) / split_size))
        print "Splitting %s triples into %s parts." % (len(graph), split_num)
        split_count = 0
        filenames = []
        for graph_part in graph_split_generator(graph, split_size):
            split_count += 1
            filenames.append(_serialize(graph_part, filepath, prefix, split_count))
        return filenames
    else:
        return _serialize(graph, filepath, prefix, suffix)


def _serialize(graph, filepath, prefix, suffix=None):
    filename = "%s-%s%s.ttl" % (prefix, time.strftime("%Y%m%d%H%M%S"), "-" + str(suffix) if suffix else "")
    print "Serializing %s triples to %s" % (len(graph), filename)
    with codecs.open(os.path.join(filepath, filename), "w") as out:
        graph.serialize(format="turtle", destination=out)
    return filename


def load_previous_graph(graph_dir, prefix):
    #Find the most recent graph with the prefix
    filenames = [f for f in os.listdir(graph_dir) if f.startswith(prefix + "-")]
    g = Graph(namespace_manager=ns_manager)
    if filenames:
        filenames.sort(reverse=True)
        print "Loading existing graph %s for %s in %s" % (filenames[0], prefix, graph_dir)
        g.parse(os.path.join(graph_dir, filenames[0]), format="turtle")
    else:
        print "No existing graphs for %s in %s" % (prefix, graph_dir)
    return g


def sparql_load(g, htdocs_dir, username, password, split_size=None):
    filenames = serialize(g, htdocs_dir, "load", split_size=split_size)
    ip = socket.gethostbyname(socket.gethostname())
    for filename in filenames:
        print "Loading %s" % filename
        sparql_update("""
            LOAD <http://%s/%s> into graph <http://vitro.mannlib.cornell.edu/default/vitro-kb-2>
        """ % (ip, filename), username, password)


def sparql_delete(g, username, password, split_size=None):
    if split_size:
        split_num = int(math.ceil(len(g) / split_size))
        print "Splitting %s triples into %s parts for deleting." % (len(g), split_num)
        for graph_part in graph_split_generator(g, split_size):
            print "Deleting %s triples." % len(graph_part)
            _sparql_delete(graph_part, username, password)
    else:
        print "Deleting %s triples." % len(g)
        _sparql_delete(g, username, password)


def _sparql_delete(g, username, password):
    #Need to construct query
    ns_lines = []
    triple_lines = []
    for line in g.serialize(format="turtle").splitlines():
        if line.startswith("@prefix"):
            #Change from @prefix to PREFIX
            ns_lines.append("PREFIX" + line[7:-2])
        else:
            triple_lines.append(line)
    query = "\n".join(ns_lines)
    query += "\nDELETE DATA { GRAPH <http://vitro.mannlib.cornell.edu/default/vitro-kb-2> {\n"
    query += "\n".join(triple_lines)
    query += "\n}}"
    sparql_update(query, username, password)


def sparql_update(query, username, password):
    sparql = SPARQLWrapper("http://tomcat:8080/vivo/api/sparqlUpdate")
    sparql.addParameter("email", username)
    sparql.addParameter("password", password)
    sparql.setQuery(query)
    sparql.setMethod("POST")
    sparql.query()


def graph_split_generator(graph, split_size):
    split_num = int(math.ceil(len(graph) / split_size))
    split_count = 0
    tr_count = 0
    graph_part = Graph(namespace_manager=ns_manager)
    for tr in graph:
        graph_part.add(tr)
        tr_count += 1
        if tr_count == split_size:
            split_count += 1
            print "%s of %s:" % (split_count, split_num),
            yield graph_part
            tr_count = 0
            graph_part = Graph(namespace_manager=ns_manager)
    if len(graph_part) > 0:
        split_count += 1
        print "%s of %s:" % (split_count, split_num),
        yield graph_part
