import os
import xlrd
from entity import *
import argparse
from rdflib.compare import graph_diff
from sparql import load_previous_graph, sparql_load, sparql_delete, serialize

GWU = "The George Washington University"


def load_faculty(data_dir, load_vcards=True, load_facilities=True, load_departments=True, load_persons=True, limit=None):
    print """
    Loading faculty. Load vcards=%s. Load facilities=%s. Load departments=%s. Load persons=%s. Limit=%s.
    """ % (load_vcards, load_facilities, load_departments, load_persons, limit)
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    gwu = Organization(GWU, organization_type="University", is_gw=True)
    g += gwu.to_graph()

    wb = xlrd.open_workbook(os.path.join(data_dir, "faculty.xlsx"))
    ws = wb.sheet_by_name(u'faculty')
    #Skip header row
    row_num = 1
    while row_num < (limit or ws.nrows):
        #Facility
        building_name = ws.cell_value(row_num, 12)
        f = None
        if building_name and load_facilities:
            room_number = num_to_str(ws.cell_value(row_num, 11))
            f = Facility(building_name, room_number)
            g += f.to_graph()

        #Department
        #The department contained in faculty.csv shouldn't be used to create
        #association with faculty because it doesn't indicate anything about position.
        #However, it is useful for getting some organizations.
        d = None
        if load_departments:
            college_name = ws.cell_value(row_num, 4)
            if college_name and college_name != "No College Designated":
                c = Organization(college_name, organization_type="College", is_gw=True)
                c.part_of = gwu
                g += c.to_graph()
                department_name = ws.cell_value(row_num, 5)
                if department_name and department_name != "No Department":
                    d = Organization(department_name, organization_type="Department", is_gw=True)
                    d.part_of = c
                    g += d.to_graph()

        #Person
        if load_persons:
            gw_id = ws.cell_value(row_num, 0)
            p = Person(gw_id, load_vcards=load_vcards)
            p.first_name = ws.cell_value(row_num, 1)
            p.middle_name = ws.cell_value(row_num, 2)
            p.last_name = ws.cell_value(row_num, 3)
            p.username = ws.cell_value(row_num, 6)
            p.personal_statement = ws.cell_value(row_num, 9)
            p.address = ws.cell_value(row_num, 13)
            p.city = ws.cell_value(row_num, 14)
            p.state = ws.cell_value(row_num, 15)
            p.country = ws.cell_value(row_num, 16)
            p.zip = num_to_str(ws.cell_value(row_num, 17))
            p.fixed_line = ws.cell_value(row_num, 20)
            p.fax = ws.cell_value(row_num, 21)
            p.facility = f
            p.home_department = d
            g += p.to_graph()

        row_num += 1

    return g


def load_academic_appointment(data_dir, limit=None):
    print "Loading academic appointments. Limit is %s." % limit
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    wb = xlrd.open_workbook(os.path.join(data_dir, "Academic Appointment.xlsx"))
    ws = wb.sheet_by_name(u'Academic Appointment')
    #Skip header row
    row_num = 1
    while row_num < (limit or ws.nrows):
        #Person stub
        gw_id = ws.cell_value(row_num, 0)
        p = Person(gw_id)

        #Department stub
        department_name = ws.cell_value(row_num, 5)
        #Skip an appointment without a department
        if department_name:
            o = Organization(department_name)
            rank = ws.cell_value(row_num, 13)
            a = AcademicAppointment(p, o, rank)
            a.start_term = ws.cell_value(row_num, 15)
            a.end_term = ws.cell_value(row_num, 16)
            g += a.to_graph()
        row_num += 1

    return g


