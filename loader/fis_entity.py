from utility import *
from rdflib import Graph
import re
from prefixes import *


class Person():
    def __init__(self, netid, personal_statement=None, home_department=None, research_areas=None, languages_known=None,
                 languages_other=None):
        self.netid = netid
        self.personal_statement = personal_statement
        self.home_department = home_department
        self.research_areas = research_areas
        self.languages_known = languages_known
        self.languages_other = languages_other

        self.uri = D[self.netid]

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Person type
        g.add((self.uri, RDF.type, VIVO.FacultyMember))

        #Overview
        if self.personal_statement:
            g.add((self.uri, VIVO.overview, Literal(self.personal_statement)))

        ##Research areas
        if self.research_areas:
            #Split on ; then ,
            research_area_split = re.split("; *", self.research_areas)
            if len(research_area_split) == 1:
                research_area_split = re.split(", *", self.research_areas)
            for research_area in research_area_split:
                if research_area:
                    research_area_uri = D[to_hash_identifier(PREFIX_RESEARCH_AREA, [research_area, ])]
                    g.add((research_area_uri, RDF.type, SKOS.concept))
                    g.add((research_area_uri, RDFS.label, Literal(research_area[0].capitalize() + research_area[1:])))
                    g.add((self.uri, VIVO.hasResearchArea, research_area_uri))

        ##Home Department
        if self.home_department:
            g.add((self.uri, LOCAL.homeDept, self.home_department.uri))

        ##Languages
        if self.languages_known:
            for language_code in re.split(", *", self.languages_known):
                if language_code in language_map:
                    add_language(language_map[language_code], self.uri, g)

        if self.languages_other:
            for language in re.split(", *", self.languages_other):
                add_language(language, self.uri, g)

        return g


class Organization():

    def __init__(self, name, organization_type="Organization", is_gw=False, part_of=None):
        self.name = name
        self.organization_type = organization_type
        self.is_gw = is_gw
        self.part_of = part_of

        self.uri = D[to_hash_identifier(PREFIX_ORGANIZATION, (self.name,))]

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


class Appointment():

    def __init__(self, person, organization, rank, appt_type,
                 title=None, start_term=None, end_term=None):
        self.person = person
        self.organization = organization
        self.rank = rank
        self.appt_type = appt_type
        self.title = title
        self.start_term = start_term
        self.end_term = end_term

        self.uri = D[
            to_hash_identifier(PREFIX_APPOINTMENT, (person.uri, organization.uri, rank, title, start_term, end_term))]

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        g.add((self.uri, RDF.type, self.appt_type))
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


class AcademicAppointment(Appointment):

    def __init__(self, person, organization, rank,
                 title=None, start_term=None, end_term=None):
        Appointment.__init__(self, person, organization, rank, VIVO.FacultyPosition,
                             title=title, start_term=start_term, end_term=end_term)


class AdminAppointment(Appointment):

    def __init__(self, person, organization, rank,
                 title=None, start_term=None, end_term=None):
        Appointment.__init__(self, person, organization, rank, VIVO.FacultyAdministrativePosition,
                             title=title, start_term=start_term, end_term=end_term)


class Document():

    def __init__(self, person, title, start_year=None, start_month=None):
        self.title = title
        self.person = person
        self.start_year = start_year
        self.start_month = start_month

        self.uri = D[to_hash_identifier(PREFIX_DOCUMENT, (person.uri, title, self._get_document_type()))]

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
        add_date(date_uri, self.start_year, g, self.start_month)

        return g

    def _get_document_type(self):
        return BIBO.Document


class Book(Document):

    def __init__(self, person, title, publisher=None, start_year=None):
        Document.__init__(self, person, title, start_year=start_year)
        self.publisher = publisher

    def _get_document_type(self):
        return BIBO.Book

    def to_graph(self):
        g = Document.to_graph(self)

        #Publisher
        if self.publisher:
            g.add((self.uri, VIVO.publisher, self.publisher.uri))

        return g


class Article(Document):

    def __init__(self, person, title, start_year=None, start_month=None, publication_venue=None):
        Document.__init__(self, person, title, start_year=start_year, start_month=start_month)
        self.publication_venue = publication_venue

    def _get_document_type(self):
        return BIBO.Article

    def _get_publication_venue_type(self):
        return BIBO.Periodical

    def to_graph(self):
        g = Document.to_graph(self)

        #Publication venue
        if self.publication_venue:
            journal_uri = D[to_hash_identifier(PREFIX_JOURNAL, (self._get_publication_venue_type(),
                                                                self.publication_venue,))]
            g.add((journal_uri, RDF.type, self._get_publication_venue_type()))
            g.add((journal_uri, RDFS.label, Literal(self.publication_venue)))
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

    def __init__(self, person, title, start_year=None, start_month=None, distributor=None):
        Document.__init__(self, person, title, start_year=start_year, start_month=start_month)
        self.distributor = distributor

    def _get_document_type(self):
        return BIBO.Report

    def to_graph(self):
        g = Document.to_graph(self)

        #Distributor
        if self.distributor:
            g.add((self.uri, BIBO.distributor, self.distributor.uri))

        return g


