from fis_entity import Award, ProfessionalMembership, Reviewership, Presentation
from fis_load import BasicLoader
from utility import xml_result_generator, ns_manager, D, to_hash_identifier, RDF, LINKVOJ, RDFS
from prefixes import PREFIX_LANGUAGE
from fis_entity import Person
import orcid2vivo_loader
import os
from rdflib import Graph, Literal


def load_awards(data_dir, non_faculty_gwids, limit=None):
    print "Loading mygw awards."

    l = BasicLoader("mygw_award.xml", data_dir, Award, non_faculty_gwids, limit=limit)
    return l.load()


def load_professional_memberships(data_dir, non_faculty_gwids, limit=None):
    print "Loading mygw professional memberships."

    l = BasicLoader("mygw_membership.xml", data_dir, ProfessionalMembership, non_faculty_gwids, limit=limit)
    return l.load()


def load_reviewerships(data_dir, non_faculty_gwids, limit=None):
    print "Loading mygw reviewerships."

    l = BasicLoader("mygw_editorial.xml", data_dir, Reviewership, non_faculty_gwids, limit=limit)
    return l.load()


def load_presentations(data_dir, non_faculty_gwids, limit=None):
    print "Loading mygw presentations."

    l = BasicLoader("mygw_presentation.xml", data_dir, Presentation, non_faculty_gwids, limit=limit)
    return l.load()


def load_users(data_dir, store_dir, non_faculty_gwids, limit=None):
    print "Loading mygw users."

    #Setup orcid2vivo store
    store = orcid2vivo_loader.Store(store_dir)
    #Set everyone to inactive
    store.delete_all()

    g = Graph(namespace_manager=ns_manager)

    for result_num, result in enumerate(xml_result_generator(os.path.join(data_dir, "mygw_users.xml"))):
        if result["gw_id"] in non_faculty_gwids:
            person = Person(result["gw_id"])
            #If there is an orcid id, add to store.
            if result["orcid_id"]:
                store.add(result["orcid_id"], person_uri=person.uri)

            #Add languages spoken
            if result["languages"]:
                languages = result["languages"].split(",")
                for language in languages:
                    language_uri = D[to_hash_identifier(PREFIX_LANGUAGE, (language,))]
                    g.add((language_uri, RDF.type, LINKVOJ.Lingvo))
                    g.add((language_uri, RDFS.label, Literal(language)))
                    g.add((person.uri, LINKVOJ.expertUnderstanding, language_uri))
            if limit and result_num >= limit-1:
                break

    return g