def load_admin_appointment(data_dir, limit=None):
    print "Loading admin appointments. Limit is %s." % limit
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #Create an entry for GWU
    gwu = Organization(GWU, organization_type="University", is_gw=True)
    g += gwu.to_graph()

    wb = xlrd.open_workbook(os.path.join(data_dir, "Admin Appointment.xlsx"))
    ws = wb.sheet_by_name(u'Admin Appointment')
    #Skip header row
    row_num = 1
    while row_num < (limit or ws.nrows):
        #Person stub
        gw_id = ws.cell_value(row_num, 0)
        p = Person(gw_id)

        #Assuming that departments and colleges already created when
        #faculty loaded
        college_name = ws.cell_value(row_num, 4)
        department_name = ws.cell_value(row_num, 5)
        #If Department name, then Department
        if department_name and department_name != "No Department":
            o = Organization(department_name)
        #Else, if College name, then College
        elif college_name:
            o = Organization(college_name)
        #Else GWU
        else:
            o = gwu

        rank = ws.cell_value(row_num, 13)
        a = AdminAppointment(p, o, rank)
        a.title = ws.cell_value(row_num, 8)
        a.start_term = ws.cell_value(row_num, 15)
        a.end_term = ws.cell_value(row_num, 16)
        g += a.to_graph()

        row_num += 1

    return g


def load_research(data_dir, limit=None, contribution_type_limit=None, research_group_codes=None, contribution_type_codes=None):
    print """
    Loading research. Limit is %s. Contribution type limit is %s. Research group codes is %s.
    Contribution types codes is %s.
    """ % (limit, contribution_type_limit, contribution_type_codes, research_group_codes)

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    wb = xlrd.open_workbook(os.path.join(data_dir, "Research.xlsx"))
    ws = wb.sheet_by_name(u'Research')
    #Skip header row
    row_num = 1
    contribution_type_count = 0
    while ((row_num < (limit or ws.nrows))
           and (contribution_type_limit is None or contribution_type_count < contribution_type_limit)):
        #Person stub
        gw_id = ws.cell_value(row_num, 0)
        p = Person(gw_id)

        title = ws.cell_value(row_num, 6)
        research_group_code = ws.cell_value(row_num, 8)
        contribution_type_code = ws.cell_value(row_num, 10)
        if ((research_group_codes is None or research_group_code in research_group_codes)
                and (contribution_type_codes is None or contribution_type_code in contribution_type_codes)):
            r = None
            if research_group_code == "LIT_BOOK":
                r = Book(title, p)
            elif (research_group_code == "LIT_PUBLICATION" and
                    contribution_type_code in (
                              #Refereed article
                              "GW_RESEARCH_TYPE_CD1",
                              #Other
                              "GW_RESEARCH_TYPE_CD8")):
                r = AcademicArticle(title, p)
            elif research_group_code == "LIT_PATENT":
                patent_status_code = ws.cell_value(row_num, 17)
                #Only accepted patents.  Submitted, pending, other, or blank are ignored.
                if patent_status_code == "GW_PATENT_STATUS_CD1":
                    r = Patent(title, p)
                    r.patent = ws.cell_value(row_num, 16)
            elif research_group_code == "LIT_GRANT":
                grant_status_code = ws.cell_value(row_num, 19)
                #Awarded or closed (not proposed or rejected)
                if grant_status_code in ("GW_GRANT_STATUS_CD3", "GW_GRANT_STATUS_CD5"):
                    grant_role_code = ws.cell_value(row_num, 21)
                    #Skip if no grant_role_code
                    if grant_role_code:
                        r = Grant(title, grant_role_code, p)
                        r.award_amount = ws.cell_value(row_num, 25)

            if r:
                r.contribution_start_year = ws.cell_value(row_num, 11)
                r.contribution_start_month = ws.cell_value(row_num, 12)
                r.additional_details = ws.cell_value(row_num, 47)
                g += r.to_graph()
                contribution_type_count += 1
        row_num += 1

    return g


