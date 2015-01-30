#from namespace import *
from utility import *
from rdflib import Graph
import re

#Prefixes
PREFIX_APPOINTMENT = "apt"
PREFIX_AWARD_RECEIPT = "awdrec"
PREFIX_AWARD = "awd"
PREFIX_AWARDED_DEGREE = "awdgre"
PREFIX_CONFERENCE = "conf"
PREFIX_COURSE = "crs"
PREFIX_DEGREE = "dgre"
PREFIX_DOCUMENT = "doc"
PREFIX_GRANT = "grant"
PREFIX_JOURNAL = "jrnl"
PREFIX_MEMBERSHIP = "memb"
PREFIX_NON_DEGREE = "nondgre"
PREFIX_ORGANIZATION = "org"
PREFIX_PATENT = "pat"
PREFIX_PERSON = "per"
PREFIX_PRESENTER = "presr"
PREFIX_PRESENTATION = "pres"
PREFIX_REVIEWERSHIP = "rev"
PREFIX_SITE = "site"
PREFIX_TEACHER = "tch"


class Person():
    def __init__(self, gw_id, person_type="FacultyMember", load_vcards=True):
        self.gw_id = gw_id
        self.uri = D[to_hash_identifier(PREFIX_PERSON, (self.gw_id,))]
        self.person_type = person_type
        self.load_vcards = load_vcards

        self.first_name = None
        self.middle_name = None
        self.last_name = None
        self.fixed_line = None
        self.fax = None
        self.personal_statement = None
        self.facility = None
        self.address = None
        self.city = None
        self.state = None
        self.zip = None
        self.country = None
        self.home_department = None
        self.username = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        full_name = join_if_not_empty((self.first_name, self.middle_name, self.last_name))

        ##FacultyMember
        g.add((self.uri, RDF.type, getattr(VIVO, self.person_type)))
        g.add((self.uri, RDFS.label, Literal(full_name)))
        #Overview
        if self.personal_statement:
            g.add((self.uri, VIVO.overview, Literal(self.personal_statement)))

        ##vcard
        if self.load_vcards:
            #Main vcard
            vcard_uri = D["%s-vcard" % self.gw_id]
            g.add((vcard_uri, RDF.type, VCARD.Individual))
            #Contact info for
            g.add((vcard_uri, OBO.ARG_2000029, self.uri))
            #Name vcard
            vcard_name_uri = D["%s-vcard-name" % self.gw_id]
            g.add((vcard_name_uri, RDF.type, VCARD.Name))
            g.add((vcard_uri, VCARD.hasName, vcard_name_uri))
            if self.first_name:
                g.add((vcard_name_uri, VCARD.givenName, Literal(self.first_name)))
            if self.middle_name:
                g.add((vcard_name_uri, VCARD.middleName, Literal(self.middle_name)))
            if self.last_name:
                g.add((vcard_name_uri, VCARD.familyName, Literal(self.last_name)))

            #Email vcard
            if self.username:
                vcard_email_uri = D["%s-vcard-email" % self.gw_id]
                g.add((vcard_email_uri, RDF.type, VCARD.Email))
                g.add((vcard_email_uri, RDF.type, VCARD.Work))
                g.add((vcard_uri, VCARD.hasEmail, vcard_email_uri))
                g.add((vcard_email_uri, VCARD.email, Literal("%s@gwu.edu" % self.username)))

            #Phone vcard
            if self.fixed_line:
                vcard_phone_uri = D["%s-vcard-phone" % self.gw_id]
                g.add((vcard_phone_uri, RDF.type, VCARD.Telephone))
                g.add((vcard_phone_uri, RDF.type, VCARD.Work))
                g.add((vcard_phone_uri, RDF.type, VCARD.Voice))
                g.add((vcard_uri, VCARD.hasTelephone, vcard_phone_uri))
                g.add((vcard_phone_uri, VCARD.telephone, Literal(num_to_str(self.fixed_line))))

            if self.fax:
                vcard_fax_uri = D["%s-vcard-fax" % self.gw_id]
                g.add((vcard_fax_uri, RDF.type, VCARD.Telephone))
                g.add((vcard_fax_uri, RDF.type, VCARD.Work))
                g.add((vcard_fax_uri, RDF.type, VCARD.Fax))
                g.add((vcard_uri, VCARD.hasTelephone, vcard_fax_uri))
                g.add((vcard_fax_uri, VCARD.telephone, Literal(num_to_str(self.fax))))

            #Address vcard
            if self.address and self.city and self.zip:
                vcard_address_uri = D["%s-vcard-address" % self.gw_id]
                g.add((vcard_address_uri, RDF.type, VCARD.Address))
                g.add((vcard_address_uri, RDF.type, VCARD.Work))
                g.add((vcard_uri, VCARD.hasAddress, vcard_address_uri))
                g.add((vcard_address_uri, VCARD.streetAddress, Literal(self.address)))
                g.add((vcard_address_uri, VCARD.locality, Literal(self.city)))
                if self.state:
                    g.add((vcard_address_uri, VCARD.region, Literal(self.state)))
                g.add((vcard_address_uri, VCARD.postalCode, Literal(self.zip)))
                g.add((vcard_address_uri, VCARD.country, Literal(self.country or "USA")))

        ##Facility
        if self.facility:
            #Location of
            g.add((self.facility.uri, OBO.RO_0001015, self.uri))

        ##Home Department
        if self.home_department:
            g.add((self.uri, LOCAL.homeDept, self.home_department.uri))

        return g


