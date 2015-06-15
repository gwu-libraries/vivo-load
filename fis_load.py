from fis_entity import *
from utility import get_faculty_gwids, valid_college_name, valid_department_name
import os

GWU = "The George Washington University"


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

        #Get faculty ids
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

    def __init__(self, filename, data_dir, entity_class,
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
        d = Organization(result["department"], organization_type="AcademicDepartment", is_gw=True, part_of=c)
        return [c, d]


def load_departments(data_dir, limit=None):
    print "Loading departments."

    l = DepartmentLoader(data_dir, limit=limit)
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


def load_books(data_dir, limit=None, fac_limit=None):
    print "Loading books."

    l = Loader("fis_books.xml", data_dir, has_fac=True, entity_class=Book,
               field_to_entity={"gw_id": Person, "publisher": Organization},
               field_rename={"gw_id": "person"}, add_entities_from_fields=["publisher"],
               limit=limit, fac_limit=fac_limit)
    return l.load()


def load_reports(data_dir, limit=None, fac_limit=None):
    print "Loading reports."

    l = Loader("fis_reports.xml", data_dir, has_fac=True, entity_class=Book,
               field_to_entity={"gw_id": Person, "distributor": Organization},
               field_rename={"gw_id": "person"}, add_entities_from_fields=["distributor"],
               limit=limit, fac_limit=fac_limit)
    return l.load()


def load_articles(data_dir, limit=None, fac_limit=None):
    print "Loading articles"

    l = BasicLoader("fis_articles.xml", data_dir, Article, limit=limit, fac_limit=fac_limit)
    return l.load()


def load_academic_articles(data_dir, limit=None, fac_limit=None):
    print "Loading academic articles"

    l = BasicLoader("fis_acad_articles.xml", data_dir, AcademicArticle, limit=limit, fac_limit=fac_limit)
    return l.load()


def load_article_abstracts(data_dir, limit=None, fac_limit=None):
    print "Loading article abstracts"

    l = BasicLoader("fis_article_abstracts.xml", data_dir, ArticleAbstract, limit=limit, fac_limit=fac_limit)
    return l.load()


def load_reviews(data_dir, limit=None, fac_limit=None):
    print "Loading reviews"

    l = BasicLoader("fis_reviews.xml", data_dir, Review, limit=limit, fac_limit=fac_limit)
    return l.load()


def load_reference_articles(data_dir, limit=None, fac_limit=None):
    print "Loading reference articles"

    l = BasicLoader("fis_ref_articles.xml", data_dir, ReferenceArticle, limit=limit, fac_limit=fac_limit)
    return l.load()


def load_letters(data_dir, limit=None, fac_limit=None):
    print "Loading letters"

    l = BasicLoader("fis_letters.xml", data_dir, Letter, limit=limit, fac_limit=fac_limit)
    return l.load()


def load_testimony(data_dir, limit=None, fac_limit=None):
    print "Loading testimony"

    l = BasicLoader("fis_testimony.xml", data_dir, Testimony, limit=limit, fac_limit=fac_limit)
    return l.load()


def load_chapters(data_dir, limit=None, fac_limit=None):
    print "Loading chapters"

    l = BasicLoader("fis_chapters.xml", data_dir, Chapter, limit=limit, fac_limit=fac_limit)
    return l.load()


def load_conference_abstracts(data_dir, limit=None, fac_limit=None):
    print "Loading conference abstracts"

    l = BasicLoader("fis_conf_abstracts.xml", data_dir, ConferenceAbstract, limit=limit, fac_limit=fac_limit)
    return l.load()


def load_patents(data_dir, limit=None, fac_limit=None):
    print "Loading patents"

    l = BasicLoader("fis_patents.xml", data_dir, Patent, limit=limit, fac_limit=fac_limit)
    return l.load()

def load_grants(data_dir, limit=None, fac_limit=None):
    print "Loading grants."

    l = Loader("fis_grants.xml", data_dir, has_fac=True, entity_class=Grant,
               field_to_entity={"awarded_by": Organization, "gw_id": Person},
               field_rename={"gw_id": "person"},
               add_entities_from_fields=["awarded_by"],
               limit=limit, fac_limit=fac_limit)
    return l.load()
