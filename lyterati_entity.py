from utility import *
from rdflib import Graph
import re
from prefixes import *


class Person():
    def __init__(self, gw_id):
        self.gw_id = gw_id
        self.uri = D[to_hash_identifier(PREFIX_PERSON, (self.gw_id,))]

        self.personal_statement = None
        self.home_department = None
        self.scholarly_interest = None

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Overview
        if self.personal_statement:
            g.add((self.uri, VIVO.overview, Literal(self.personal_statement)))

        ##Scholarly interest
        if self.scholarly_interest:
            research_area_uri = D[to_hash_identifier(PREFIX_RESEARCH_AREA, [self.scholarly_interest,])]
            g.add((research_area_uri, RDF.type, SKOS.concept))
            g.add((research_area_uri, RDFS.label, Literal(self.scholarly_interest)))
            g.add((self.uri, VIVO.hasResearchArea, research_area_uri))

        ##Home Department
        if self.home_department:
            g.add((self.uri, LOCAL.homeDept, self.home_department.uri))

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

    def __init__(self, title, person):
        Document.__init__(self, title, person)

        self.publisher = None

    def _get_document_type(self):
        return BIBO.Book

    def to_graph(self):
        g = Document.to_graph(self)

        #Publisher
        if self.publisher:
            g.add((self.uri, VIVO.publisher, self.publisher.uri))

        return g


class Article(Document):

    def __init__(self, title, person):
        Document.__init__(self, title, person)

        self.publication_venue_name = None

    def _get_document_type(self):
        return BIBO.Article

    def _get_publication_venue_type(self):
        return BIBO.Periodical

    def to_graph(self):
        g = Document.to_graph(self)

        #Publication venue
        if self.publication_venue_name:
            journal_uri = D[to_hash_identifier(PREFIX_JOURNAL, (self._get_publication_venue_type(), self.publication_venue_name,))]
            g.add((journal_uri, RDF.type, self._get_publication_venue_type()))
            g.add((journal_uri, RDFS.label, Literal(self.publication_venue_name)))
            g.add((self.uri, VIVO.hasPublicationVenue, journal_uri))

        return g


class AcademicArticle(Article):

    def _get_document_type(self):
        return BIBO.AcademicArticle

    def _get_publication_venue_type(self):
        return BIBO.Journal


class ArticleAbstract(AcademicArticle):

    def _get_document_type(self):
        return VIVO.Abstract


class Review(AcademicArticle):

    def _get_document_type(self):
        return VIVO.Review


class ReferenceArticle(Article):
    #Article in Dictionary or Encyclopedia

    def _get_publication_venue_type(self):
        return BIBO.ReferenceSource


class Letter(AcademicArticle):

    def _get_document_type(self):
        return BIBO.Letter


class Chapter(Article):

    def _get_document_type(self):
        return BIBO.Chapter

    def _get_publication_venue_type(self):
        return BIBO.Book


class Report(Document):

    def __init__(self, title, person):
        Document.__init__(self, title, person)

        self.distributor = None

    def _get_document_type(self):
        return BIBO.Report

    def to_graph(self):
        g = Document.to_graph(self)

        #Distributor
        if self.distributor:
            g.add((self.uri, BIBO.distributor, self.distributor.uri))

        return g


class ConferenceAbstract(Document):

    def __init__(self, title, person, conference):
        Document.__init__(self, title, person)

        self.conference = conference

    def _get_document_type(self):
        return VIVO.Abstract

    def to_graph(self):
        g = Document.to_graph(self)

        #Presented at
        conference_uri = D[to_hash_identifier(PREFIX_EVENT, (self.conference,))]
        g.add((conference_uri, RDF.type, BIBO.Conference))
        g.add((conference_uri, RDFS.label, Literal(self.conference)))
        g.add((self.uri, BIBO.presentedAt, conference_uri))

        return g


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
        self.awarded_by = None

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
        if self.award_amount and re.search("\d", unicode(self.award_amount)):
            #Extract digits
            clean_award_amount = "${:,}".format(int(re.sub("\D", "", unicode(self.award_amount))))
            g.add((self.uri, VIVO.totalAwardAmount, Literal(clean_award_amount)))

        #Awarded by
        if self.awarded_by:
            g.add((self.uri, VIVO.assignedBy, self.awarded_by.uri))

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
        self.course_title = None

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
        course_name = "%s (%s %s)" % (self.course_title,
                                      strip_gw_prefix(self.subject_id), strip_gw_prefix(self.course_id))
        g.add((course_uri, RDFS.label, Literal(course_name)))
        g.add((self.uri, OBO.BFO_0000054, course_uri))

        #Interval
        #Start and end are the same
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_season_date(interval_start_uri, self.start_term, g) else None,
                          interval_start_uri if add_season_date(interval_start_uri, self.start_term, g) else None)

        return g


class ProfessionalMembership():

    def __init__(self, person, organization, position):
        self.person = person
        self.organization = organization
        self.position = position
        self.uri = D[to_hash_identifier(PREFIX_MEMBERSHIP, (person.uri, organization.uri, position))]

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
        g.add((self.uri, RDFS.label, Literal(self.position)))

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

    def __init__(self, person, service_name, position):
        self.person = person
        #Service name is the name of the journal
        self.service_name = service_name
        self.position = position
        self.uri = D[to_hash_identifier(PREFIX_REVIEWERSHIP, (person.uri, service_name, position))]

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
        g.add((self.uri, RDFS.label, Literal(self.position)))

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

    def _get_event_type(self):
        return BIBO.Conference

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
        #Presentation part of Event
        event_uri = D[to_hash_identifier(PREFIX_EVENT, (self.service_name,))]
        g.add((event_uri, RDF.type, self._get_event_type()))
        g.add((event_uri, RDFS.label, Literal(self.service_name)))
        g.add((presentation_uri, OBO.BFO_0000050, event_uri))

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


class Testimony(Presentation):

    def __init__(self, person, title, name):
        Presentation.__init__(self, person, title, name)

    def _get_event_type(self):
        return BIBO.Hearing