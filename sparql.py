from SPARQLWrapper import SPARQLWrapper
import socket
import codecs
import os
import time
from namespace import ns_manager
from rdflib import Graph

def serialize(graph, dir, prefix):
    filename = time.strftime(prefix + "-%Y%m%d%H%M%S.ttl")
    print "Serializing to %s" % filename
    with codecs.open(os.path.join(dir, filename), "w") as out:
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


def sparql_load(g, htdocs_dir):
    print "Loading"
    filename = serialize(g, htdocs_dir, "load")
    ip = socket.gethostbyname(socket.gethostname())
    sparql_update("""
        LOAD <http://%s/%s> into graph <http://vitro.mannlib.cornell.edu/default/vitro-kb-2>
    """ % (ip, filename))


def sparql_delete(g):
    print "Deleting"
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
    sparql_update(query)


def sparql_update(query):
    sparql = SPARQLWrapper("http://tomcat:8080/vivo/api/sparqlUpdate")
    sparql.addParameter("email", "vivo_root@gwu.edu")
    sparql.addParameter("password", "password")
    sparql.setQuery(query)
    sparql.setMethod("POST")
    sparql.query()