class ConferenceDocument(Document):

    def __init__(self, person, title, conference, start_year=None, start_month=None):
        Document.__init__(self, person, title, start_year=start_year, start_month=start_month)
        self.conference = conference

    def to_graph(self):
        g = Document.to_graph(self)

        #Presented at
        conference_uri = D[to_hash_identifier(PREFIX_EVENT, (self.conference,))]
        g.add((conference_uri, RDF.type, BIBO.Conference))
        g.add((conference_uri, RDFS.label, Literal(self.conference)))
        g.add((self.uri, BIBO.presentedAt, conference_uri))

        return g


class ConferenceAbstract(ConferenceDocument):

    def _get_document_type(self):
        return VIVO.Abstract


class ConferencePaper(ConferenceDocument):

    def _get_document_type(self):
        return VIVO.ConferencePaper


class ConferencePoster(ConferenceDocument):

    def _get_document_type(self):
        return VIVO.ConferencePoster


class Patent():

    def __init__(self, person, title, patent=None, start_year=None, start_month=None):
        self.title = title
        self.person = person
        self.start_year = start_year
        self.start_month = start_month
        self.patent = patent

        self.uri = D[to_hash_identifier(PREFIX_PATENT, (person.uri, title))]

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
        add_date(date_uri, self.start_year, g, self.start_month)

        return g


class Grant():

    def __init__(self, person, title, grant_role, start_year=None, start_month=None,
                 award_amount=None, awarded_by=None,
                 award_start_year=None, award_start_month=None, award_start_day=None,
                 award_end_year=None, award_end_month=None, award_end_day=None):
        self.title = title
        self.grant_role = grant_role
        self.person = person

        self.award_amount = award_amount
        self.award_start_year = award_start_year
        self.award_start_month = award_start_month
        self.award_start_day = award_start_day
        self.award_end_year = award_end_year
        self.award_end_month = award_end_month
        self.award_end_day = award_end_day
        #Organization awarding the grant
        self.awarded_by = awarded_by

        #Using start year, month to disambiguate grants, but not storing.
        self.uri = D[to_hash_identifier(PREFIX_GRANT, (person.uri, title, grant_role,
                                                       start_year, start_month))]

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
            "PI": VIVO.PrincipalInvestigatorRole,
            "Co-PI": VIVO.CoPrincipalInvestigatorRole,
            "Member": VIVO.ResearcherRole,
            #Just role
            "Other": OBO.BFO_0000023
        }[self.grant_role]))
        #Inheres in
        g.add((role_uri, OBO.RO_0000052, self.person.uri))
        g.add((role_uri, VIVO.relatedBy, self.uri))

        #Date interval
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        interval_end_uri = interval_uri + "-end"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_date(interval_start_uri,
                                                         self.award_start_year,
                                                         g,
                                                         self.award_start_month,
                                                         self.award_start_day) else None,
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

    def __init__(self, person, organization, degree,
                 program=None, major=None, start_term=None, end_term=None):
        self.person = person
        self.organization = organization
        self.degree_name = degree
        self.program = program
        self.major = major
        self.start_term = start_term
        self.end_term = end_term
        self.uri = D[to_hash_identifier(PREFIX_AWARDED_DEGREE, (person.uri, organization.uri, degree))]

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

    def __init__(self, person, course_id, course=None):
        self.person = person
        self.course_id = course_id
        self.course = course
        self.uri = D[to_hash_identifier(PREFIX_TEACHER, (person.uri, self.course_id))]

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Teacher Role
        g.add((self.uri, RDF.type, VIVO.TeacherRole))

        #Inheres in person
        g.add((self.uri, OBO.RO_0000052, self.person.uri))

        #Realized in course
        course_uri = D[to_hash_identifier(PREFIX_COURSE, (self.course_id,))]
        g.add((course_uri, RDF.type, VIVO.Course))
        course_name = "%s (%s)" % (self.course, self.course_id)
        g.add((course_uri, RDFS.label, Literal(course_name)))
        g.add((self.uri, OBO.BFO_0000054, course_uri))

        return g


