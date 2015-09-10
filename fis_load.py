from fis_entity import *
from utility import valid_college_name, valid_department_name
import os

GWU = "The George Washington University"


class Loader():
    def __init__(self, filename, data_dir,
                 gwids=None, entity_class=None, field_to_entity=None, field_rename=None,
                 add_entities_from_fields=None,
                 limit=None):
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

        #Gwids
        self.gwids = gwids

    def load(self):
        addl_entities = self._addl_entities()
        for entity in addl_entities:
            self.g += entity.to_graph()

        try:
            row_count = 0
            for row_count, result in enumerate(xml_result_generator(os.path.join(self.data_dir, self.filename)),
                                                start=1):
                #Check the _use_result function
                if (self._use_result(result)
                        #Optionally limit by faculty ids
                        and (self.gwids is None or result["gw_id"] in self.gwids)):
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
                if self.limit and row_count > self.limit-1:
                    break

            if not row_count:
                warning_log.error("%s has no data.", self.filename)
                return None

            return self.g
        #If there is an IOError, log it and return None
        except IOError, e:
            warning_log.error("%s: %s", e.strerror, e.filename)
            return None


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

    def __init__(self, filename, data_dir, entity_class, gwids,
                 limit=None):
        Loader.__init__(self, filename, data_dir, gwids=gwids, entity_class=entity_class,
                        field_to_entity={"gw_id": Person, "organization": Organization},
                        field_rename={"gw_id": "person"}, add_entities_from_fields=["organization"],
                        limit=limit)


class DepartmentLoader(Loader):
    #List of departments that should be modeled as colleges.
    colleges = ("The Trachtenberg School of Public Policy and Public Administration",
                "Graduate School of Political Management",
                "School of Media and Public Affairs",
                "Corcoran School of the Arts & Design")

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
        d = Organization(result["department"],
                         organization_type="College" if result["department"] in self.colleges else "AcademicDepartment",
                         is_gw=True, part_of=c)
        return [c, d]


def load_departments(data_dir, limit=None):
    print "Loading departments."

    l = DepartmentLoader(data_dir, limit=limit)
    return l.load()


class FacultyLoader(Loader):
    def __init__(self, data_dir, gwids, limit=None):
        Loader.__init__(self, "fis_faculty.xml", data_dir, gwids=gwids, entity_class=Person,
                        field_to_entity={"home_department": Organization}, limit=limit)

    def _process_result(self, result):
        if not (valid_department_name(result["home_department"]) and valid_college_name(result["home_college"])):
            #Remove home department
            del result["home_department"]


def load_faculty(data_dir, faculty_gwids, limit=None):
    print "Loading faculty."

    l = FacultyLoader(data_dir, faculty_gwids, limit=limit)
    return l.load()


class AcademicAppointmentLoader(Loader):
    def __init__(self, data_dir, gwids, limit=None):
        Loader.__init__(self, "fis_academic_appointment.xml", data_dir, gwids=gwids,
                        entity_class=AcademicAppointment,
                        field_to_entity={"organization": Organization, "gw_id": Person},
                        field_rename={"gw_id": "person"},
                        limit=limit)

    def _use_result(self, result):
        return valid_department_name(result["department"]) or valid_college_name(result["college"])

    def _process_result(self, result):
        if valid_department_name(result["department"]):
            result["organization"] = result["department"]
        #Else, if College name, then College
        else:
            result["organization"] = result["college"]


def load_academic_appointment(data_dir, faculty_gwids, limit=None):
    print "Loading academic appointments."

    l = AcademicAppointmentLoader(data_dir, faculty_gwids, limit=limit)
    return l.load()


class AdminAppointmentLoader(Loader):
    def __init__(self, data_dir, gwids, limit=None):
        Loader.__init__(self, "fis_admin_appointment.xml", data_dir, gwids=gwids,
                        entity_class=AdminAppointment,
                        field_to_entity={"organization": Organization, "gw_id": Person},
                        field_rename={"gw_id": "person"},
                        limit=limit)
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


def load_admin_appointment(data_dir, faculty_gwids, limit=None):
    print "Loading admin appointments."

    l = AdminAppointmentLoader(data_dir, faculty_gwids, limit=limit)
    return l.load()


def load_degree_education(data_dir, faculty_gwids, limit=None):
    print "Loading degree education."

    l = Loader("fis_degree_education.xml", data_dir, gwids=faculty_gwids, entity_class=DegreeEducation,
               field_to_entity={"institution": Organization, "gw_id": Person},
               field_rename={"institution": "organization", "gw_id": "person"},
               add_entities_from_fields=["organization"],
               limit=limit)
    return l.load()


