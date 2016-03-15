from utility import *
from rdflib import Graph
from prefixes import *
import re


class Person():
    def __init__(self, netid, load_vcards=True):
        self.netid = netid
        self.uri = D[netid]
        self.vcard_uri = self.uri + "-vcard"
        self.load_vcards = load_vcards

        self.first_name = None
        self.middle_name = None
        self.last_name = None
        self.suffix = None
        self.address1 = None
        self.address2 = None
        self.address3 = None
        self.city = None
        self.state = None
        self.zip = None
        self.email = None
        self.phone = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        # Switched for testing sorting
        # full_name = join_if_not_empty((self.first_name, self.middle_name, self.last_name, self.suffix))
        full_name = join_if_not_empty((self.last_name, self.first_name, self.middle_name))

        ##Person
        if full_name:
            g.add((self.uri, RDFS.label, Literal(full_name)))
        #Note that not assigning class here.

        ##vcard
        if self.load_vcards:
            #Main vcard
            g.add((self.vcard_uri, RDF.type, VCARD.Individual))
            #Contact info for
            g.add((self.vcard_uri, OBO.ARG_2000029, self.uri))
            #Name vcard
            if self.first_name or self.middle_name or self.last_name:
                vcard_name_uri = self.uri + "-vcard-name"
                g.add((vcard_name_uri, RDF.type, VCARD.Name))
                g.add((self.vcard_uri, VCARD.hasName, vcard_name_uri))
                if self.first_name:
                    g.add((vcard_name_uri, VCARD.givenName, Literal(self.first_name)))
                if self.middle_name:
                    g.add((vcard_name_uri, VIVO.middleName, Literal(self.middle_name)))
                if self.last_name:
                    g.add((vcard_name_uri, VCARD.familyName, Literal(self.last_name)))
                if self.suffix:
                    g.add((vcard_name_uri, VCARD.honorificSuffix, Literal(self.suffix)))

            #Email vcard
            if self.email:
                vcard_email_uri = self.uri + "-vcard-email"
                g.add((vcard_email_uri, RDF.type, VCARD.Email))
                g.add((vcard_email_uri, RDF.type, VCARD.Work))
                g.add((self.vcard_uri, VCARD.hasEmail, vcard_email_uri))
                g.add((vcard_email_uri, VCARD.email, Literal(self.email)))

            #Phone vcard
            format_phone = format_phone_number(self.phone)
            if format_phone:
                vcard_phone_uri = self.uri + "-vcard-phone"
                g.add((vcard_phone_uri, RDF.type, VCARD.Telephone))
                g.add((vcard_phone_uri, RDF.type, VCARD.Work))
                g.add((vcard_phone_uri, RDF.type, VCARD.Voice))
                g.add((self.vcard_uri, VCARD.hasTelephone, vcard_phone_uri))
                g.add((vcard_phone_uri, VCARD.telephone, Literal(format_phone)))

            #Address vcard
            if self.address1 and self.city and self.zip:
                vcard_address_uri = self.uri + "-vcard-address"
                g.add((vcard_address_uri, RDF.type, VCARD.Address))
                g.add((vcard_address_uri, RDF.type, VCARD.Work))
                g.add((self.vcard_uri, VCARD.hasAddress, vcard_address_uri))
                g.add((vcard_address_uri, VCARD.streetAddress,
                       Literal(join_if_not_empty((self.address1, self.address2, self.address3), sep="; "))))
                g.add((vcard_address_uri, VCARD.locality, Literal(self.city)))
                if self.state:
                    g.add((vcard_address_uri, VCARD.region, Literal(self.state)))
                g.add((vcard_address_uri, VCARD.postalCode, Literal(self.zip)))
                g.add((vcard_address_uri, VCARD.country, Literal("USA")))

        return g


class NonFaculty():
    def __init__(self, person, person_type):
        self.person = person
        self.uri = self.person.uri
        self.person_type = person_type

        self.home_organization = None
        self.title = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Person type
        g.add((self.uri, RDF.type, getattr(VIVO, self.person_type)))

        #Position
        if self.title:
            #Remove level from librarian titles, e.g., Uv Librarian 4 FT
            clean_title = re.sub(r'(Lib(rarian)?) [0-4]', r'\1', self.title)
            appt_uri = D[to_hash_identifier(PREFIX_APPOINTMENT, (self.uri, self.title))]
            g.add((appt_uri, RDF.type, VIVO.NonFacultyAcademicPosition))
            g.add((appt_uri, RDFS.label, Literal(clean_title)))
            #Related by
            g.add((self.uri, VIVO.relatedBy, appt_uri))
            g.add((self.home_organization.uri, VIVO.relatedBy, appt_uri))

        return g


class Faculty():
    def __init__(self, person, load_appt=True):
        self.person = person
        self.uri = self.person.uri
        self.load_appt = load_appt

        self.department = None
        self.title = None
        self.start_term = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Person type
        g.add((self.uri, RDF.type, VIVO.FacultyMember))

        #Appointment
        if self.load_appt:
            appt_uri = D[to_hash_identifier(PREFIX_APPOINTMENT, (self.uri,))]
            g.add((appt_uri, RDF.type, VIVO.FacultyPosition))
            g.add((appt_uri, RDFS.label, Literal(self.title)))
            #Related by
            g.add((self.uri, VIVO.relatedBy, appt_uri))
            g.add((self.department.uri, VIVO.relatedBy, appt_uri))

            interval_uri = self.uri + "-interval"
            interval_start_uri = interval_uri + "-start"
            add_date_interval(interval_uri, self.uri, g,
                              interval_start_uri if add_season_date(interval_start_uri, self.start_term, g) else None,
                              None)

        return g


class Organization():

    def __init__(self, org_id, organization_type="Organization"):
        self.org_id = org_id
        self.organization_type = organization_type
        self.uri = D[to_hash_identifier(PREFIX_ORGANIZATION, (self.org_id,))]

        self.part_of = None
        self.name = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Department
        g.add((self.uri, RDF.type,
               FOAF.Organization if self.organization_type == "Organization"
               else getattr(VIVO, self.organization_type)))
        g.add((self.uri, RDF.type, LOCAL.InstitutionalInternal))
        g.add((self.uri, RDFS.label, Literal(self.name)))

        #Part of
        if self.part_of:
            g.add((self.uri, OBO.BFO_0000050, self.part_of.uri))

        return g


class Course():
    #"G10002741","625-25","LAW","200003","Fed Criminal Appellate Clinc","4","9",
    def __init__(self, person, course_number, course_subject, course_title):
        self.person = person
        self.course_number = course_number
        self.course_subject = course_subject
        self.course_title = course_title
        self.uri = D[to_hash_identifier(PREFIX_TEACHER, (self.person.uri, self.course_number,
                                                         self.course_subject))]

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Teacher Role
        g.add((self.uri, RDF.type, VIVO.TeacherRole))

        #Inheres in person
        g.add((self.uri, OBO.RO_0000052, self.person.uri))

        #Realized in course
        course_uri = D[to_hash_identifier(PREFIX_COURSE, (self.course_number, self.course_subject))]
        g.add((course_uri, RDF.type, VIVO.Course))
        course_name = "%s (%s %s)" % (self.course_title,
                                      self.course_subject, self.course_number)
        g.add((course_uri, RDFS.label, Literal(course_name)))
        g.add((self.uri, OBO.BFO_0000054, course_uri))

        return g
