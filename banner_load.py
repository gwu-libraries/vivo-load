import os
from banner_entity import *
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

pos_code_to_classes = {
    "28101": "NonFacultyAcademic",
    "28301": "NonFacultyAcademic",
    "28302": "NonFacultyAcademic",
    "28502": "NonFacultyAcademic",
    "283R2": "NonFacultyAcademic",
    "283R1": "NonFacultyAcademic",
    "28102": "NonFacultyAcademic",
    "19S01": "NonFacultyAcademic",
    "28501": "NonFacultyAcademic",
    "27401": "NonFacultyAcademic",
    "289A1": "Postdoc",
    "289A2": "Postdoc",
    "307A1": "Librarian",
    "30601": "Librarian",
    "30602": "Librarian",
    "30402": "Librarian",
    "30401": "Librarian",
    "01001": "Librarian",
    "30501": "Librarian",
}


def get_non_faculty_gwids(data_dir, non_fac_limit=None):
    gwids = []
    with codecs.open(os.path.join(data_dir, "vivo_emplappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            if row[2] in pos_code_to_classes:
                gwids.append(row[0])
    demo_gwids = demographic_intersection(gwids, data_dir)
    if non_fac_limit and len(demo_gwids) > non_fac_limit:
        return demo_gwids[:non_fac_limit]
    else:
        return demo_gwids


def get_faculty_gwids(data_dir, fac_limit=None):
    gwids = set()
    with codecs.open(os.path.join(data_dir, "vivo_acadappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            gwids.add(row[0])
    demo_gwids = demographic_intersection(gwids, data_dir)
    if fac_limit and len(demo_gwids) > fac_limit:
        return demo_gwids[:fac_limit]
    else:
        return demo_gwids


def demographic_intersection(gwids, data_dir):
    demo_gwids = set()
    with codecs.open(os.path.join(data_dir, "vivo_demographic.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            demo_gwids.add(row[0])
    return list(demo_gwids.intersection(gwids))


def print_position_code_to_name(data_dir):
    """
    Prints map of position code to position names.
    """
    positions = {}
    with codecs.open(os.path.join(data_dir, "vivo_emplappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            pos_code = row[2]
            pos_name = row[1]
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
        reader = csv.reader(csv_file)
        p_count = 0
        for row in reader:
            gw_id = row[0]
            if gw_id in faculty_gwids or gw_id in non_faculty_gwids:
                p = Person(gw_id)
                p.first_name = row[1] if row[1] else None
                p.middle_name = row[2] if row[2] else None
                p.last_name = row[3] if row[3] else None
                p.address1 = row[4] if row[4] else None
                p.address2 = row[5] if row[5] else None
                p.address3 = row[6] if row[6] else None
                p.city = row[7] if row[7] else None
                p.state = row[8] if row[8] else None
                p.zip = row[10] if row[10] else None
                p.email = row[11] if row[11] else None
                p.phone = row[13] if row[13] else None

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
        reader = csv.reader(csv_file)
        p_count = 0
        for row in reader:
            gw_id = row[0]
            pos_cd = row[2]
            if gw_id in non_faculty_gwids and pos_cd in pos_code_to_classes:
                nf = NonFaculty(Person(gw_id), pos_code_to_classes[pos_cd])
                nf.title = row[1]
                nf.home_organization = Organization(row[3])
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
        reader = csv.reader(csv_file)
        for row in reader:
            if row[2] in pos_code_to_classes:
                org_cds.add(row[3])

    with codecs.open(os.path.join(data_dir, "vivo_orgn.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        o_count = 0
        for row in reader:
            org_cd = row[0]
            if org_cd in org_cds:
                o = Organization(row[0])
                o.name = row[1]
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
        reader = csv.reader(csv_file)
        for row in reader:
            college_cds.add(row[1])

    #Remove "No College Designated"
    college_cds.remove("00")

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #"01","Columbian Col & Grad School"
    with open(os.path.join(data_dir, "vivo_college.txt"), 'rb') as csv_file:
        reader = csv.reader(csv_file)
        o_count = 0
        for row in reader:
            college_cd = row[0]
            if college_cd in college_cds:
                o = Organization(college_cd, organization_type="College")
                o.name = row[1]
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
        reader = csv.reader(csv_file)
        for row in reader:
            department_to_college_dict[row[2]] = row[1]

    #"HKLS","Human Kinetics&Leisure Studies"
    with codecs.open(os.path.join(data_dir, "vivo_depart.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        o_count = 0
        for row in reader:
            dept_cd = row[0]
            if dept_cd not in ("0000",):
                o = Organization(dept_cd, organization_type="Department")
                o.name = row[1]
                o.part_of = Organization(department_to_college_dict.get(dept_cd))
                g += o.to_graph()
                o_count += 1
                if limit and o_count >= limit:
                    break

    return g


def load_acadappt(data_dir, limit=None, load_appt=True, fac_limit=None):
    print """
    Loading acadappt. Limit=%s.
    """ % limit

    #"G10002741","625-25","LAW","200003","Fed Criminal Appellate Clinc","4","9",
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #Get the faculty gwids
    #Yes this isn't the most efficient, but simpler.
    faculty_gwids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    with codecs.open(os.path.join(data_dir, "vivo_acadappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        for row_num, row in enumerate(reader):
            gw_id = row[0]
            if gw_id in faculty_gwids:
                f = Faculty(Person(gw_id), load_appt=load_appt)
                f.department = Organization(row[2])
                f.title = row[4]
                f.start_term = row[5]
                g += f.to_graph()

                if limit and row_num >= limit-1:
                    break

    return g


def load_courses(data_dir, limit=None, fac_limit=None):
    print """
    Loading courses. Limit=%s.
    """ % limit
    #"G10002741","625-25","LAW","200003","Fed Criminal Appellate Clinc","4","9",

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #Get the faculty gwids
    faculty_gwids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    #This file is supposed to be utf-8, but is not valid.
    with codecs.open(os.path.join(data_dir, "vivo_courses.txt"), 'r', encoding="utf-8", errors="ignore") as csv_file:
        reader = csv.reader(csv_file)
        for row_num, row in enumerate(reader):
            gw_id = row[0]
            if gw_id in faculty_gwids:
                c = Course(Person(gw_id), row[1], row[2], row[3])
                c.course_title = row[4]
                g += c.to_graph()

                if limit and row_num >= limit-1:
                    break

    return g
