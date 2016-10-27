from rdflib.namespace import Namespace, NamespaceManager
from rdflib import Graph

#Our data namespace
D = Namespace('https://expert.gwu.edu/individual/')
#The VIVO namespace
VIVO = Namespace('http://vivoweb.org/ontology/core#')
#The VCARD namespace
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')
#The OBO namespace
OBO = Namespace('http://purl.obolibrary.org/obo/')
#The BIBO namespace
BIBO = Namespace('http://purl.org/ontology/bibo/')
#The FOAF namespace
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
#The GW Local namespace
#LOCAL = Namespace('https://expert.gwu.edu/ontology/local#')
LOCAL = Namespace('http://vivo.gwu.edu/ontology/local#')
#The SKOS namespace
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
#The Linkvoj namespace
LINKVOJ = Namespace('http://www.lingvoj.org/ontology#')

ns_manager = NamespaceManager(Graph())
ns_manager.bind('d', D)
ns_manager.bind('vivo', VIVO)
ns_manager.bind('vcard', VCARD)
ns_manager.bind('obo', OBO)
ns_manager.bind('bibo', BIBO)
ns_manager.bind("foaf", FOAF)
ns_manager.bind("local", LOCAL)
ns_manager.bind("skos", SKOS)
ns_manager.bind("linkvoj", LINKVOJ)