class ProfessionalMembership():

    def __init__(self, person, organization, position=None,
                 start_year=None, start_month=None,
                 end_year=None, end_month=None):
        self.person = person
        self.organization = organization
        self.position = position
        self.start_year = start_year
        self.start_month = start_month
        self.end_year = end_year
        self.end_month = end_month

        self.uri = D[to_hash_identifier(PREFIX_MEMBERSHIP, (person.uri, organization.uri, position, start_year,
                                                            start_month, end_year, end_month))]

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Contributes to Organization
        g.add((self.uri, VIVO.roleContributesTo, self.organization.uri))

        #Inheres in Person
        g.add((self.uri, OBO.RO_0000052, self.person.uri))

        if self.position:
            #Service provider role
            g.add((self.uri, RDF.type, OBO.ERO_0000012))
            #Label is position
            g.add((self.uri, RDFS.label, Literal(self.position)))

        #Interval
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        interval_end_uri = interval_uri + "-end"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_date(interval_start_uri,
                                                         self.start_year,
                                                         g,
                                                         self.start_month) else None,
                          interval_end_uri if add_date(interval_end_uri,
                                                       self.end_year,
                                                       g,
                                                       self.end_month) else None)

        return g


class Reviewership():

    def __init__(self, person, journal, position=None,
                 start_year=None, start_month=None, end_year=None, end_month=None):
        self.person = person
        #Service name is the name of the journal
        self.journal = journal
        self.position = position
        self.start_year = None
        self.start_month = None
        self.end_year = None
        self.end_month = None

        self.uri = D[to_hash_identifier(PREFIX_REVIEWERSHIP, (person.uri, journal, position, start_year, start_month,
                                                              end_year, end_month))]

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Reviewer role
        g.add((self.uri, RDF.type, VIVO.ReviewerRole))
        #Label is position
        if self.position:
            g.add((self.uri, RDFS.label, Literal(self.position)))

        #Contributes to Journal
        #Although it seems not all of these are journals
        journal_uri = D[to_hash_identifier(PREFIX_JOURNAL, (self.journal,))]
        g.add((journal_uri, RDF.type, BIBO.Journal))
        g.add((journal_uri, RDFS.label, Literal(self.journal)))
        g.add((self.uri, VIVO.roleContributesTo, journal_uri))

        #Inheres in Person
        g.add((self.uri, OBO.RO_0000052, self.person.uri))

        #Interval
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        interval_end_uri = interval_uri + "-end"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_date(interval_start_uri,
                                                         self.start_year,
                                                         g,
                                                         self.start_month) else None,
                          interval_end_uri if add_date(interval_end_uri,
                                                       self.end_year,
                                                       g,
                                                       self.end_month) else None)

        return g


class Award():

    def __init__(self, person, award, organization=None, start_year=None, start_month=None):
        self.person = person
        self.organization = organization
        self.award = award
        self.start_year = start_year
        self.start_month = start_month

        self.uri = D[to_hash_identifier(PREFIX_AWARD_RECEIPT, (person.uri, award))]

    def to_graph(self):
        #Create an RDFLib Graph
        g = Graph()

        #Award Receipt
        g.add((self.uri, RDF.type, VIVO.AwardReceipt))
        g.add((self.uri, RDFS.label, Literal("Awarded %s" % self.award)))

        #Assigned by Organization
        if self.organization:
            g.add((self.uri, VIVO.assignedBy, self.organization.uri))

        #Relates to Person
        g.add((self.uri, VIVO.relates, self.person.uri))

        #Relates to Award
        award_uri = D[to_hash_identifier(PREFIX_AWARD, (self.award,))]
        g.add((award_uri, RDF.type, VIVO.Award))
        g.add((award_uri, RDFS.label, Literal(self.award)))
        g.add((self.uri, VIVO.relates, award_uri))

        #Date/Time value
        date_uri = self.uri + "-date"
        g.add((self.uri, VIVO.dateTimeValue, date_uri))
        add_date(date_uri, self.start_year, g, self.start_month)

        return g


class Presentation():

    def __init__(self, person, title, event, start_year=None, start_month=None):
        self.person = person
        #Title of the presentation
        self.title = title
        #Where presented
        self.event = event
        self.start_year = start_year
        self.start_month = start_month

        self.uri = D[to_hash_identifier(PREFIX_PRESENTER, (person.uri, title, event, start_year, start_month))]

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
        event_uri = D[to_hash_identifier(PREFIX_EVENT, (self.event,))]
        g.add((event_uri, RDF.type, self._get_event_type()))
        g.add((event_uri, RDFS.label, Literal(self.event)))
        g.add((presentation_uri, OBO.BFO_0000050, event_uri))

        #Inheres in person
        g.add((self.uri, OBO.RO_0000052, self.person.uri))

        #Date/time interval (no end)
        interval_uri = self.uri + "-interval"
        interval_start_uri = interval_uri + "-start"
        add_date_interval(interval_uri, self.uri, g,
                          interval_start_uri if add_date(interval_start_uri,
                                                         self.start_year,
                                                         g,
                                                         self.start_month) else None)

        return g


class Testimony(Presentation):

    def __init__(self, person, title, event, start_year=None, start_month=None):
        Presentation.__init__(self, person, title, event, start_year=start_year, start_month=start_month)

    def _get_event_type(self):
        return BIBO.Hearing