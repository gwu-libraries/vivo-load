import os
from lyterati_entity import *
from banner_load import get_faculty_gwids

GWU = "The George Washington University"


def load_faculty(data_dir, load_departments=True, load_persons=True, limit=None, fac_limit=None):
    print """
    Loading faculty. Load departments=%s. Load persons=%s. Limit=%s.
    """ % (load_departments, load_persons, limit)

    #Get faculty ids from banner
    faculty_gw_ids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    gwu = Organization(GWU, organization_type="University", is_gw=True)
    g += gwu.to_graph()

    ws = XlWrapper(os.path.join(data_dir, "faculty.xlsx"))

    #Skip header row
    row_num = 1
    while row_num < (limit or ws.nrows):
        #Department
        #The department contained in faculty.csv shouldn't be used to create
        #association with faculty because it doesn't indicate anything about position.
        #However, it is useful for getting some organizations.
        d = None
        if load_departments:
            college_name = ws.cell_value(row_num, "College Name")
            if college_name and college_name not in ("No College Designated", "University"):
                c = Organization(college_name, organization_type="College", is_gw=True)
                c.part_of = gwu
                g += c.to_graph()
                department_name = ws.cell_value(row_num, "Department Name")
                if department_name and department_name not in ("No Department", "University-level Dept"):
                    d = Organization(department_name, organization_type="Department", is_gw=True)
                    d.part_of = c
                    g += d.to_graph()

        #Person
        if load_persons:
            gw_id = strip_gw_prefix(ws.cell_value(row_num, "Faculty ID"))
            if gw_id in faculty_gw_ids:
                p = Person(gw_id)
                p.personal_statement = ws.cell_value(row_num, "Personal Statement")
                p.home_department = d
                p.scholarly_interest = ws.cell_value(row_num, "Area of Scholary Interest")
                g += p.to_graph()

        row_num += 1

    return g


def load_academic_appointment(data_dir, limit=None, fac_limit=None):
    print "Loading academic appointments. Limit is %s." % limit

    #Get faculty ids from banner
    faculty_gw_ids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    ws = XlWrapper(os.path.join(data_dir, "Academic Appointment.xlsx"))

    #Skip header row
    row_num = 1
    while row_num < (limit or ws.nrows):
        #Person stub
        gw_id = strip_gw_prefix(ws.cell_value(row_num, "Faculty ID"))
        if gw_id in faculty_gw_ids:
            p = Person(gw_id)

            #Department stub
            department_name = ws.cell_value(row_num, "Department Name")
            #Skip an appointment without a department
            if department_name:
                o = Organization(department_name)
                rank = ws.cell_value(row_num, "Rank")
                a = AcademicAppointment(p, o, rank)
                a.start_term = ws.cell_value(row_num, "Start Term")
                a.end_term = ws.cell_value(row_num, "End Term")
                g += a.to_graph()
        row_num += 1

    return g


def load_admin_appointment(data_dir, limit=None, fac_limit=None):
    print "Loading admin appointments. Limit is %s." % limit

    #Get faculty ids from banner
    faculty_gw_ids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    #Create an entry for GWU
    gwu = Organization(GWU, organization_type="University", is_gw=True)
    g += gwu.to_graph()

    ws = XlWrapper(os.path.join(data_dir, "Admin Appointment.xlsx"))

    #Skip header row
    row_num = 1
    while row_num < (limit or ws.nrows):
        #Person stub
        gw_id = strip_gw_prefix(ws.cell_value(row_num, "Faculty ID"))
        if gw_id in faculty_gw_ids:
            p = Person(gw_id)

            #Assuming that departments and colleges already created when
            #faculty loaded
            college_name = ws.cell_value(row_num, "College Name")
            department_name = ws.cell_value(row_num, "Department Name")
            #If Department name, then Department
            if department_name and department_name not in ("No Department", "University-level Dept"):
                o = Organization(department_name)
            #Else, if College name, then College
            elif college_name and college_name not in ("No College Designated", "University"):
                o = Organization(college_name)
            #Else GWU
            else:
                o = gwu

            rank = ws.cell_value(row_num, "Rank")
            a = AdminAppointment(p, o, rank)
            a.title = ws.cell_value(row_num, "Title")
            a.start_term = ws.cell_value(row_num, "Start Term")
            a.end_term = ws.cell_value(row_num, "End Term")
            g += a.to_graph()

        row_num += 1

    return g


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


