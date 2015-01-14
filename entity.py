from namespace import *
from utility import *
from rdflib import Graph
import re


class Person():
    def __init__(self, gw_id, person_type="FacultyMember", load_vcards=True):
        self.gw_id = gw_id
        self.uri = D[self.gw_id]
        self.person_type = person_type
        self.load_vcards = load_vcards

        self.first_name = None
        self.middle_name = None
        self.last_name = None
        self.email = None
        self.fixed_line = None
        self.fax = None
        self.personal_statement = None
        self.facility = None
        self.address = None
        self.city = None
        self.state = None
        self.zip = None
        self.country = None

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
            if self.email:
                vcard_email_uri = D["%s-vcard-email" % self.gw_id]
                g.add((vcard_email_uri, RDF.type, VCARD.Email))
                g.add((vcard_email_uri, RDF.type, VCARD.Work))
                g.add((vcard_uri, VCARD.hasEmail, vcard_email_uri))
                g.add((vcard_email_uri, VCARD.email, Literal(self.email)))

            #Phone vcard
            if self.fixed_line:
                vcard_phone_uri = D["%s-vcard-phone" % self.gw_id]
                g.add((vcard_phone_uri, RDF.type, VCARD.Telephone))
                g.add((vcard_phone_uri, RDF.type, VCARD.Work))
                g.add((vcard_phone_uri, RDF.type, VCARD.Voice))
                g.add((vcard_uri, VCARD.hasTelephone, vcard_phone_uri))
                g.add((vcard_phone_uri, VCARD.telephone, Literal(self.fixed_line)))

            if self.fax:
                vcard_fax_uri = D["%s-vcard-fax" % self.gw_id]
                g.add((vcard_fax_uri, RDF.type, VCARD.Telephone))
                g.add((vcard_fax_uri, RDF.type, VCARD.Work))
                g.add((vcard_fax_uri, RDF.type, VCARD.Fax))
                g.add((vcard_uri, VCARD.hasTelephone, vcard_fax_uri))
                g.add((vcard_fax_uri, VCARD.telephone, Literal(self.fax)))

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

        return g


class Facility():

    def __init__(self, building_name, room_number=None):
        self.building_name = building_name
        self.room_number = room_number
        self.name = self.building_name
        if self.room_number:
            self.name = "%s %s" % (self.building_name, self.room_number)
        self.uri = D[to_identifier("site", self.name)]

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        building_uri = D[to_identifier("site", self.building_name)]
        g.add((building_uri, RDF.type, VIVO.Building))
        g.add((building_uri, RDFS.label, Literal(self.building_name)))
        if self.room_number:
            g.add((self.uri, RDF.type, VIVO.Room))
            #Part of
            g.add((self.uri, OBO.BFO_0000050, building_uri))
            g.add((self.uri, RDFS.label, Literal(self.name)))

        return g


class Department():

    def __init__(self, name):
        self.name = name
        self.uri = D[to_identifier("org", self.name)]

        self.college_name = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Department
        g.add((self.uri, RDF.type, VIVO.AcademicDepartment))
        g.add((self.uri, RDFS.label, Literal(self.name)))

        #College
        if self.college_name:
            college_uri = D[to_identifier("org", self.college_name)]
            g.add((college_uri, RDF.type, VIVO.College))
            g.add((college_uri, RDFS.label, Literal(self.college_name)))
            #Part of
            g.add((self.uri, OBO.BFO_0000050, college_uri))

        return g


class Organization():

    def __init__(self, name):
        self.name = name
        self.uri = D[to_identifier("org", self.name)]

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Department
        g.add((self.uri, RDF.type, FOAF.Organization))
        g.add((self.uri, RDFS.label, Literal(self.name)))

        return g


class AcademicAppointment():

    def __init__(self, department, person, rank):
        self.department = department
        self.person = person
        self.rank = rank
        self.uri = D[to_hash_identifier("apt", (department.uri, person.uri, rank))]

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


class Document():

    def __init__(self, title, research_group_code, contribution_type_code, person):
        self.title = title
        self.person = person
        self.research_group_code = research_group_code
        self.uri = D[to_hash_identifier("doc", (person.uri, title, research_group_code))]
        self.contribution_type_code = contribution_type_code

        self.contribution_start_year = None
        self.contribution_start_month = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Type
        if self.research_group_code == "LIT_BOOK":
            g.add((self.uri, RDF.type, BIBO.Book))
        elif self.research_group_code == "LIT_PUBLICATION":
            if self.contribution_type_code == "GW_RESEARCH_TYPE_CD1":
                g.add((self.uri, RDF.type, BIBO.AcademicArticle))

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


class Grant():

    def __init__(self, title, grant_role_code, person):
        self.title = title
        self.grant_role_code = grant_role_code
        self.person = person
        self.uri = D[to_hash_identifier("grant", (person.uri, title, grant_role_code))]

        self.contribution_start_year = None
        self.contribution_start_month = None
        self.award_amount = None

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

        #Date
        interval_uri = self.uri + "-interval"
        start_uri = interval_uri + "-start"
        add_date(start_uri, self.contribution_start_year, g, self.contribution_start_month)
        add_date_interval(interval_uri, self.uri, g, start_uri)

        #Award amount
        if self.award_amount:
            #Extract digits
            clean_award_amount = "${:,}".format(int(re.sub("\D", "", str(self.award_amount))))
            g.add((self.uri, VIVO.totalAwardAmount, Literal(clean_award_amount)))

        return g


class Degree():

    def __init__(self, person, organization, degree_name):
        self.person = person
        self.organization = organization
        self.degree_name = degree_name
        self.uri = D[to_hash_identifier("awdgre", (person.uri, organization.uri, degree_name))]

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
        degree_uri = D[to_identifier("dgre", self.degree_name)]
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