def load_education(data_dir, limit=None, degree_type_codes=None, degree_type_limit=None):
    print "Loading education. Limit is %s. Degree type codes is %s. Degree type limit is %s" % (
        limit, degree_type_codes, degree_type_limit)

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    wb = xlrd.open_workbook(os.path.join(data_dir, "education.xlsx"))
    ws = wb.sheet_by_name(u'education')
    #Skip header row
    row_num = 1
    degree_type_count = 0
    while (row_num < (limit or ws.nrows)
           and (degree_type_limit is None or degree_type_count < degree_type_limit)):
        #Person stub
        gw_id = ws.cell_value(row_num, 0)
        p = Person(gw_id)

        org_name = ws.cell_value(row_num, 6)
        #Skip rows with blank organizations
        if org_name:
            o = Organization(org_name)
            g += o.to_graph()

            d = None
            degree_type_code = ws.cell_value(row_num, 7)
            degree_name = ws.cell_value(row_num, 9)
            program = ws.cell_value(row_num, 10)
            #Degree types that result in degrees
            if degree_type_code in (
                #Undergraduate
                "GW_DEGREE_TYPE_CD1",
                #Graduate
                "GW_DEGREE_TYPE_CD2",
                #Doctoral
                "GW_DEGREE_TYPE_CD3",

            ):

                d = DegreeEducation(p, o, degree_name)
                d.major = ws.cell_value(row_num, 11)
                d.program = program
            #Otherwise, non-degree education
            elif degree_type_code in (
                #Post-Doc
                "GW_DEGREE_TYPE_CD4",
                #Post-Grad
                "GW_DEGREE_TYPE_CD7",
                #Clinical
                "GW_DEGREE_TYPE_CD8"
            ):
                d = NonDegreeEducation(p, o, degree_name, program)
                d.degree = degree_name
            #Not handling GW_DEGREE_TYPE_CD5 = Other
            if d and (degree_type_codes is None or degree_type_code in degree_type_codes):
                d.start_term = ws.cell_value(row_num, 13)
                d.end_term = ws.cell_value(row_num, 14)
                g += d.to_graph()
                degree_type_count += 1

        row_num += 1
    return g


def load_courses(data_dir, limit=None):
    print "Loading courses taught. Limit is %s." % limit

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    wb = xlrd.open_workbook(os.path.join(data_dir, "Course Taught.xlsx"))
    ws = wb.sheet_by_name(u'Course_taght(Banner)')
    #Skip header row
    row_num = 1
    while row_num < (limit or ws.nrows):
        #Person stub
        gw_id = ws.cell_value(row_num, 0)
        p = Person(gw_id)

        course_id = ws.cell_value(row_num, 8)
        start_term = ws.cell_value(row_num, 10)
        c = Course(p, course_id, start_term)
        c.end_term = ws.cell_value(row_num, 11)
        g += c.to_graph()

        row_num += 1

    return g


