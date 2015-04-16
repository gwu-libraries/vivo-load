import os
from fis_entity import *
from banner_load import get_faculty_gwids
import codecs
import csv

GWU = "The George Washington University"


def get_department_names(data_dir):
    department_names = []
    with codecs.open(os.path.join(data_dir, "fis_departments.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file, delimiter="\t")

        for row_num, row in enumerate(reader):
            #Skip header
            if row_num == 0:
                continue
            department_names.append(row[1])
    return department_names


def valid_department_name(name):
    if name and name not in ("No Department","University-level Dept"):
        return True
    return False


def valid_college_name(name):
    if name and name not in ("University","No College Designated"):
        return True
    return False


class Loader():
    def __init__(self, filename, data_dir,
                 has_fac=False, entity_class=None, field_to_entity=None, field_rename=None,
                 add_entities_from_fields=None,
                 limit=None, fac_limit=None):
        self.filename = filename
        self.data_dir = data_dir
        self.limit = limit
        #Map of result field names to entity classes. Classes must take a single positional argument.
        self.field_to_entity = field_to_entity or {}
        #Map of result field names to rename.
        self.field_rename = field_rename or {}
        #The entity class to create.
        self.entity_class = entity_class
        #List of fields that contain entities that should be added to graph.
        self.add_entities_from_fields = add_entities_from_fields or []

        #Create an RDFLib Graph
        self.g = Graph(namespace_manager=ns_manager)

        #Get faculty ids from banner
        self.fac_gw_ids = None
        if has_fac:
            self.fac_gw_ids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    def load(self):
        addl_entities = self._addl_entities()
        for entity in addl_entities:
            self.g += entity.to_graph()

        for result_num, result in enumerate(xml_result_generator(os.path.join(self.data_dir, self.filename))):
            #Check the _use_result function
            if (self._use_result(result)
                #Optionally limit by faculty ids
                and (self.fac_gw_ids is None or result["gw_id"] in self.fac_gw_ids)):
                #Optionally process the result to change values
                self._process_result(result)

                #Optionally map some result values to entities (e.g., organization)
                for key, clazz in self.field_to_entity.items():
                    if key in result:
                        result[key] = clazz(result[key])

                #Optionally rename some fields
                for src_key, dest_key in self.field_rename.items():
                    if src_key in result:
                        result[dest_key] = result[src_key]
                        del result[src_key]

                #Generate the entities
                entities = self._generate_entities(result)
                for entity in entities:
                    self.g += entity.to_graph()
            if self.limit and result_num >= self.limit-1:
                break

        return self.g

    def _addl_entities(self):
        return []

    def _use_result(self, result):
        return True

    def _process_result(self, result):
        pass

    def _generate_entities(self, result):
        #Instantiate an entity using the result as keyword args
        entities = [self._create_entity(self.entity_class, result)]
        for field in self.add_entities_from_fields:
            if field in result and result[field] and hasattr(result[field], "to_graph"):
                entities.append(result[field])

        return entities

    @staticmethod
    def _create_entity(clazz, args):
        remove_extra_args(args, clazz.__init__)
        return clazz(**args)


class BasicLoader(Loader):
    """
    A Loader that maps gw_id field to a Person entity
    and organization field to an Organization entity.

    The Organization entity is also added to the graph.
    """

    def __init__(self, filename, data_dir, entity_class=None,
                 limit=None, fac_limit=None):
        Loader.__init__(self, filename, data_dir, has_fac=True, entity_class=entity_class,
                        field_to_entity={"gw_id": Person, "organization": Organization},
                        field_rename={"gw_id": "person"}, add_entities_from_fields=["organization"],
                        limit=limit, fac_limit=fac_limit)


class DepartmentLoader(Loader):
    def __init__(self, data_dir, limit=None):
        Loader.__init__(self, "fis_department.xml", data_dir, limit=limit)
        self.gwu = Organization(GWU, organization_type="University", is_gw=True)

    def _addl_entities(self):
        return [self.gwu]

    def _use_result(self, result):
        return valid_department_name(result["department"]) and valid_college_name(result["college"])

    def _generate_entities(self, result):
        #College
        c = Organization(result["college"], organization_type="College", is_gw=True, part_of=self.gwu)
        #Department
        d = Organization(result["department"], organization_type="Department", is_gw=True, part_of=c)
        return [c, d]


def load_departments(data_dir, limit=None):
    print "Loading departments."

    l = DepartmentLoader(data_dir)
    return l.load()


class FacultyLoader(Loader):
    def __init__(self, data_dir, limit=None, fac_limit=None):
        Loader.__init__(self, "fis_faculty.xml", data_dir, has_fac=True, entity_class=Person,
                        field_to_entity={"home_department": Organization}, limit=limit, fac_limit=fac_limit)

    def _process_result(self, result):
        if not (valid_department_name(result["home_department"]) and valid_college_name(result["home_college"])):
            #Remove home department
            del result["home_department"]


def load_faculty(data_dir, limit=None, fac_limit=None):
    print "Loading faculty."

    l = FacultyLoader(data_dir, limit=limit, fac_limit=fac_limit)
    return l.load()


class AcademicAppointmentLoader(Loader):
    def __init__(self, data_dir, limit=None, fac_limit=None):
        Loader.__init__(self, "fis_academic_appointment.xml", data_dir, has_fac=True, entity_class=AcademicAppointment,
                        field_to_entity={"organization": Organization, "gw_id": Person},
                        field_rename={"gw_id": "person"},
                        limit=limit, fac_limit=fac_limit)

    def _use_result(self, result):
        return valid_department_name(result["department"]) or valid_college_name(result["college"])

    def _process_result(self, result):
        if valid_department_name(result["department"]):
            result["organization"] = result["department"]
        #Else, if College name, then College
        else:
            result["organization"] = result["college"]


def load_academic_appointment(data_dir, limit=None, fac_limit=None):
    print "Loading academic appointments."

    l = AcademicAppointmentLoader(data_dir, limit=limit, fac_limit=fac_limit)
    return l.load()


class AdminAppointmentLoader(Loader):
    def __init__(self, data_dir, limit=None, fac_limit=None):
        Loader.__init__(self, "fis_admin_appointment.xml", data_dir, has_fac=True, entity_class=AdminAppointment,
                        field_to_entity={"organization": Organization, "gw_id": Person},
                        field_rename={"gw_id": "person"},
                        limit=limit, fac_limit=fac_limit)
        self.gwu = Organization(GWU, organization_type="University", is_gw=True)

    def _addl_entities(self):
        return [self.gwu]

    def _use_result(self, result):
        return valid_department_name(result["department"]) or valid_college_name(result["college"])

    def _process_result(self, result):
        #If Department name, then Department
        if valid_department_name(result["department"]):
            result["organization"] = result["department"]
        #Else, if College name, then College
        elif valid_college_name(result["college"]):
            result["organization"] = result["college"]
        #Else GWU
        else:
            result["organization"] = GWU


def load_admin_appointment(data_dir, limit=None, fac_limit=None):
    print "Loading admin appointments."

    l = AdminAppointmentLoader(data_dir, limit=limit, fac_limit=fac_limit)
    return l.load()


def load_research(data_dir, limit=None, contribution_type_limit=None,
                  research_group_codes=None, contribution_type_codes=None, fac_limit=None):
    print """
    Loading research. Limit is %s. Contribution type limit is %s. Research group codes is %s.
    Contribution types codes is %s.
    """ % (limit, contribution_type_limit, research_group_codes, contribution_type_codes)

    #Get faculty ids from banner
    faculty_gw_ids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    ws = XlWrapper(os.path.join(data_dir, "Research.xlsx"))
    #Skip header row
    row_num = 1
    contribution_type_count = 0
    while ((row_num < (limit or ws.nrows))
           and (contribution_type_limit is None or contribution_type_count < contribution_type_limit)):
        #Person stub
        gw_id = strip_gw_prefix(ws.cell_value(row_num, "Faculty ID"))
        if gw_id in faculty_gw_ids:
            p = Person(gw_id)

            title = ws.cell_value(row_num, "Title")
            research_group_code = ws.cell_value(row_num, "Research Group CD(Headings)")
            contribution_type_code = ws.cell_value(row_num, "Contribution Type CD")
            contribution_start_year = ws.cell_value(row_num, "Contribution Start Year")
            contribution_start_month = ws.cell_value(row_num, "Contribution Start Month")
            name = ws.cell_value(row_num, "Name")
            if ((research_group_codes is None or research_group_code in research_group_codes)
                    and (contribution_type_codes is None or contribution_type_code in contribution_type_codes)):
                r = None
                #Book
                if research_group_code == "LIT_BOOK" and title:
                    r = Book(title, p)
                    if name:
                        o = Organization(name)
                        g += o.to_graph()
                        r.publisher = o
                #Report
                elif (research_group_code == "LIT_PUBLICATION" and contribution_type_code in (
                      #Report
                      "GW_RESEARCH_TYPE_CD5",
                      #Policy brief
                      "GW_RESEARCH_TYPE_CD68", ) and title):
                    r = Report(title, p)
                    if name:
                        o = Organization(name)
                        g += o.to_graph()
                        r.distributor = o
                #Article
                elif (research_group_code == "LIT_PUBLICATION" and contribution_type_code in (
                      #Essay
                      "GW_RESEARCH_TYPE_CD2",
                      #Non-refereed article
                      "GW_RESEARCH_TYPE_CD4") and title):
                    r = Article(title, p)
                    if name:
                        r.publication_venue_name = name
                #Academic article
                elif (research_group_code == "LIT_PUBLICATION" and contribution_type_code in (
                      #Refereed article
                      "GW_RESEARCH_TYPE_CD1",
                      #Other
                      "GW_RESEARCH_TYPE_CD8",
                      #Invited article
                      "GW_RESEARCH_TYPE_CD67",
                      #Law review and journal
                      "GW_RESEARCH_TYPE_CD74") and title):
                    r = AcademicArticle(title, p)
                    if name:
                        r.publication_venue_name = name
                #Article abstract
                elif (research_group_code == "LIT_PUBLICATION" and
                        contribution_type_code in (
                            #Abstract
                            "GW_RESEARCH_TYPE_CD88",) and title):
                    r = ArticleAbstract(title, p)
                    if name:
                        r.publication_venue_name = name
                #Review
                elif (research_group_code == "LIT_PUBLICATION" and
                        contribution_type_code in (
                            #Critique and review
                            "GW_RESEARCH_TYPE_CD7",
                            #Book review
                            "GW_RESEARCH_TYPE_CD75",) and title):
                    r = Review(title, p)
                    if name:
                        r.publication_venue_name = name
                #Reference article
                elif (research_group_code == "LIT_PUBLICATION" and
                        contribution_type_code in (
                            #Dictionary entry
                            "GW_RESEARCH_TYPE_CD86",
                            #Encyclopedia entry
                            "GW_RESEARCH_TYPE_CD87",) and title):
                    r = ReferenceArticle(title, p)
                    if name:
                        r.publication_venue_name = name
                #Letter
                elif (research_group_code == "LIT_PUBLICATION" and
                        contribution_type_code in (
                            #Letter
                            "GW_RESEARCH_TYPE_CD89",) and title):
                    r = Letter(title, p)
                    if name:
                        r.publication_venue_name = name
                #Testimony
                elif (research_group_code == "LIT_PUBLICATION" and
                        contribution_type_code in (
                            #Govt. Testimony
                            "GW_RESEARCH_TYPE_CD76",) and title and name):
                    r = Testimony(p, title, name)
                #Chapter
                elif research_group_code == "LIT_CHAPTER" and title:
                    r = Chapter(title, p)
                    if name:
                        r.publication_venue_name = name
                #Patent
                elif research_group_code == "LIT_PATENT":
                    patent_status_code = ws.cell_value(row_num, "Patent Status CD")
                    #Only accepted patents.  Submitted, pending, other, or blank are ignored.
                    if patent_status_code == "GW_PATENT_STATUS_CD1":
                        r = Patent(title, p)
                        r.patent = ws.cell_value(row_num, "Patent ID")
                #Grant
                elif research_group_code == "LIT_GRANT":
                    grant_status_code = ws.cell_value(row_num, "Grant Status CD")
                    #Awarded or closed (not proposed or rejected)
                    if grant_status_code in ("GW_GRANT_STATUS_CD3", "GW_GRANT_STATUS_CD5"):
                        grant_role_code = ws.cell_value(row_num, "Grant Role CD")
                        #Skip if no grant_role_code
                        if grant_role_code:
                            r = Grant(title, grant_role_code, p, contribution_start_year, contribution_start_month)
                            r.award_amount = ws.cell_value(row_num, "Award Amount")
                            award_begin_date = ws.cell_value(row_num, "Award Begin Date")
                            if award_begin_date:
                                (r.award_begin_year, r.award_begin_month, r.award_begin_day,
                                 hour, minute, nearest_second) = xlrd.xldate_as_tuple(award_begin_date, ws.datemode)
                            award_end_date = ws.cell_value(row_num, "Award End Date")
                            if award_end_date:
                                (r.award_end_year, r.award_end_month, r.award_end_day,
                                 hour, minute, nearest_second) = xlrd.xldate_as_tuple(award_end_date, ws.datemode)
                            name = ws.cell_value(row_num, "Name")
                            if name:
                                o = Organization(name)
                                g += o.to_graph()
                                r.awarded_by = o
                #Conference abstract
                elif (research_group_code == "LIT_CONFERENCE" and contribution_type_code in (
                        #Abstract
                        "GW_RESEARCH_TYPE_CD90",) and title):
                        r = ConferenceAbstract(title, p, name)

                if r:
                    r.contribution_start_year = contribution_start_year
                    r.contribution_start_month = contribution_start_month
                    r.additional_details = ws.cell_value(row_num, "Additional Details")
                    g += r.to_graph()
                    contribution_type_count += 1
        row_num += 1

    return g


def load_degree_education(data_dir, limit=None, fac_limit=None):
    print "Loading degree education."

    l = Loader("fis_degree_education.xml", data_dir, has_fac=True, entity_class=DegreeEducation,
               field_to_entity={"institution": Organization, "gw_id": Person},
               field_rename={"institution": "organization", "gw_id": "person"},
               add_entities_from_fields=["organization"],
               limit=limit, fac_limit=fac_limit)
    return l.load()


def load_non_degree_education(data_dir, limit=None, fac_limit=None):
    print "Loading non-degree education."

    l = Loader("fis_non_degree_education.xml", data_dir, has_fac=True, entity_class=NonDegreeEducation,
               field_to_entity={"institution": Organization, "gw_id": Person},
               field_rename={"institution": "organization", "gw_id": "person"},
               add_entities_from_fields=["organization"],
               limit=limit, fac_limit=fac_limit)
    return l.load()


def load_courses(data_dir, limit=None, fac_limit=None):
    print "Loading courses taught."

    l = BasicLoader("fis_courses.xml", data_dir, entity_class=Course,
                    limit=limit, fac_limit=fac_limit)
    return l.load()


def load_awards(data_dir, limit=None, fac_limit=None):
    print "Loading awards."

    l = BasicLoader("fis_awards.xml", data_dir, entity_class=Award,
                    limit=limit, fac_limit=fac_limit)
    return l.load()


def load_professional_memberships(data_dir, limit=None, fac_limit=None):
    print "Loading professional memberships."

    l = BasicLoader("fis_prof_memberships.xml", data_dir, entity_class=ProfessionalMembership,
                    limit=limit, fac_limit=fac_limit)
    return l.load()


def load_reviewerships(data_dir, limit=None, fac_limit=None):
    print "Loading reviewerships."

    l = BasicLoader("fis_reviewer.xml", data_dir, entity_class=Reviewership,
                    limit=limit, fac_limit=fac_limit)
    return l.load()


def load_presentations(data_dir, limit=None, fac_limit=None):
    print "Loading presentations."

    l = BasicLoader("fis_presentations.xml", data_dir, entity_class=Presentation,
                    limit=limit, fac_limit=fac_limit)
    return l.load()

