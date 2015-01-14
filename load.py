from SPARQLWrapper import SPARQLWrapper
import socket
import codecs
import os
import time
import xlrd
from entity import *
import argparse


def serialize(graph, htdocs_dir):
    filename = time.strftime("load-%Y%m%d%H%M%S.ttl")
    print "Serializing to %s" % filename
    with codecs.open(os.path.join(htdocs_dir, filename), "w") as out:
        graph.serialize(format="turtle", destination=out)
    return filename


def sparql_load(filename):
    print "Loading %s" % filename
    ip = socket.gethostbyname(socket.gethostname())
    sparql = SPARQLWrapper("http://tomcat:8080/vivo/api/sparqlUpdate")
    sparql.addParameter("email", "vivo_root@gwu.edu")
    sparql.addParameter("password", "password")
    sparql.setQuery("""
        LOAD <http://%s/%s> into graph <http://vitro.mannlib.cornell.edu/default/vitro-kb-2>
    """ % (ip, filename))
    sparql.setMethod("POST")
    sparql.query()


def load_faculty(data_dir, load_vcards=True, load_facilities=True, load_departments=True, limit=None):
    print "Loading faculty. Load vcards=%s. Load facilities=%s. Load departments=%s. Limit=%s." \
          % (load_vcards, load_facilities, load_departments, limit)
    #Create an RDFLib Graph
    g = Graph()
    #Namespace bindings
    g.bind('vivo', VIVO)
    g.bind('vcard', VCARD)
    g.bind('obo', OBO)

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

        #Person
        gw_id = ws.cell_value(row_num, 0)
        p = Person(gw_id, load_vcards=load_vcards)
        p.first_name = ws.cell_value(row_num, 1)
        p.middle_name = ws.cell_value(row_num, 2)
        p.last_name = ws.cell_value(row_num, 3)
        p.personal_statement = ws.cell_value(row_num, 9)
        p.address = ws.cell_value(row_num, 13)
        p.city = ws.cell_value(row_num, 14)
        p.state = ws.cell_value(row_num, 15)
        p.country = ws.cell_value(row_num, 16)
        p.zip = num_to_str(ws.cell_value(row_num, 17))
        p.email = ws.cell_value(row_num, 18)
        p.fixed_line = ws.cell_value(row_num, 20)
        p.fax = ws.cell_value(row_num, 21)
        p.facility = f
        g += p.to_graph()

        #Department
        #The department contained in faculty.csv shouldn't be used to create
        #association with faculty because it doesn't indicate anything about position.
        #However, it is useful for getting some organizations.
        if load_departments:
            department_name = ws.cell_value(row_num, 5)
            d = Department(department_name)
            d.college_name = ws.cell_value(row_num, 4)
            g += d.to_graph()

        row_num += 1

    return g


def load_academic_appointment(data_dir, limit=None):
    print "Loading academic appointments. Limit is %s." % limit
    #Create an RDFLib Graph
    g = Graph()
    #Namespace bindings
    g.bind('vivo', VIVO)
    g.bind('obo', OBO)

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
            d = Department(department_name)
            rank = ws.cell_value(row_num, 13)
            a = AcademicAppointment(d, p, rank)
            a.start_term = ws.cell_value(row_num, 15)
            a.end_term = ws.cell_value(row_num, 16)
            g += a.to_graph()
        row_num += 1

    return g


def load_research(data_dir, limit=None, contribution_type_limit=None, research_group_codes=None, contribution_type_codes=None):
    print "Loading research. Limit is %s. Contribution type limit is %s. Research group codes is %s. Contribution types codes is %s." \
          % (limit, contribution_type_limit, contribution_type_codes, research_group_codes)

    #Create an RDFLib Graph
    g = Graph()
    #Namespace bindings
    g.bind('vivo', VIVO)
    g.bind('obo', OBO)

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
            if (research_group_code == "LIT_BOOK"
                or (research_group_code == "LIT_PUBLICATION" and
                    #Refereed article
                    contribution_type_code == "GW_RESEARCH_TYPE_CD1")):
                r = Document(title, research_group_code, contribution_type_code, p)
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