def load_service(data_dir, limit=None, service_type_limit=None, service_group_codes=None):
    print "Loading service. Limit is %s. Service type limit is %s. Service group codes is %s." \
          % (limit, service_type_limit, service_group_codes)

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    wb = xlrd.open_workbook(os.path.join(data_dir, "Service.xlsx"))
    ws = wb.sheet_by_name(u'Service')
    #Skip header row
    row_num = 1
    service_type_count = 0
    while ((row_num < (limit or ws.nrows))
           and (service_type_limit is None or service_type_count < service_type_limit)):
        #Person stub
        gw_id = ws.cell_value(row_num, 0)
        p = Person(gw_id)

        service_group_code = ws.cell_value(row_num, 8)
        service_name = ws.cell_value(row_num, 16)
        title = ws.cell_value(row_num, 6)
        if service_group_codes is None or service_group_code in service_group_codes:
            r = None
            o = None
            position_code = ws.cell_value(row_num, 18)
            if service_group_code == "LIT_PROFESSIONAL_MEMBERSHIP":
                if service_name and position_code:
                    o = Organization(service_name)
                    g += o.to_graph()

                    r = ProfessionalMembership(p, o, position_code)
            elif service_group_code == "LIT_EDITORIAL_SERVICE":
                if service_name and position_code:
                    r = Reviewership(p, service_name, position_code)
            elif service_group_code == "LIT_AWARD":
                if title:
                    if service_name:
                        #This seems to contain numerous values that are not organizations.
                        o = Organization(service_name)
                        g += o.to_graph()
                r = Award(p, o, title)
            elif service_group_code == "LIT_PRESENTATION":
                if title and service_name:
                    r = Presentation(p, title, service_name)

            if r:
                r.contribution_start_year = ws.cell_value(row_num, 11)
                r.contribution_start_month = ws.cell_value(row_num, 12)
                r.contribution_end_year = ws.cell_value(row_num, 13)
                r.contribution_end_month = ws.cell_value(row_num, 14)
                g += r.to_graph()
                service_type_count += 1
        row_num += 1

    return g


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-load", action="store_false", dest="perform_load",
                        help="Generate RDF, but do not load into VIVO.")
    parser.add_argument("--skip-diff", action="store_false", dest="perform_diff",
                        help="Load everything, not just the difference with last load.")
    default_data_dir = "./data"
    parser.add_argument("--data-dir", default=default_data_dir, dest="data_dir",
                        help="Directory containing the xlsx. Default is %s" % default_data_dir)
    default_htdocs_dir = "/usr/local/apache2/htdocs"
    parser.add_argument("--htdocs-dir", default=default_htdocs_dir, dest="htdocs_dir",
                        help="Directory from which html documents are served. Default is %s." % default_htdocs_dir)
    default_graph_dir = "/usr/local/vivo/graphs"
    parser.add_argument("--graph-dir", default=default_graph_dir, dest="graph_dir",
                        help="Directory where graphs are archived. Default is %s." % default_graph_dir)


    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--limit", type=int, help="Number of rows from csv to load.")

    subparsers = parser.add_subparsers(dest="graph")

    faculty_parser = subparsers.add_parser("faculty", parents=[parent_parser])
    faculty_parser.add_argument("--skip-vcards", action="store_false", dest="load_vcards")
    faculty_parser.add_argument("--skip-facilities", action="store_false", dest="load_facilities")
    faculty_parser.add_argument("--skip-departments", action="store_false", dest="load_departments")
    faculty_parser.add_argument("--skip-persons", action="store_false", dest="load_persons")
    faculty_parser.set_defaults(func=load_faculty)

    academic_appointment_parser = subparsers.add_parser("academic_appointment", parents=[parent_parser])
    academic_appointment_parser.set_defaults(func=load_academic_appointment)

    admin_appointment_parser = subparsers.add_parser("admin_appointment", parents=[parent_parser])
    admin_appointment_parser.set_defaults(func=load_admin_appointment)

    research_parser = subparsers.add_parser("research", parents=[parent_parser])
    research_parser.add_argument("--contribution-type-limit", type=int, help="Number of research entities to load.")
    research_parser.add_argument("--research-groups", nargs="+", dest="research_group_codes")
    research_parser.add_argument("--contribution-types", nargs="+", dest="contribution_type_codes")
    research_parser.set_defaults(func=load_research)

    education_parser = subparsers.add_parser("education", parents=[parent_parser])
    education_parser.add_argument("--degree-type-limit", type=int, help="Number of education entities to load.")
    education_parser.add_argument("--degree-types", nargs="+", dest="degree_type_codes")
    education_parser.set_defaults(func=load_education)

    courses_parser = subparsers.add_parser("courses", parents=[parent_parser])
    courses_parser.set_defaults(func=load_courses)

    service_parser = subparsers.add_parser("service", parents=[parent_parser])
    service_parser.add_argument("--service-type-limit", type=int, help="Number of service entities to load.")
    service_parser.add_argument("--service-groups", nargs="+", dest="service_group_codes")
    service_parser.set_defaults(func=load_service)

    #Parse
    args = parser.parse_args()
    func_args = vars(args).copy()

    #Remove extraneous args
    del func_args["graph"]
    del func_args["func"]
    del func_args["perform_load"]
    del func_args["perform_diff"]
    del func_args["htdocs_dir"]
    del func_args["graph_dir"]

    #Invoke the function
    g = args.func(**func_args)

    if args.perform_diff:
        #Load the previous graph
        prev_g = load_previous_graph(args.graph_dir, args.graph)
    else:
        prev_g = Graph(namespace_manager=ns_manager)

    #Save to graphs archive directory
    serialize(g, args.graph_dir, args.graph)
    #Find the diff
    (g_both, g_del, g_add) = graph_diff(prev_g, g)
    g_add.namespace_manager = ns_manager
    g_del.namespace_manager = ns_manager

    #Print the diff
    print "To add:\n%s" % g_add.serialize(format="turtle")
    print "To delete:\n%s" % g_del.serialize(format="turtle")

    if args.perform_load:
        if len(g_add) > 0:
            sparql_load(g_add, args.htdocs_dir)
        if len(g_del) > 0:
            sparql_delete(g_del)