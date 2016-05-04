from fis_load import BasicLoader

import orcid2vivo_loader
from orcid2vivo_app.utility import clean_orcid, is_valid_orcid
import os
from loader.fis_entity import Award, ProfessionalMembership, Reviewership, Presentation
from loader.fis_entity import Person
from rdflib import Literal, RDF, RDFS, XSD
from utility import xml_result_generator, add_language, warning_log, join_if_not_empty, to_hash_identifier
from namespace import *
from prefixes import PREFIX_RESEARCH_AREA, PREFIX_MULTIMEDIA
import logging

log = logging.getLogger(__name__)


def load_awards(data_dir, non_faculty_gwids, netid_lookup, limit=None):
    print "Loading mygw awards."

    l = BasicLoader("mygw_award.xml", data_dir, Award, non_faculty_gwids,
                    netid_lookup, limit=limit)
    return l.load()


def load_professional_memberships(data_dir, non_faculty_gwids, netid_lookup, limit=None):
    print "Loading mygw professional memberships."

    l = BasicLoader("mygw_membership.xml", data_dir, ProfessionalMembership, non_faculty_gwids,
                    netid_lookup, limit=limit)
    return l.load()


def load_reviewerships(data_dir, non_faculty_gwids, netid_lookup, limit=None):
    print "Loading mygw reviewerships."

    l = BasicLoader("mygw_editorial.xml", data_dir, Reviewership, non_faculty_gwids,
                    netid_lookup, limit=limit)
    return l.load()


def load_presentations(data_dir, non_faculty_gwids, netid_lookup, limit=None):
    print "Loading mygw presentations."

    l = BasicLoader("mygw_presentation.xml", data_dir, Presentation, non_faculty_gwids,
                    netid_lookup, limit=limit)
    return l.load()


def load_users(data_dir, store_dir, non_faculty_gwids, netid_lookup, limit=None):
    print "Loading mygw users."

    # Setup orcid2vivo store
    store = orcid2vivo_loader.Store(store_dir)
    # Set everyone to inactive
    store.delete_all()

    g = Graph(namespace_manager=ns_manager)

    for result_num, result in enumerate(xml_result_generator(os.path.join(data_dir, "mygw_users.xml"))):
        if result["gw_id"] in non_faculty_gwids:
            person = Person(netid_lookup[result["gw_id"]])
            # If there is an orcid id, add to store.
            if result["orcid_id"]:
                orcid_id = clean_orcid(result["orcid_id"])
                if is_valid_orcid(orcid_id):
                    store.add(orcid_id, person_uri=person.uri, confirmed=True)
                else:
                    warning_log.warn("Orcid for %s is not valid: %s", result["gw_id"], result["orcid_id"])

            # Add languages spoken
            if result["languages"]:
                languages = result["languages"].split(",")
                for language in languages:
                    add_language(language, person.uri, g)
            if limit and result_num >= limit-1:
                break

    return g


def load_mediaexperts(data_dir, store_dir, non_faculty_gwids, faculty_gwids, netid_lookup, limit=None):
    print "Loading mediaexperts"

    g = Graph(namespace_manager=ns_manager)

    for result_num, result in enumerate(xml_result_generator(os.path.join(data_dir, "mygw_mediaexperts.xml"))):
        if result["gw_id"] in non_faculty_gwids or result["gw_id"] in faculty_gwids:
            person = Person(netid_lookup[result["gw_id"]])

            # Add name
            if result["last_name"]:
                # Switched for testing sorting
                full_name = join_if_not_empty((result["first_name"], result["middle_name"], result["last_name"]))
                inverse_full_name = join_if_not_empty(
                    ("{},".format(result["last_name"]) if result["last_name"] else result["last_name"],
                     result["first_name"],
                     result["middle_name"]))

                # Person
                g.add((person.uri, RDFS.label, Literal(inverse_full_name)))
                g.add((person.uri, LOCAL.normalOrderName, Literal(full_name)))

                vcard_name_uri = person.uri + "-vcard-name"
                g.add((vcard_name_uri, RDF.type, VCARD.Name))
                g.add((person.vcard_uri, VCARD.hasName, vcard_name_uri))
                if result["first_name"]:
                    g.add((vcard_name_uri, VCARD.givenName, Literal(result["first_name"])))
                if result["middle_name"]:
                    g.add((vcard_name_uri, VIVO.middleName, Literal(result["middle_name"])))
                if result["last_name"]:
                    g.add((vcard_name_uri, VCARD.familyName, Literal(result["last_name"])))
                if result["suffix_name"]:
                    g.add((vcard_name_uri, VCARD.honorificSuffix, Literal(result["suffix_name"])))

            # Add personal statement
            if result["personal_statement"]:
                g.add((person.uri, VIVO.overview, Literal(result["personal_statement"])))

            # Add media mentions
            if result["media_mentions"]:
                g.add((person.uri, LOCAL.mediaMentions, Literal(result["media_mentions"])))

            # Add commentary
            if result["commentary"]:
                g.add((person.uri, LOCAL.commentary, Literal(result["commentary"])))

            # Add research areas
            if result["research_areas"]:
                for research_area in result["research_areas"].split(","):
                    research_area_uri = D[to_hash_identifier(PREFIX_RESEARCH_AREA, [research_area, ])]
                    g.add((research_area_uri, RDF.type, SKOS.concept))
                    g.add((research_area_uri, RDFS.label, Literal(research_area)))
                    g.add((person.uri, VIVO.hasResearchArea, research_area_uri))

            # Add multimedia
            if result["multimedia"]:
                for multimedia_string in result["multimedia"].split(","):
                    (multimedia_type, multimedia_label, multimedia_url) = multimedia_string.split("|")
                    multimedia_uri = D[to_hash_identifier(PREFIX_MULTIMEDIA, multimedia_url)]
                    if multimedia_type == "A":
                        multimedia_class = BIBO.AudioDocument
                    else:
                        multimedia_class = VIVO.Video
                    g.add((multimedia_uri, RDF.type, multimedia_class))
                    g.add((person.uri, LOCAL.multimedia, multimedia_uri))
                    g.add((multimedia_uri, RDFS.label, Literal(multimedia_label)))
                    g.add((multimedia_uri, VCARD.url, Literal(multimedia_url, datatype=XSD.anyURI)))
            if limit and result_num >= limit-1:
                break

    return g
