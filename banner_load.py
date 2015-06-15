from banner_entity import *
from utility import *
import csv
import codecs

# #Non-faculty academic
# 28101 --> ['Uv Sr Rsch Scientist FT', 'Senior Research Scientist', 'Senior Research Scientist FT', 'Mc Sr Rsch Scientist FT', 'Sr Rsch Scientist', 'Uv Sr Rsch Scientist Ft', ' Senior Research Scientist']
# 28301 --> ['Uv Rsch Scientist FT', 'Mc Rsch Scientist FT', 'Research Scientist', 'Uv Research Scientist Ft', 'Mc Rsh Scient Ft', 'Uv Rsh Scient Ft', 'Mc Research Scientist Ft', 'Sr. Research Scientist']
# 28302 --> ['Mc Rsch Scientist PT', 'Research Scientist', 'Uv Rsch Scientist PT']
# 28502 --> ['Uv Rsch Assoc PT', 'Research Associate PT', 'Uv Rsch Assoc', 'Research Associate', 'Uv Rsh Assoc Pt', 'Mc Rsch Assoc PT', 'Postdoctoral Scientist']
# 283R2 --> ['Mc Lead Research Scientist Pt', 'Uv Lead Research Scientist PT', 'Uv Lead Research Scientist FT']
# 283R1 --> ['Lead Research Scientist', 'Deputy Director CHCQ', ' Lead Research Scientist', 'Uv Lead Research Scientist FT', 'Sr Research Network Engineer', 'Mc Lead Research Scientist Ft']
# 28102 --> ['Mc Sr Rsch Scientist FT', 'Sr. Research Scientist']
# 19S01 --> ['Research Project Director', 'Programs&Development Director', 'Director of Research']
# 28501 --> ['Uv Rsh Assoc Ft', 'Uv Rsch Assoc FT', 'Policy Associate', 'Research Asso. Study Coodntr', 'Research Associate', 'Bioinformatics Analyst', 'Mc Rsch Assoc FT', 'Rsch Assoc', 'Mc Rsh Assoc Ft', 'Uv Rsch Assoc FT/SAS Pgrmr']
# 27401 --> ['Uv Rsch Dir Non-Fa Ft']
#
# #Postdoc
# 289A1 --> ['Uv Post-Doctoral Scientist Ft', ' Post-Doctoral Scientist', 'Post-Doctoral Scientist', 'Post Doctoral Scientist', 'Research Scientist', 'Mc Post-Doctoral Scientist Ft', 'Uv Post-Doctoral Scientist PT']
# 289A2 --> ['Uv Post-Doctoral Scientist Pt']
#
# #Librarian
# 307A1 --> ['Uv Librarian 4 FT', 'Uv Lib 4 Ft']
# 30601 --> ['Lib 1', 'Uv Librarian 1 FT', 'Uv Librarian II FT', 'Mc Lib 1 Ft']
# 30602 --> ['Uv Lib 1 Ft', 'Systems Librarian']
# 30402 --> ['Uv Lib 3 Pt', 'Uv Librarian 3 PT', 'Uv Librarian IV FT']
# 30401 --> ['Uv Lib 3 Ft', 'Mc Lib 3 Ft', 'Uv Librarian 4FT', 'Uv Lib 4 Ft', 'Uv Lib 2 Ft', 'Uv Librarian 3 FT']
# 01001 --> ['UV Librarian & Vice Provost']
# 30501 --> ['Uv Lib 3 Ft', 'Uv Librarian 2 FT', 'Uv Librarian 3 FT', 'Mc Lib 2 Ft', 'Uv Lib 2 Ft', 'Uv Lib  Ft', 'Systems Librarian', 'Uv Lib 4 Ft', 'Librarian 2']


