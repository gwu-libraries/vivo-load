from banner_entity import *
from utility import *
import unicodecsv as csv


def print_position_code_to_name(data_dir):
    """
    Prints map of position code to position names.
    """
    positions = {}
    with open(os.path.join(data_dir, "vivo_emplappt.txt"), 'rb') as csv_file:
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


def load_demographic(data_dir, non_faculty_gwids, faculty_gwids, limit=None):
    print """
    Loading demographic. Limit=%s.
    """ % limit
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    with open(os.path.join(data_dir, "vivo_demographic.txt"), 'rb') as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        p_count = 0
        row_count = 0
        for row_count, row in enumerate(reader):
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

        if not row_count:
            warning_log.error("vivo_demographic.txt has no data.")
            return None

    return g


def load_emplappt(data_dir, non_faculty_gwids, limit=None):
    #"G17437285","Uv Rsh Assoc Ft","28501","152401"
    print """
    Loading emplappt. Limit=%s.
    """ % limit
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)
    try:
        with open(os.path.join(data_dir, "vivo_emplappt.txt"), 'rb') as csv_file:
            reader = csv.DictReader(csv_file, dialect="banner")
            row_count = 0
            p_count = 0
            for row_count, row in enumerate(reader, start=1):
                gw_id = row["EMPLOYEEID"]
                pos_cd = row["POSITION_CLASS"]
                if gw_id in non_faculty_gwids:
                    nf = NonFaculty(Person(gw_id), pos_code_to_classes.get(pos_cd, "NonFacultyAcademic"))
                    nf.title = row["JOB_TITLE"]
                    nf.home_organization = Organization(row["HOME_ORG_CODE"])
                    g += nf.to_graph()

                    p_count += 1
                    if limit and p_count >= limit:
                        break

            if not row_count:
                warning_log.error("vivo_emplappt.txt has no data.")
                return None

        return g
        #If there is an IOError, log it and return None
    except IOError, e:
        warning_log.error("%s: %s", e.strerror, e.filename)
        return None


def load_orgn(data_dir, non_faculty_gwids, limit=None):
    #"001101","BOARD OF TRUSTEES"
    print """
    Loading orgn. Limit=%s.
    """ % limit
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    try:
        #Only load organizations that have entries in emplappt
        org_cds = set()
        with open(os.path.join(data_dir, "vivo_emplappt.txt"), 'rb') as csv_file:
            reader = csv.DictReader(csv_file, dialect="banner")
            row_count = 0
            for row_count, row in enumerate(reader, start=1):
                if row["EMPLOYEEID"] in non_faculty_gwids:
                    org_cds.add(row["HOME_ORG_CODE"])
            if not row_count:
                warning_log.error("vivo_emplappt.txt has no data, so not loading organization.")
                return None

        with open(os.path.join(data_dir, "vivo_orgn.txt"), 'rb') as csv_file:
            reader = csv.DictReader(csv_file, dialect="banner")
            row_count = 0
            o_count = 0
            for row_count, row in enumerate(reader, start=1):
                org_cd = row["ORG_CODE"]
                if org_cd in org_cds:
                    o = Organization(org_cd, organization_type="Department")
                    o.name = row["ORG_TITLE"]
                    g += o.to_graph()

                    o_count += 1
                    if limit and o_count >= limit:
                        break
            if not row_count:
                warning_log.error("vivo_orgn.txt has no data.")
                return None

        return g
    #If there is an IOError, log it and return None
    except IOError, e:
        warning_log.error("%s: %s", e.strerror, e.filename)
        return None


def load_college(data_dir, limit=None):
    print """
    Loading college. Limit=%s.
    """ % limit

    try:
        college_cds = set()
        #Only load colleges that have entries in acadappt
        with open(os.path.join(data_dir, "vivo_acadappt.txt"), 'rb') as csv_file:
            row_count = 0
            reader = csv.DictReader(csv_file, dialect="banner")
            for row_count, row in enumerate(reader, start=1):
                college_cds.add(row["COLLEGE"])
            if not row_count:
                warning_log.error("vivo_acadappt.txt has no data, so not loading college.")
                return None

        #Remove "No College Designated"
        college_cds.remove("00")

        #Create an RDFLib Graph
        g = Graph(namespace_manager=ns_manager)

        #"01","Columbian Col & Grad School"
        with open(os.path.join(data_dir, "vivo_college.txt"), 'rb') as csv_file:
            reader = csv.DictReader(csv_file, dialect="banner")
            row_count = 0
            o_count = 0
            for row_count, row in enumerate(reader, start=1):
                college_cd = row["COLLEGE_CD"]
                if college_cd in college_cds:
                    o = Organization(college_cd, organization_type="College")
                    o.name = row["COLLEGE"]
                    g += o.to_graph()
                    o_count += 1
                    if limit and o_count >= limit:
                        break
            if not row_count:
                warning_log.error("vivo_college.txt has no data.")
                return None

        return g
    #If there is an IOError, log it and return None
    except IOError, e:
        warning_log.error("%s: %s", e.strerror, e.filename)
        return None


