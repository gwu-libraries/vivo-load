from fis_load import BasicLoader

import orcid2vivo_loader
from orcid2vivo_app.utility import clean_orcid, is_valid_orcid
import os
from loader.fis_entity import Award, ProfessionalMembership, Reviewership, Presentation
from loader.fis_entity import Person
from rdflib import Graph
from utility import xml_result_generator, ns_manager, add_language, warning_log
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