class Facility():

    def __init__(self, building_name, room_number=None):
        self.building_name = building_name
        self.room_number = room_number
        self.name = self.building_name
        if self.room_number:
            self.name = "%s %s" % (self.building_name, self.room_number)
        self.uri = D[to_hash_identifier(PREFIX_SITE, (self.building_name, self.room_number))]

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        building_uri = D[to_hash_identifier(PREFIX_SITE, (self.building_name,))]
        g.add((building_uri, RDF.type, VIVO.Building))
        g.add((building_uri, RDFS.label, Literal(self.building_name)))
        if self.room_number:
            g.add((self.uri, RDF.type, VIVO.Room))
            #Part of
            g.add((self.uri, OBO.BFO_0000050, building_uri))
            g.add((self.uri, RDFS.label, Literal(self.name)))

        return g


class Organization():

    def __init__(self, name, organization_type="Organization", is_gw=False):
        self.name = name
        self.organization_type = organization_type
        self.is_gw = is_gw
        self.uri = D[to_hash_identifier(PREFIX_ORGANIZATION, (self.name,))]

        self.part_of = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Department
        g.add((self.uri, RDF.type,
               FOAF.Organization if self.organization_type == "Organization"
               else getattr(VIVO, self.organization_type)))
        if self.is_gw:
            g.add((self.uri, RDF.type, LOCAL.InstitutionalInternal))
        g.add((self.uri, RDFS.label, Literal(self.name)))

        #Part of
        if self.part_of:
            g.add((self.uri, OBO.BFO_0000050, self.part_of.uri))

        return g


class AcademicAppointment():

    def __init__(self, person, department, rank):
        self.department = department
        self.person = person
        self.rank = rank
        self.uri = D[to_hash_identifier(PREFIX_APPOINTMENT, (department.uri, person.uri, rank))]

        self.start_term = None
        self.end_term = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        g.add((self.uri, RDF.type, VIVO.FacultyPosition))
        g.add((self.uri, RDFS.label, Literal(self.rank)))
        #Related by
        g.add((self.person.uri, VIVO.relatedBy, self.uri))
        g.add((self.department.uri, VIVO.relatedBy, self.uri))

        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        interval_end_uri = interval_uri + "-end"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_season_date(interval_start_uri, self.start_term, g) else None,
                          interval_end_uri if add_season_date(interval_end_uri, self.end_term, g) else None)

        return g