def load_education(data_dir, limit=None, degree_types=None, degree_type_limit=None, fac_limit=None):
    print "Loading education. Limit is %s. Degree types is %s. Degree type limit is %s" % (
        limit, degree_types, degree_type_limit)

    #Get faculty ids from banner
    faculty_gw_ids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    ws = XlWrapper(os.path.join(data_dir, "education.xlsx"))
    #Skip header row
    row_num = 1
    degree_type_count = 0
    while (row_num < (limit or ws.nrows)
           and (degree_type_limit is None or degree_type_count < degree_type_limit)):
        #Person stub
        gw_id = strip_gw_prefix(ws.cell_value(row_num, "Faculty ID"))
        if gw_id in faculty_gw_ids:
            p = Person(gw_id)

            org_name = ws.cell_value(row_num, "Institution")
            #Skip rows with blank organizations
            if org_name:
                o = Organization(org_name)
                g += o.to_graph()

                d = None
                #Degree Type CD disappeared from spreadsheet so using Degree Type.
                degree_type = ws.cell_value(row_num, "Degree Type")
                degree_name = ws.cell_value(row_num, "Degree")
                program = ws.cell_value(row_num, "Prgram")
                #Degree types that result in degrees
                if degree_type in (
                    "Undergraduate",
                    "Graduate",
                    "Doctoral"
                ):

                    d = DegreeEducation(p, o, degree_name)
                    d.major = ws.cell_value(row_num, "Major")
                    d.program = program
                #Otherwise, non-degree education
                elif degree_type in (
                    "Post Doctoral",
                    "Post Graduate",
                    "Clinical"
                ):
                    d = NonDegreeEducation(p, o, degree_name, program)
                    d.degree = degree_name
                #Not handling GW_DEGREE_TYPE_CD5 = Other
                if d and (degree_types is None or degree_type in degree_types):
                    d.start_term = ws.cell_value(row_num, "Start Term")
                    d.end_term = ws.cell_value(row_num, "End Term")
                    g += d.to_graph()
                    degree_type_count += 1

        row_num += 1
    return g


def load_courses(data_dir, limit=None, fac_limit=None):
    print "Loading courses taught. Limit is %s." % limit

    #Get faculty ids from banner
    faculty_gw_ids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    ws = XlWrapper(os.path.join(data_dir, "Course Taught.xlsx"))
    #Skip header row
    row_num = 1
    while row_num < (limit or ws.nrows):
        created_by = ws.cell_value(row_num, "Created By")
        #Skip everything not created by Interface.
        #If not created by Interface, then manually entered.
        if created_by == "Interface":
            #Person stub
            gw_id = strip_gw_prefix(ws.cell_value(row_num, "Faculty ID"))
            if gw_id in faculty_gw_ids:
                p = Person(gw_id)

                course_id = ws.cell_value(row_num, "Course ID")
                subject_id = ws.cell_value(row_num, "Subject ID")
                start_term = ws.cell_value(row_num, "Start Term")
                c = Course(p, course_id, subject_id, start_term)
                c.course_title = ws.cell_value(row_num, "Course Title")
                g += c.to_graph()

        row_num += 1

    return g


def load_service(data_dir, limit=None, service_type_limit=None, service_group_codes=None, fac_limit=None):
    print "Loading service. Limit is %s. Service type limit is %s. Service group codes is %s." \
          % (limit, service_type_limit, service_group_codes)

    #Get faculty ids from banner
    faculty_gw_ids = get_faculty_gwids(data_dir, fac_limit=fac_limit)

    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    ws = XlWrapper(os.path.join(data_dir, "Service.xlsx"))
    #Skip header row
    row_num = 1
    service_type_count = 0
    while ((row_num < (limit or ws.nrows))
           and (service_type_limit is None or service_type_count < service_type_limit)):
        #Person stub
        gw_id = strip_gw_prefix(ws.cell_value(row_num, "Faculty ID"))
        if gw_id in faculty_gw_ids:
            p = Person(gw_id)

            service_group_code = ws.cell_value(row_num, "Service Group CD(Headings)")
            service_name = ws.cell_value(row_num, "Serviec Name")
            title = ws.cell_value(row_num, "Title")
            if service_group_codes is None or service_group_code in service_group_codes:
                r = None
                o = None
                position = ws.cell_value(row_num, "Position")
                if service_group_code == "LIT_PROFESSIONAL_MEMBERSHIP":
                    if service_name and position:
                        o = Organization(service_name)
                        g += o.to_graph()

                        r = ProfessionalMembership(p, o, position)
                elif service_group_code == "LIT_EDITORIAL_SERVICE":
                    if service_name and position:
                        r = Reviewership(p, service_name, position)
                elif service_group_code == "LIT_AWARD":
                    if title:
                        if service_name:
                            #There seems to contain numerous values that are not organizations.
                            o = Organization(service_name)
                            g += o.to_graph()
                    r = Award(p, o, title)
                elif service_group_code == "LIT_PRESENTATION":
                    if title and service_name:
                        r = Presentation(p, title, service_name)

                if r:
                    r.contribution_start_year = ws.cell_value(row_num, "Contribution Start Year")
                    r.contribution_start_month = ws.cell_value(row_num, "Contribution Start Month")
                    r.contribution_end_year = ws.cell_value(row_num, "Contribution End Year")
                    r.contribution_end_month = ws.cell_value(row_num, "Contribution End Month")
                    g += r.to_graph()
                    service_type_count += 1
        row_num += 1

    return g
