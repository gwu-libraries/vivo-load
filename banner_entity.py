from utility import *
from rdflib import Graph
from prefixes import *


class Person():
    def __init__(self, gw_id, load_vcards=True):
        self.gw_id = gw_id
        self.uri = D[to_hash_identifier(PREFIX_PERSON, (self.gw_id,))]
        self.load_vcards = load_vcards

        self.first_name = None
        self.middle_name = None
        self.last_name = None
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

        full_name = join_if_not_empty((self.first_name, self.middle_name, self.last_name))

        ##Person
        g.add((self.uri, RDFS.label, Literal(full_name)))
        #Note that not assigning class here.

        ##vcard
        if self.load_vcards:
            #Main vcard
            vcard_uri = self.uri + "-vcard"
            g.add((vcard_uri, RDF.type, VCARD.Individual))
            #Contact info for
            g.add((vcard_uri, OBO.ARG_2000029, self.uri))
            #Name vcard
            vcard_name_uri = self.uri + "-vcard-name"
            g.add((vcard_name_uri, RDF.type, VCARD.Name))
            g.add((vcard_uri, VCARD.hasName, vcard_name_uri))
            if self.first_name:
                g.add((vcard_name_uri, VCARD.givenName, Literal(self.first_name)))
            if self.middle_name:
                g.add((vcard_name_uri, VCARD.middleName, Literal(self.middle_name)))
            if self.last_name:
                g.add((vcard_name_uri, VCARD.familyName, Literal(self.last_name)))

            #Email vcard
            if self.email:
                vcard_email_uri = self.uri + "-vcard-email"
                g.add((vcard_email_uri, RDF.type, VCARD.Email))
                g.add((vcard_email_uri, RDF.type, VCARD.Work))
                g.add((vcard_uri, VCARD.hasEmail, vcard_email_uri))
                g.add((vcard_email_uri, VCARD.email, Literal(self.email)))

            #Phone vcard
            if self.phone:
                vcard_phone_uri = self.uri + "-vcard-phone"
                g.add((vcard_phone_uri, RDF.type, VCARD.Telephone))
                g.add((vcard_phone_uri, RDF.type, VCARD.Work))
                g.add((vcard_phone_uri, RDF.type, VCARD.Voice))
                g.add((vcard_uri, VCARD.hasTelephone, vcard_phone_uri))
                g.add((vcard_phone_uri, VCARD.telephone, Literal(self.phone)))

            #Address vcard
            if self.address1 and self.city and self.zip:
                vcard_address_uri = self.uri + "-vcard-address"
                g.add((vcard_address_uri, RDF.type, VCARD.Address))
                g.add((vcard_address_uri, RDF.type, VCARD.Work))
                g.add((vcard_uri, VCARD.hasAddress, vcard_address_uri))
                g.add((vcard_address_uri, VCARD.streetAddress,
                       Literal(join_if_not_empty((self.address1, self.address2, self.address3), sep="; "))))
                g.add((vcard_address_uri, VCARD.locality, Literal(self.city)))
                if self.state:
                    g.add((vcard_address_uri, VCARD.region, Literal(self.state)))
                g.add((vcard_address_uri, VCARD.postalCode, Literal(self.zip)))
                g.add((vcard_address_uri, VCARD.country, Literal("USA")))

        return g


class NonFaculty():
    def __init__(self, gw_id, person_type):
        self.gw_id = gw_id
        self.uri = D[to_hash_identifier(PREFIX_PERSON, (self.gw_id,))]
        self.person_type = person_type

        self.home_org_cd = None
        self.title = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Person type
        g.add((self.uri, RDF.type, getattr(VIVO, self.person_type)))

        #Position
        if self.title:
            appt_uri = D[to_hash_identifier(PREFIX_APPOINTMENT, (self.gw_id, self.title))]
            g.add((appt_uri, RDF.type, VIVO.NonFacultyAcademicPosition))
            g.add((appt_uri, RDFS.label, Literal(self.title)))
            #Related by
            g.add((self.uri, VIVO.relatedBy, appt_uri))
            home_org_uri = D[to_hash_identifier(PREFIX_ORGANIZATION, (self.home_org_cd,))]
            g.add((home_org_uri, VIVO.relatedBy, appt_uri))

        return g


class Faculty():
    def __init__(self, gw_id):
        self.gw_id = gw_id
        self.uri = D[to_hash_identifier(PREFIX_PERSON, (self.gw_id,))]

        self.department_cd = None
        self.title = None
        self.start_term = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Person type
        g.add((self.uri, RDF.type, VIVO.FacultyMember))

        #Appointment
        appt_uri = D[to_hash_identifier(PREFIX_APPOINTMENT, (self.gw_id,))]
        g.add((appt_uri, RDF.type, VIVO.FacultyPosition))
        g.add((appt_uri, RDFS.label, Literal(self.title)))
        #Related by
        g.add((self.uri, VIVO.relatedBy, appt_uri))
        department_uri = D[to_hash_identifier(PREFIX_ORGANIZATION, (self.department_cd,))]
        g.add((department_uri, VIVO.relatedBy, appt_uri))

        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_season_date(interval_start_uri, self.start_term, g) else None,
                          None)

        return g


class Organization():

    def __init__(self, org_id, name, organization_type="Organization"):
        self.org_id = org_id
        self.name = name
        self.organization_type = organization_type
        self.uri = D[to_hash_identifier(PREFIX_ORGANIZATION, (self.org_id,))]

        self.part_of = None

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
            part_of_uri = D[to_hash_identifier(PREFIX_ORGANIZATION, (self.part_of,))]
            g.add((self.uri, OBO.BFO_0000050, part_of_uri))

        return g


class Course():
    #"G10002741","625-25","LAW","200003","Fed Criminal Appellate Clinc","4","9",
    def __init__(self, gw_id, course_number, course_subject, start_term):
        self.gw_id = gw_id
        self.course_number = course_number
        self.course_subject = course_subject
        self.start_term = start_term
        self.uri = D[to_hash_identifier(PREFIX_TEACHER, (self.gw_id, self.course_number,
                                                         self.course_subject, self.start_term))]

        self.course_title = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Teacher Role
        g.add((self.uri, RDF.type, VIVO.TeacherRole))

        #Inheres in person
        person_uri = D[to_hash_identifier(PREFIX_PERSON, (self.gw_id,))]
        g.add((self.uri, OBO.RO_0000052, person_uri))

        #Realized in course
        course_uri = D[to_hash_identifier(PREFIX_COURSE, (self.course_number, self.course_subject))]
        g.add((course_uri, RDF.type, VIVO.Course))
        course_name = "%s (%s %s)" % (self.course_title,
                                      self.course_subject, self.course_number)
        g.add((course_uri, RDFS.label, Literal(course_name)))
        g.add((self.uri, OBO.BFO_0000054, course_uri))

        #Interval
        #Start and end are the same
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_season_date(interval_start_uri, self.start_term, g) else None,
                          None)

        return g