class AdminAppointment():

    def __init__(self, person, organization, rank):
        self.person = person
        self.organization = organization
        self.rank = rank
        self.uri = D[to_hash_identifier(PREFIX_APPOINTMENT, (person.uri, organization.uri, rank))]

        self.title = None
        self.start_term = None
        self.end_term = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        g.add((self.uri, RDF.type, VIVO.FacultyAdministrativePosition))
        #Title otherwise rank
        g.add((self.uri, RDFS.label, Literal(self.title or self.rank)))
        #Related by
        g.add((self.person.uri, VIVO.relatedBy, self.uri))
        g.add((self.organization.uri, VIVO.relatedBy, self.uri))

        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        interval_end_uri = interval_uri + "-end"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_season_date(interval_start_uri, self.start_term, g) else None,
                          interval_end_uri if add_season_date(interval_end_uri, self.end_term, g) else None)

        return g


class Document():

    def __init__(self, title, person):
        self.title = title
        self.person = person
        self.uri = D[to_hash_identifier(PREFIX_DOCUMENT, (person.uri, title, self._get_document_type()))]

        self.contribution_start_year = None
        self.contribution_start_month = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Type
        g.add((self.uri, RDF.type, self._get_document_type()))

        #Person (via Authorship)
        authorship_uri = self.uri + "-auth"
        g.add((authorship_uri, RDF.type, VIVO.Authorship))
        g.add((authorship_uri, VIVO.relates, self.uri))
        g.add((authorship_uri, VIVO.relates, self.person.uri))

        #Title
        g.add((self.uri, RDFS.label, Literal(self.title)))

        #Date
        date_uri = self.uri + "-date"
        g.add((self.uri, VIVO.dateTimeValue, date_uri))
        add_date(date_uri, self.contribution_start_year, g, self.contribution_start_month)

        return g

    def _get_document_type(self):
        return BIBO.Document


class Book(Document):

    def _get_document_type(self):
        return BIBO.Book


class AcademicArticle(Document):

    def _get_document_type(self):
        return BIBO.AcademicArticle


class Patent():

    def __init__(self, title, person):
        self.title = title
        self.person = person
        self.uri = D[to_hash_identifier(PREFIX_PATENT, (person.uri, title))]

        self.contribution_start_year = None
        self.contribution_start_month = None
        self.patent = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Type
        g.add((self.uri, RDF.type, BIBO.Patent))

        #Assignee
        g.add((self.uri, VIVO.assignee, self.person.uri))

        #Title
        g.add((self.uri, RDFS.label, Literal(self.title)))

        #Patent
        if self.patent:
            g.add((self.uri, VIVO.patentNumber, Literal(num_to_str(self.patent))))

        #Date
        date_uri = self.uri + "-date"
        g.add((self.uri, VIVO.dateTimeValue, date_uri))
        add_date(date_uri, self.contribution_start_year, g, self.contribution_start_month)

        return g


class Grant():

    def __init__(self, title, grant_role_code, person, contribution_start_year=None, contribution_start_month=None):
        self.title = title
        self.grant_role_code = grant_role_code
        self.person = person
        #Using contribution start year, month to disambiguate grants, but not storing.
        self.uri = D[to_hash_identifier(PREFIX_GRANT, (person.uri, title, grant_role_code,
                                                       contribution_start_year, contribution_start_month))]

        self.award_amount = None
        self.award_begin_year = None
        self.award_begin_month = None
        self.award_begin_day = None
        self.award_end_year = None
        self.award_end_month = None
        self.award_end_day = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Type
        g.add((self.uri, RDF.type, VIVO.Grant))

        #Person
        g.add((self.uri, VIVO.relates, self.person.uri))

        #Title
        g.add((self.uri, RDFS.label, Literal(self.title)))

        #Role
        role_uri = self.uri + "-role"
        g.add((role_uri, RDF.type, {
            "GW_GRANT_ROLE_CD1": VIVO.PrincipalInvestigatorRole,
            "GW_GRANT_ROLE_CD2": VIVO.CoPrincipalInvestigatorRole,
            "GW_GRANT_ROLE_CD3": VIVO.ResearcherRole,
            #Just role
            "GW_GRANT_ROLE_CD4": OBO.BFO_0000023
        }[self.grant_role_code]))
        #Inheres in
        g.add((role_uri, OBO.RO_0000052, self.person.uri))
        g.add((role_uri, VIVO.relatedBy, self.uri))

        #Date interval
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        interval_end_uri = interval_uri + "-end"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_date(interval_start_uri,
                                                         self.award_begin_year,
                                                         g,
                                                         self.award_begin_month,
                                                         self.award_begin_day) else None,
                          interval_end_uri if add_date(interval_end_uri,
                                                       self.award_end_year,
                                                       g,
                                                       self.award_end_month,
                                                       self.award_end_day) else None)

        #Award amount
        if self.award_amount:
            #Extract digits
            clean_award_amount = "${:,}".format(int(re.sub("\D", "", str(self.award_amount))))
            g.add((self.uri, VIVO.totalAwardAmount, Literal(clean_award_amount)))

        return g


