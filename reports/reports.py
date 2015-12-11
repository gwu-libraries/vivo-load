import sys
import os
sys.path.append(os.path.abspath('..'))
from loader.utility import xml_result_generator, valid_department_name, valid_college_name
import codecs
import csv
import argparse
from collections import Counter

def fis_appointments_with_invalid_college_or_department(data_dir):
    valid_gwids = set()
    invalid_gwids = set()
    for result in xml_result_generator(os.path.join(data_dir, "fis_academic_appointment.xml")):
        if valid_department_name(result["department"]) or valid_college_name(result["college"]):
            valid_gwids.add(result["gw_id"])
            if result["gw_id"] in invalid_gwids:
                invalid_gwids.remove(result["gw_id"])
        elif result["gw_id"] not in valid_gwids:
            invalid_gwids.add(result["gw_id"])
    for result in xml_result_generator(os.path.join(data_dir, "fis_admin_appointment.xml")):
        if valid_department_name(result["department"]) or valid_college_name(result["college"]):
            valid_gwids.add(result["gw_id"])
            if result["gw_id"] in invalid_gwids:
                invalid_gwids.remove(result["gw_id"])
        elif result["gw_id"] not in valid_gwids:
            invalid_gwids.add(result["gw_id"])
    return invalid_gwids


def fis_faculty_with_no_appointments(data_dir):
    fis_faculty_gwids = load_fis_faculty(data_dir)
    fis_appointment_gwids = load_fis_appointments(data_dir)
    return fis_faculty_gwids - fis_appointment_gwids


def fis_faculty_with_no_appointments_and_in_banner(data_dir):
    fis_faculty_gwids = load_fis_faculty(data_dir)
    fis_appointment_gwids = load_fis_appointments(data_dir)
    banner_gwids = load_banner_demographic(data_dir)

    return (fis_faculty_gwids - fis_appointment_gwids).intersection(banner_gwids)


def fis_faculty_not_in_banner(data_dir):
    fis_gwids = load_fis_faculty(data_dir)
    banner_gwids = load_banner_demographic(data_dir)

    return fis_gwids - banner_gwids


def fis_faculty_in_banner(data_dir):
    fis_gwids = load_fis_faculty(data_dir)
    banner_gwids = load_banner_demographic(data_dir)

    return fis_gwids.intersection(banner_gwids)


def fis_appointments_not_in_banner_demographic(data_dir):
    fis_gwids = load_fis_appointments(data_dir)
    banner_gwids = load_banner_demographic(data_dir)
    return fis_gwids - banner_gwids


def fis_appointments_not_in_banner_appointments_in_banner_demographics(data_dir):
    fis_gwids = load_fis_appointments(data_dir)
    banner_demographic_gwids = load_banner_demographic(data_dir)
    banner_appointment_gwids = load_banner_appointment(data_dir)
    return fis_gwids.intersection(banner_demographic_gwids) - banner_appointment_gwids


def fis_faculty_and_banner_demographics_intersection(data_dir):
    fis_gwids = load_fis_faculty(data_dir)
    banner_demographic_gwids = load_banner_demographic(data_dir)
    return fis_gwids.intersection(banner_demographic_gwids)


def fis_faculty_and_banner_demographics_intersection_not_in_banner_appointments(data_dir):
    fis_gwids = load_fis_faculty(data_dir)
    banner_demographic_gwids = load_banner_demographic(data_dir)
    gwids = fis_gwids.intersection(banner_demographic_gwids)
    banner_appointment_gwids = load_banner_appointment(data_dir)
    return gwids - banner_appointment_gwids


def fis_faculty_and_banner_demographics_intersection_not_in_banner_appointments_or_fis_appointments(data_dir):
    return fis_faculty_and_banner_demographics_intersection_not_in_banner_appointments(data_dir) - \
           load_fis_appointments(data_dir)


def fis_appointments(data_dir):
    return load_banner_appointment(data_dir)


def fis_appointments_in_banner_demographics(data_dir):
    return load_banner_appointment(data_dir).intersection(load_banner_demographic(data_dir))


def fis_faculty_and_banner_appointments_intersection(data_dir):
    return load_banner_appointment(data_dir).intersection(load_fis_faculty(data_dir))


def fis_faculty_roles(data_dir):
    roles = Counter()
    for result in xml_result_generator(os.path.join(data_dir, "fis_faculty.xml")):
        roles[result["role"]] += 1
    return roles