def print_position_code_to_name(data_dir):
    """
    Prints map of position code to position names.
    """
    positions = {}
    with codecs.open(os.path.join(data_dir, "vivo_emplappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        for row in reader:
            pos_code = row["POSITION_CLASS"]
            pos_name = row["JOB_TITLE"]
            if not pos_code in positions:
                positions[pos_code] = []
            if not pos_name in positions[pos_code]:
                positions[pos_code].append(pos_name)
    for pos_code in positions:
        print "%s --> %s" % (pos_code, positions[pos_code])


def load_demographic(data_dir, limit=None, fac_limit=None, non_fac_limit=None):
    #"G37176643","Sabina","M","Alkire","Institute for International Economic Policy","1900 F Street NW",,"Washington","DC",,"20052","sabina_alkire@gwu.edu","sabina_alkire","202-994-5320"
    print """
    Loading demographic. Limit=%s.
    """ % limit
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #Get the non-faculty and faculty gwids
    non_faculty_gwids = get_non_faculty_gwids(data_dir, non_fac_limit=non_fac_limit)
    faculty_gwids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    with codecs.open(os.path.join(data_dir, "vivo_demographic.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        p_count = 0
        for row in reader:
            gw_id = row["EMPLOYEEID"]
            if gw_id in faculty_gwids or gw_id in non_faculty_gwids:
                p = Person(gw_id)
                p.first_name = row["FIRST_NAME"] if row["FIRST_NAME"] else None
                p.middle_name = row["MIDDLE_NAME"] if row["MIDDLE_NAME"] else None
                p.last_name = row["LAST_NAME"] if row["LAST_NAME"] else None
                p.address1 = row["ADDRESS_LINE1"] if row["ADDRESS_LINE1"] else None
                p.address2 = row["ADDRESS_LINE2"] if row["ADDRESS_LINE2"] else None
                p.address3 = row["ADDRESS_LINE3"] if row["ADDRESS_LINE3"] else None
                p.city = row["CITY"] if row["CITY"] else None
                p.state = row["STATE"] if row["STATE"] else None
                p.zip = row["ZIP"] if row["ZIP"] else None
                p.email = row["EMAIL"] if row["EMAIL"] else None
                p.phone = row["PHONE"] if row["PHONE"] else None

                g += p.to_graph()

                p_count += 1
                if limit and p_count >= limit:
                    break

    return g


def load_emplappt(data_dir, limit=None, non_fac_limit=None):
    #"G17437285","Uv Rsh Assoc Ft","28501","152401"
    print """
    Loading emplappt. Limit=%s.
    """ % limit
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #Get the non-faculty gwids
    #Yes this isn't the most efficient, but simpler.
    non_faculty_gwids = get_non_faculty_gwids(data_dir, non_fac_limit=non_fac_limit)

    with codecs.open(os.path.join(data_dir, "vivo_emplappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        p_count = 0
        for row in reader:
            gw_id = row["EMPLOYEEID"]
            pos_cd = row["POSITION_CLASS"]
            if gw_id in non_faculty_gwids and pos_cd in pos_code_to_classes:
                nf = NonFaculty(Person(gw_id), pos_code_to_classes[pos_cd])
                nf.title = row["JOB_TITLE"]
                nf.home_organization = Organization(row["HOME_ORG_CODE"])
                g += nf.to_graph()

                p_count += 1
                if limit and p_count >= limit:
                    break

    return g


def load_orgn(data_dir, limit=None):
    #"001101","BOARD OF TRUSTEES"
    print """
    Loading orgn. Limit=%s.
    """ % limit
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #Only load organizations that have entries in emplappt
    org_cds = set()
    with codecs.open(os.path.join(data_dir, "vivo_emplappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        for row in reader:
            if row["POSITION_CLASS"] in pos_code_to_classes:
                org_cds.add(row["HOME_ORG_CODE"])

    with codecs.open(os.path.join(data_dir, "vivo_orgn.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        o_count = 0
        for row in reader:
            org_cd = row["ORG_CODE"]
            if org_cd in org_cds:
                o = Organization(org_cd, organization_type="Department")
                o.name = row["ORG_TITLE"]
                g += o.to_graph()

                o_count += 1
                if limit and o_count >= limit:
                    break
    return g


def load_college(data_dir, limit=None):
    print """
    Loading college. Limit=%s.
    """ % limit

    college_cds = set()
    #Only load colleges that have entries in acadappt
    with codecs.open(os.path.join(data_dir, "vivo_acadappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        for row in reader:
            college_cds.add(row["COLLEGE"])

    #Remove "No College Designated"
    college_cds.remove("00")

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #"01","Columbian Col & Grad School"
    with open(os.path.join(data_dir, "vivo_college.txt"), 'rb') as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        o_count = 0
        for row in reader:
            college_cd = row["COLLEGE_CD"]
            if college_cd in college_cds:
                o = Organization(college_cd, organization_type="College")
                o.name = row["COLLEGE"]
                g += o.to_graph()
                o_count += 1
                if limit and o_count >= limit:
                    break

    return g


def load_depart(data_dir, limit=None):
    print """
    Loading department. Limit=%s.
    """ % limit

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #Read acadappt to get map of department to college
    department_to_college_dict = {}
    with codecs.open(os.path.join(data_dir, "vivo_acadappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        for row in reader:
            department_to_college_dict[row["DEPARTMENT"]] = row["COLLEGE"]

    #"HKLS","Human Kinetics&Leisure Studies"
    with codecs.open(os.path.join(data_dir, "vivo_depart.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        o_count = 0
        for row in reader:
            dept_cd = row["DEPARTMENT_CD"]
            if dept_cd not in ("0000",):
                o = Organization(dept_cd, organization_type="Department")
                o.name = row["DEPARTMENT"]
                o.part_of = Organization(department_to_college_dict.get(dept_cd))
                g += o.to_graph()
                o_count += 1
                if limit and o_count >= limit:
                    break

    return g


def load_acadappt(data_dir, limit=None, load_appt=True, fac_limit=None):
    print """
    Loading acadappt. Limit=%s. Load appt=%s.
    """ % (limit, load_appt)

    #"G10002741","625-25","LAW","200003","Fed Criminal Appellate Clinc","4","9",
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #Get the faculty gwids
    #Yes this isn't the most efficient, but simpler.
    faculty_gwids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    with codecs.open(os.path.join(data_dir, "vivo_acadappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        for row_num, row in enumerate(reader):
            gw_id = row["EMPLOYEEID"]
            if gw_id in faculty_gwids:
                f = Faculty(Person(gw_id), load_appt=load_appt)
                f.department = Organization(row["DEPARTMENT"])
                f.title = row["POSITION_TITLE"]
                f.start_term = row["START_TERM_CODE"]
                g += f.to_graph()

                if limit and row_num >= limit-1:
                    break

    return g


def load_courses(data_dir, limit=None, fac_limit=None, non_fac_limit=None):
    print """
    Loading courses. Limit=%s.
    """ % limit
    #"G10002741","625-25","LAW","200003","Fed Criminal Appellate Clinc","4","9",

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #Get the non-faculty and faculty gwids
    non_faculty_gwids = get_non_faculty_gwids(data_dir, non_fac_limit=non_fac_limit)
    faculty_gwids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    #This file is supposed to be utf-8, but is not valid.
    with codecs.open(os.path.join(data_dir, "vivo_courses.txt"), 'r', encoding="utf-8", errors="ignore") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        for row_num, row in enumerate(reader):
            gw_id = row["EMPLOYEEID"]
            if gw_id in faculty_gwids or gw_id in non_faculty_gwids:
                c = Course(Person(gw_id), row["COURSE_NBR"], row["SUBJECT"], row["COURSE_TITLE"])
                g += c.to_graph()

                if limit and row_num >= limit-1:
                    break

    return g