class DegreeEducation():

    def __init__(self, person, organization, degree_name):
        self.person = person
        self.organization = organization
        self.degree_name = degree_name
        self.uri = D[to_hash_identifier(PREFIX_AWARDED_DEGREE, (person.uri, organization.uri, degree_name))]

        self.program = None
        self.major = None
        self.start_term = None
        self.end_term = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Awarded degree
        g.add((self.uri, RDF.type, VIVO.AwardedDegree))
        g.add((self.uri, RDFS.label, Literal(self.degree_name)))
        #Assigned by organization
        g.add((self.uri, VIVO.assignedBy, self.organization.uri))

        #Relates to degree
        degree_uri = D[to_hash_identifier(PREFIX_DEGREE, (self.degree_name,))]
        g.add((degree_uri, RDF.type, VIVO.AcademicDegree))
        g.add((degree_uri, RDFS.label, Literal("%s degree" % self.degree_name)))
        g.add((self.uri, VIVO.relates, degree_uri))

        #Relates to person
        g.add((self.uri, VIVO.relates, self.person.uri))

        #Output of educational process
        educational_process_uri = self.uri + "-process"
        g.add((educational_process_uri, RDF.type, VIVO.EducationalProcess))
        g.add((self.uri, OBO.RO_0002353, educational_process_uri))
        #Has participants
        g.add((educational_process_uri, OBO.RO_0000057, self.organization.uri))
        g.add((educational_process_uri, OBO.RO_0000057, self.person.uri))
        #Major
        major_or_program = self.major or self.program
        if major_or_program:
            g.add((educational_process_uri, VIVO.majorField, Literal(major_or_program)))
        #Interval
        interval_uri = educational_process_uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        interval_end_uri = interval_uri + "-end"
        add_date_interval(interval_uri, educational_process_uri, g,
                          interval_start_uri if add_season_date(interval_start_uri, self.start_term, g) else None,
                          interval_end_uri if add_season_date(interval_end_uri, self.end_term, g) else None)

        return g


class NonDegreeEducation():

    def __init__(self, person, organization, degree=None, program=None):
        self.person = person
        self.organization = organization
        self.degree = degree
        self.program = program
        self.uri = D[to_hash_identifier(PREFIX_NON_DEGREE, (person.uri, organization.uri, degree, program))]

        self.start_term = None
        self.end_term = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #All are Postdoctoral-training, since can't differentiate
        #medical residencies, etc.
        g.add((self.uri, RDF.type, VIVO.PostdoctoralTraining))
        g.add((self.uri, VIVO.supplementalInformation, Literal(self.degree or self.program)))
        #Has participant
        g.add((self.uri, OBO.RO_0000057, self.organization.uri))
        g.add((self.uri, OBO.RO_0000057, self.person.uri))

        #Interval
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        interval_end_uri = interval_uri + "-end"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_season_date(interval_start_uri, self.start_term, g) else None,
                          interval_end_uri if add_season_date(interval_end_uri, self.end_term, g) else None)

        return g