def load_education(data_dir, limit=None):
    print "Loading education. Limit is %s." % limit

    #Create an RDFLib Graph
    g = Graph()
    #Namespace bindings
    g.bind('vivo', VIVO)
    g.bind('obo', OBO)
    g.bind('foaf', FOAF)

    wb = xlrd.open_workbook(os.path.join(data_dir, "education.xlsx"))
    ws = wb.sheet_by_name(u'education')
    #Skip header row
    row_num = 1
    while row_num < (limit or ws.nrows):
        #Person stub
        gw_id = ws.cell_value(row_num, 0)
        p = Person(gw_id)

        org_name = ws.cell_value(row_num, 6)
        #Skip rows with blank organizations
        if org_name:
            o = Organization(org_name)
            g += o.to_graph()

            degree_type_code = ws.cell_value(row_num, 7)
            #Degree types that result in degrees
            if degree_type_code in (
                #Undergraduate
                "GW_DEGREE_TYPE_CD1",
                #Graduate
                "GW_DEGREE_TYPE_CD2",
                #Doctoral
                "GW_DEGREE_TYPE_CD3",

            ):
                degree_name = ws.cell_value(row_num, 9)

                d = Degree(p, o, degree_name)
                d.program = ws.cell_value(row_num, 10)
                d.major = ws.cell_value(row_num, 11)
                d.start_term = ws.cell_value(row_num, 13)
                d.end_term = ws.cell_value(row_num, 14)
                g += d.to_graph()
            #Otherwise, non-degree education, e.g.,
            #GW_DEGREE_TYPE_CD4 = Post-Doc
            #GW_DEGREE_TYPE_CD5 = Other
            #GW_DEGREE_TYPE_CD7 = Post-Grad
            #GW_DEGREE_TYPE_CD8 = Clinical

        row_num += 1
    return g


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-load", action="store_false", dest="perform_load",
                        help="Generate RDF, but do not load into VIVO.")
    default_data_dir = "./data"
    parser.add_argument("--data-dir", default=default_data_dir, dest="data_dir",
                        help="Directory containing the xlsx. Default is %s" % default_data_dir)
    default_htdocs_dir = "/usr/local/apache2/htdocs"
    parser.add_argument("--htdocs-dir", default=default_htdocs_dir, dest="htdocs_dir",
                        help="Directory from which html documents are served. Default is %s." % default_htdocs_dir)

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--limit", type=int, help="Number of rows from csv to load.")

    subparsers = parser.add_subparsers(dest="graph")

    faculty_parser = subparsers.add_parser("faculty", parents=[parent_parser])
    faculty_parser.add_argument("--skip-vcards", action="store_false", dest="load_vcards")
    faculty_parser.add_argument("--skip-facilities", action="store_false", dest="load_facilities")
    faculty_parser.add_argument("--skip-departments", action="store_false", dest="load_departments")
    faculty_parser.set_defaults(func=load_faculty)

    academic_appointment_parser = subparsers.add_parser("academic_appointment", parents=[parent_parser])
    academic_appointment_parser.set_defaults(func=load_academic_appointment)

    research_parser = subparsers.add_parser("research", parents=[parent_parser])
    research_parser.add_argument("--contribution-type-limit", type=int, help="Number of research entities load.")
    research_parser.add_argument("--research-groups", nargs="+", dest="research_group_codes")
    research_parser.add_argument("--contribution-types", nargs="+", dest="contribution_type_codes")
    research_parser.set_defaults(func=load_research)

    education_parser = subparsers.add_parser("education", parents=[parent_parser])
    education_parser.set_defaults(func=load_education)

    #Parse
    args = parser.parse_args()
    func_args = vars(args).copy()
    #Remove extraneous args
    del func_args["graph"]
    del func_args["func"]
    del func_args["perform_load"]
    del func_args["htdocs_dir"]

    #Invoke the function
    g = args.func(**func_args)
    print g.serialize(format="turtle")
    if args.perform_load:
        load_filename = serialize(g, args.htdocs_dir)
        sparql_load(load_filename)
