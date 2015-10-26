from utility import xml_result_generator, valid_department_name, valid_college_name
import os
import codecs
import csv
import argparse


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


def fis_faculty_not_in_banner(data_dir):
    fis_gwids = load_fis_faculty(data_dir)
    banner_gwids = load_banner_demographic(data_dir)

    return fis_gwids - banner_gwids


def fis_appointments_not_in_banner_demographic(data_dir):
    fis_gwids = load_fis_appointments(data_dir)
    banner_gwids = load_banner_demographic(data_dir)
    return fis_gwids - banner_gwids


def fis_appointments_not_in_banner_appointments_in_banner_demographics(data_dir):
    fis_gwids = load_fis_appointments(data_dir)
    banner_demographic_gwids = load_banner_demographic(data_dir)
    banner_appointment_gwids = load_banner_appointment(data_dir)
    return fis_gwids.intersection(banner_demographic_gwids) - banner_appointment_gwids


def load_fis_faculty(data_dir):
    gwids = set()
    for result in xml_result_generator(os.path.join(data_dir, "fis_faculty.xml")):
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


if __name__ == "__main__":

    reports = {
        "fis_appointments_with_invalid_college_or_department": fis_appointments_with_invalid_college_or_department,
        "fis_faculty_with_no_appointments": fis_faculty_with_no_appointments,
        "fis_faculty_not_in_banner": fis_faculty_not_in_banner,
        "fis_appointments_not_in_banner_demographic": fis_appointments_not_in_banner_demographic,
        "fis_appointments_not_in_banner_appointments_in_banner_demographics":
            fis_appointments_not_in_banner_appointments_in_banner_demographics
    }

    parser = argparse.ArgumentParser()
    default_data_dir = "./data"
    parser.add_argument("--data-dir", default=default_data_dir, dest="data_dir",
                        help="Directory containing the data files. Default is %s" % default_data_dir)
    parser.add_argument("--file", action="store_true", help="Write output to file.")
    parser.add_argument("report_type", choices=reports.keys(),
                        help="The report to run.")

    args = parser.parse_args()
    main_gwids = reports[args.report_type](args.data_dir)
    if args.file:
        with open("{}.txt".format(args.report_type), 'w') as f:
            for gwid in main_gwids:
                f.write(gwid)
                f.write("\n")
    else:
        print "\n".join(main_gwids)