class Course():

    def __init__(self, person, course_id, subject_id, start_term):
        self.person = person
        self.course_id = num_to_str(course_id)
        self.subject_id = subject_id
        self.start_term = start_term
        self.uri = D[to_hash_identifier(PREFIX_TEACHER, (person.uri, self.course_id, self.subject_id, self.start_term))]

        self.end_term = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Teacher Role
        g.add((self.uri, RDF.type, VIVO.TeacherRole))

        #Inheres in person
        g.add((self.uri, OBO.RO_0000052, self.person.uri))

        #Realized in course
        course_uri = D[to_hash_identifier(PREFIX_COURSE, (self.course_id, self.subject_id))]
        g.add((course_uri, RDF.type, VIVO.Course))
        course_name = strip_gw_prefix(self.subject_id) + " " + strip_gw_prefix(self.course_id)
        g.add((course_uri, RDFS.label, Literal(course_name)))
        g.add((self.uri, OBO.BFO_0000054, course_uri))

        #Interval
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        interval_end_uri = interval_uri + "-end"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_season_date(interval_start_uri, self.start_term, g) else None,
                          interval_end_uri if add_season_date(interval_end_uri, self.end_term, g) else None)

        return g


class ProfessionalMembership():

    def __init__(self, person, organization, position_code):
        self.person = person
        self.organization = organization
        self.position_code = position_code
        self.uri = D[to_hash_identifier(PREFIX_MEMBERSHIP, (person.uri, organization.uri, position_code))]

        self.contribution_start_year = None
        self.contribution_start_month = None
        self.contribution_end_year = None
        self.contribution_end_month = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Service provider role
        g.add((self.uri, RDF.type, OBO.ERO_0000012))
        #Label is position
        g.add((self.uri, RDFS.label, Literal(
            {
                "GW_OUTREACH_POSITION_CD16": "Member",
                "GW_OUTREACH_POSITION_CD17": "President",
                "GW_OUTREACH_POSITION_CD18": "Secretary",
                "GW_OUTREACH_POSITION_CD19": "Treasurer",
                "GW_OUTREACH_POSITION_CD20": "Vice-President",
                "GW_OUTREACH_POSITION_CD21": "Senior Member",
                "GW_OUTREACH_POSITION_CD22": "Other",

            }[self.position_code]
        )))

        #Contributes to Organization
        g.add((self.uri, VIVO.roleContributesTo, self.organization.uri))

        #Inheres in Person
        g.add((self.uri, OBO.RO_0000052, self.person.uri))

        #Interval
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        interval_end_uri = interval_uri + "-end"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_date(interval_start_uri,
                                                         self.contribution_start_year,
                                                         g,
                                                         self.contribution_start_month) else None,
                          interval_end_uri if add_date(interval_end_uri,
                                                       self.contribution_end_year,
                                                       g,
                                                       self.contribution_end_month) else None)

        return g