def match_job_title(data_dir, gwids):
    gwid_map = {}
    job_title_map = load_banner_job_titles(data_dir)
    for gwid in gwids:
        gwid_map[gwid] = job_title_map.get(gwid)
    return gwid_map


def load_fis_faculty(data_dir):
    gwids = set()
    for result in xml_result_generator(os.path.join(data_dir, "fis_faculty.xml")):
        if result["role"] in ("Dean", "Dep Head", "Provost", "Faculty"):
            gwids.add(result["gw_id"])
    return gwids


def load_fis_appointments(data_dir):
    gwids = set()
    for result in xml_result_generator(os.path.join(data_dir, "fis_academic_appointment.xml")):
        gwids.add(result["gw_id"])
    for result in xml_result_generator(os.path.join(data_dir, "fis_admin_appointment.xml")):
        result["gw_id"]
    return gwids


def load_banner_demographic(data_dir):
    gwids = set()
    with codecs.open(os.path.join(data_dir, "vivo_demographic.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        for row in reader:
            gwids.add(row["EMPLOYEEID"])
    return gwids


def load_banner_appointment(data_dir):
    gwids = set()
    with codecs.open(os.path.join(data_dir, "vivo_acadappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        for row in reader:
            gwids.add(row["EMPLOYEEID"])
    return gwids


def load_banner_job_titles(data_dir):
    jobs = {}
    with codecs.open(os.path.join(data_dir, "vivo_emplappt.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        for row in reader:
            jobs[row["EMPLOYEEID"]] = row["JOB_TITLE"]
    return jobs


if __name__ == "__main__":

    reports = {
        "fis_appointments_with_invalid_college_or_department": fis_appointments_with_invalid_college_or_department,
        "fis_faculty_with_no_appointments": fis_faculty_with_no_appointments,
        "fis_faculty_not_in_banner": fis_faculty_not_in_banner,
        "fis_faculty_in_banner": fis_faculty_in_banner,
        "fis_appointments_not_in_banner_demographic": fis_appointments_not_in_banner_demographic,
        "fis_appointments_not_in_banner_appointments_in_banner_demographics":
            fis_appointments_not_in_banner_appointments_in_banner_demographics,
        "fis_faculty_and_banner_demographics_intersection": fis_faculty_and_banner_demographics_intersection,
        "fis_faculty_and_banner_demographics_intersection_not_in_banner_appointments":
            fis_faculty_and_banner_demographics_intersection_not_in_banner_appointments,
        "fis_faculty_with_no_appointments_and_in_banner": fis_faculty_with_no_appointments_and_in_banner,
        "fis_appointments": fis_appointments,
        "fis_appointments_in_banner_demographics": fis_appointments_in_banner_demographics,
        "fis_faculty_roles": fis_faculty_roles,
        "banner_appointments": load_banner_appointment,
        "fis_faculty_and_banner_appointments_intersection": fis_faculty_and_banner_appointments_intersection,
        "fis_faculty_and_banner_demographics_intersection_not_in_banner_appointments_or_fis_appointments":
            fis_faculty_and_banner_demographics_intersection_not_in_banner_appointments_or_fis_appointments,
    }

    parser = argparse.ArgumentParser()
    default_data_dir = "../data"
    parser.add_argument("--data-dir", default=default_data_dir, dest="data_dir",
                        help="Directory containing the data files. Default is %s" % default_data_dir)
    parser.add_argument("--file", action="store_true", help="Write output to file.")
    parser.add_argument("--job", action="store_true", help="Map gwids to job titles")
    parser.add_argument("report_type", choices=reports.keys(),
                        help="The report to run.")

    args = parser.parse_args()
    main_result = reports[args.report_type](args.data_dir)
    if args.job:
        main_result = match_job_title(args.data_dir, main_result)

    if args.file:
        with open("{}.txt".format(args.report_type), 'w') as f:
            if isinstance(main_result, dict):
                for key, value in main_result.items():
                    f.write("{}: {}".format(key, value))
                    f.write("\n")
            else:
                for value in main_result:
                    f.write(value)
                    f.write("\n")
    else:
        if isinstance(main_result, dict):
            print "\n".join(["{} ==> {}".format(key, value) for key, value in main_result.items()])
        else:
            print "\n".join(main_result)