def load_depart(data_dir, limit=None):
    print """
    Loading department. Limit=%s.
    """ % limit

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    try:
        #Read acadappt to get map of department to college
        department_to_college_dict = {}
        with open(os.path.join(data_dir, "vivo_acadappt.txt"), 'rb') as csv_file:
            row_count = 0
            reader = csv.DictReader(csv_file, dialect="banner")
            for row_count, row in enumerate(reader, start=1):
                department_to_college_dict[row["DEPARTMENT"]] = row["COLLEGE"]

            if not row_count:
                warning_log.error("vivo_acadappt.txt has no data, so not loading department.")
                return None

        #"HKLS","Human Kinetics&Leisure Studies"
        with open(os.path.join(data_dir, "vivo_depart.txt"), 'rb') as csv_file:
            reader = csv.DictReader(csv_file, dialect="banner")
            o_count = 0
            row_count = 0
            for row_count, row in enumerate(reader, start=1):
                dept_cd = row["DEPARTMENT_CD"]
                if dept_cd not in ("0000",):
                    o = Organization(dept_cd, organization_type="Department")
                    o.name = row["DEPARTMENT"]
                    o.part_of = Organization(department_to_college_dict.get(dept_cd))
                    g += o.to_graph()
                    o_count += 1
                    if limit and o_count >= limit:
                        break
            if not row_count:
                warning_log.error("vivo_depart.txt has no data.")
                return None

        return g
    #If there is an IOError, log it and return None
    except IOError, e:
        warning_log.error("%s: %s", e.strerror, e.filename)
        return None


def load_acadappt(data_dir, faculty_gwids, limit=None, load_appt=True):
    print """
    Loading acadappt. Limit=%s. Load appt=%s.
    """ % (limit, load_appt)

    #"G10002741","625-25","LAW","200003","Fed Criminal Appellate Clinc","4","9",
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    try:
        with open(os.path.join(data_dir, "vivo_acadappt.txt"), 'rb') as csv_file:
            reader = csv.DictReader(csv_file, dialect="banner")
            row_count = 0
            for row_count, row in enumerate(reader):
                gw_id = row["EMPLOYEEID"]
                if gw_id in faculty_gwids:
                    f = Faculty(Person(gw_id), load_appt=load_appt)
                    f.department = Organization(row["DEPARTMENT"])
                    f.title = row["POSITION_TITLE"]
                    f.start_term = row["START_TERM_CODE"]
                    g += f.to_graph()

                    if limit and row_count > limit-1:
                        break
            if not row_count:
                warning_log.error("vivo_acadappt.txt has no data.")
                return None

        return g
    #If there is an IOError, log it and return None
    except IOError, e:
        warning_log.error("%s: %s", e.strerror, e.filename)
        return None


def load_courses(data_dir, non_faculty_gwids, faculty_gwids, limit=None):
    print """
    Loading courses. Limit=%s.
    """ % limit
    #"G10002741","625-25","LAW","200003","Fed Criminal Appellate Clinc","4","9",

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    try:
        #This file is supposed to be utf-8, but is not valid.
        with open(os.path.join(data_dir, "vivo_courses.txt"), 'rb') as csv_file:
            reader = csv.DictReader(csv_file, dialect="banner")
            row_count = 0
            for row_count, row in enumerate(reader, start=1):
                gw_id = row["EMPLOYEEID"]
                if gw_id in faculty_gwids or gw_id in non_faculty_gwids:
                    c = Course(Person(gw_id), row["COURSE_NBR"], row["SUBJECT"], row["COURSE_TITLE"])
                    g += c.to_graph()

                    if limit and row_count > limit-1:
                        break
            if not row_count:
                warning_log.error("vivo_courses.txt has no data.")
                return None

        return g
    #If there is an IOError, log it and return None
    except IOError, e:
        warning_log.error("%s: %s", e.strerror, e.filename)
        return None