class Reviewership():

    def __init__(self, person, service_name, position_code):
        self.person = person
        #Service name is the name of the journal
        self.service_name = service_name
        self.position_code = position_code
        self.uri = D[to_hash_identifier(PREFIX_REVIEWERSHIP, (person.uri, service_name, position_code))]

        self.contribution_start_year = None
        self.contribution_start_month = None
        self.contribution_end_year = None
        self.contribution_end_month = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Reviewer role
        g.add((self.uri, RDF.type, VIVO.ReviewerRole))
        #Label is position
        g.add((self.uri, RDFS.label, Literal(
            {
                "GW_OUTREACH_POSITION_CD1": "Editor",
                "GW_OUTREACH_POSITION_CD2": "Co-Editor",
                "GW_OUTREACH_POSITION_CD3": "Associate Editor",
                "GW_OUTREACH_POSITION_CD4": "Editorial Board",
                "GW_OUTREACH_POSITION_CD5": "Reviewer",
                "GW_OUTREACH_POSITION_CD6": "Special Issue Editor",
                "GW_OUTREACH_POSITION_CD7": "Area Editor",
                "GW_OUTREACH_POSITION_CD8": "Other",
                "GW_OUTREACH_POSITION_CD9": "Referee",
                "GW_OUTREACH_POSITION_CD10": "Member",
                "GW_OUTREACH_POSITION_CD11": "Chair",
                "GW_OUTREACH_POSITION_CD12": "Co-Chair",
                "GW_OUTREACH_POSITION_CD22": "Other",
            }[self.position_code]
        )))

        #Contributes to Journal
        #Although it seems not all of these are journals
        journal_uri = D[to_hash_identifier(PREFIX_JOURNAL, (self.service_name,))]
        g.add((journal_uri, RDF.type, BIBO.Journal))
        g.add((journal_uri, RDFS.label, Literal(self.service_name)))
        g.add((self.uri, VIVO.roleContributesTo, journal_uri))

        #Inheres in Person
        g.add((self.uri, OBO.RO_0000052, self.person.uri))

        #Interval
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        interval_end_uri = interval_uri + "-end"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_date(interval_start_uri,
                                                         self.contribution_start_year,
                                                         g,
                                                         self.contribution_start_month) else None,
                          interval_end_uri if add_date(interval_end_uri,
                                                       self.contribution_end_year,
                                                       g,
                                                       self.contribution_end_month) else None)

        return g


class Award():

    def __init__(self, person, organization, title):
        self.person = person
        self.organization = organization
        self.title = title
        self.uri = D[to_hash_identifier(PREFIX_AWARD_RECEIPT, (person.uri, title))]

        self.contribution_start_year = None
        self.contribution_start_month = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Award Receipt
        g.add((self.uri, RDF.type, VIVO.AwardReceipt))
        g.add((self.uri, RDFS.label, Literal("Awarded %s" % self.title)))

        #Assigned by Organization
        if self.organization:
            g.add((self.uri, VIVO.assignedBy, self.organization.uri))

        #Relates to Person
        g.add((self.uri, VIVO.relates, self.person.uri))

        #Relates to Award
        award_uri = D[to_hash_identifier(PREFIX_AWARD, (self.title,))]
        g.add((award_uri, RDF.type, VIVO.Award))
        g.add((award_uri, RDFS.label, Literal(self.title)))
        g.add((self.uri, VIVO.relates, award_uri))

        #Date/Time value
        date_uri = self.uri + "-date"
        g.add((self.uri, VIVO.dateTimeValue, date_uri))
        add_date(date_uri, self.contribution_start_year, g, self.contribution_start_month)

        return g


class Presentation():

    def __init__(self, person, title, service_name):
        self.person = person
        #Title of the presentation
        self.title = title
        #Where presented
        self.service_name = service_name
        self.uri = D[to_hash_identifier(PREFIX_PRESENTER, (person.uri, title, service_name))]

        self.contribution_start_year = None
        self.contribution_start_month = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Presenter role
        g.add((self.uri, RDF.type, VIVO.PresenterRole))

        #Realized in presentation
        presentation_uri = D[to_hash_identifier(PREFIX_PRESENTATION, (self.title,))]
        g.add((presentation_uri, RDF.type, VIVO.Presentation))
        g.add((presentation_uri, RDFS.label, Literal(self.title)))
        g.add((self.uri, OBO.BFO_0000054, presentation_uri))
        #Presentation part of Conference
        conference_uri = D[to_hash_identifier(PREFIX_CONFERENCE, (self.service_name,))]
        g.add((conference_uri, RDF.type, BIBO.Conference))
        g.add((conference_uri, RDFS.label, Literal(self.service_name)))
        g.add((presentation_uri, OBO.BFO_0000050, conference_uri))

        #Inheres in person
        g.add((self.uri, OBO.RO_0000052, self.person.uri))

        #Date/time interval (no end)
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_date(interval_start_uri,
                                                         self.contribution_start_year,
                                                         g,
                                                         self.contribution_start_month) else None)

        return g