def load_non_degree_education(data_dir, faculty_gwids, limit=None):
    print "Loading non-degree education."

    l = Loader("fis_non_degree_education.xml", data_dir, gwids=faculty_gwids, entity_class=NonDegreeEducation,
               field_to_entity={"institution": Organization, "gw_id": Person},
               field_rename={"institution": "organization", "gw_id": "person"},
               add_entities_from_fields=["organization"],
               limit=limit)
    return l.load()


def load_courses(data_dir, faculty_gwids, limit=None,):
    print "Loading courses taught."

    l = BasicLoader("fis_courses.xml", data_dir, Course, faculty_gwids, limit=limit)
    return l.load()


def load_awards(data_dir, faculty_gwids, limit=None):
    print "Loading awards."

    l = BasicLoader("fis_awards.xml", data_dir, Award, faculty_gwids, limit=limit)
    return l.load()


def load_professional_memberships(data_dir, faculty_gwids, limit=None):
    print "Loading professional memberships."

    l = BasicLoader("fis_prof_memberships.xml", data_dir, ProfessionalMembership, faculty_gwids, limit=limit)
    return l.load()


def load_reviewerships(data_dir, faculty_gwids, limit=None):
    print "Loading reviewerships."

    l = BasicLoader("fis_reviewer.xml", data_dir, Reviewership, faculty_gwids, limit=limit)
    return l.load()


def load_presentations(data_dir, faculty_gwids, limit=None):
    print "Loading presentations."

    l = BasicLoader("fis_presentations.xml", data_dir, Presentation, faculty_gwids, limit=limit)
    return l.load()


def load_books(data_dir, faculty_gwids, limit=None):
    print "Loading books."

    l = Loader("fis_books.xml", data_dir, gwids=faculty_gwids, entity_class=Book,
               field_to_entity={"gw_id": Person, "publisher": Organization},
               field_rename={"gw_id": "person"}, add_entities_from_fields=["publisher"],
               limit=limit)
    return l.load()


def load_reports(data_dir, faculty_gwids, limit=None):
    print "Loading reports."

    l = Loader("fis_reports.xml", data_dir, gwids=faculty_gwids, entity_class=Book,
               field_to_entity={"gw_id": Person, "distributor": Organization},
               field_rename={"gw_id": "person"}, add_entities_from_fields=["distributor"],
               limit=limit)
    return l.load()


def load_articles(data_dir, faculty_gwids, limit=None):
    print "Loading articles"

    l = BasicLoader("fis_articles.xml", data_dir, Article, faculty_gwids, limit=limit)
    return l.load()


def load_academic_articles(data_dir, faculty_gwids, limit=None):
    print "Loading academic articles"

    l = BasicLoader("fis_acad_articles.xml", data_dir, AcademicArticle, faculty_gwids, limit=limit)
    return l.load()


def load_article_abstracts(data_dir, faculty_gwids, limit=None):
    print "Loading article abstracts"

    l = BasicLoader("fis_article_abstracts.xml", data_dir, ArticleAbstract, faculty_gwids, limit=limit)
    return l.load()


def load_reviews(data_dir, faculty_gwids, limit=None):
    print "Loading reviews"

    l = BasicLoader("fis_reviews.xml", data_dir, Review, faculty_gwids, limit=limit)
    return l.load()


def load_reference_articles(data_dir, faculty_gwids, limit=None):
    print "Loading reference articles"

    l = BasicLoader("fis_ref_articles.xml", data_dir, ReferenceArticle, faculty_gwids, limit=limit)
    return l.load()


def load_letters(data_dir, faculty_gwids, limit=None):
    print "Loading letters"

    l = BasicLoader("fis_letters.xml", data_dir, Letter, faculty_gwids, limit=limit)
    return l.load()


def load_testimony(data_dir, faculty_gwids, limit=None):
    print "Loading testimony"

    l = BasicLoader("fis_testimony.xml", data_dir, Testimony, faculty_gwids, limit=limit)
    return l.load()


def load_chapters(data_dir, faculty_gwids, limit=None):
    print "Loading chapters"

    l = BasicLoader("fis_chapters.xml", data_dir, Chapter, faculty_gwids, limit=limit)
    return l.load()


def load_conference_abstracts(data_dir, faculty_gwids, limit=None):
    print "Loading conference abstracts"

    l = BasicLoader("fis_conf_abstracts.xml", data_dir, ConferenceAbstract, faculty_gwids, limit=limit)
    return l.load()


def load_patents(data_dir, faculty_gwids, limit=None):
    print "Loading patents"

    l = BasicLoader("fis_patents.xml", data_dir, Patent, faculty_gwids, limit=limit)
    return l.load()


def load_grants(data_dir, faculty_gwids, limit=None):
    print "Loading grants."

    l = Loader("fis_grants.xml", data_dir, gwids=faculty_gwids, entity_class=Grant,
               field_to_entity={"awarded_by": Organization, "gw_id": Person},
               field_rename={"gw_id": "person"},
               add_entities_from_fields=["awarded_by"],
               limit=limit)
    return l.load()
