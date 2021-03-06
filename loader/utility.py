import csv
import hashlib
import inspect
import logging
from numbers import Number

from namespace import *

import codecs
import os
import petl as etl
import re
from loader.prefixes import PREFIX_LANGUAGE, PREFIX_MULTIMEDIA
from lxml import etree
from petl.util.base import Table
from rdflib import Literal, RDF, RDFS, XSD

# A logger to be used for logging warnings or errors detected during loading.
warning_log = logging.getLogger("load_warnings")
warning_log.setLevel(logging.WARNING)


def num_to_str(num):
    """
    Converts a number to a string.

    If the number is already a string, then just returns.
    """
    if isinstance(num, Number):
        return str(int(num))
    return num


def join_if_not_empty(items, sep=" "):
    """
    Joins a list of items with a provided separator.

    Skips an empty item.
    """
    joined = ""
    for item in items:
        if item and len(item) > 0:
            if joined != "":
                joined += sep
            joined += item
    return joined


def to_hash_identifier(prefix, parts):
    """
    Return an identifier composed of the prefix and hash of the parts.
    """
    hash_parts = hashlib.md5("".join([unicode(part) for part in parts if part]).encode("utf-8"))
    return "%s-%s" % (prefix, hash_parts.hexdigest())


def season_to_month(season):
    """
    Converts a season to the corresponding month.
    """
    return {
        "Spring": 1,
        "Summer": 5,
        "Fall": 8
    }[season]

months = ("January",
          "February",
          "March",
          "April",
          "May",
          "June",
          "July",
          "August",
          "September",
          "October",
          "November",
          "December")


def month_str_to_month_int(month_str):
    """
    Converts a month name to the corresponding month number.

    If already a number, returns the number.

    Also, tries to convert the string to a number.
    """
    if isinstance(month_str, Number):
        return month_str

    try:
        return int(month_str)
    except ValueError:
        pass

    return months.index(month_str)+1


def month_int_to_month_str(month_int):
    if isinstance(month_int, basestring):
        return month_int

    return months[month_int-1]


def add_date(date_uri, year, g, month=None, day=None, label=None):
    """
    Adds triples for a date.

    Return True if date was added.
    """
    # Date
    # Filtering out dates that are set to 1900.
    if year and str(year) != "1900":
        g.add((date_uri, RDF.type, VIVO.DateTimeValue))
        # Day, month, and year
        if day and month:
            g.add((date_uri, VIVO.dateTimePrecision, VIVO.yearMonthDayPrecision))
            g.add((date_uri, VIVO.dateTime,
                   Literal("%s-%02d-%02dT00:00:00" % (
                       year, month_str_to_month_int(month), day),
                       datatype=XSD.dateTime)))
            g.add((date_uri,
                   RDFS.label,
                   Literal(label or "%s %s, %s" % (month_int_to_month_str(month), num_to_str(day), num_to_str(year)))))
        # Month and year
        elif month:
            g.add((date_uri, VIVO.dateTimePrecision, VIVO.yearMonthPrecision))
            g.add((date_uri, VIVO.dateTime,
                   Literal("%s-%02d-01T00:00:00" % (
                       year, month_str_to_month_int(month)),
                       datatype=XSD.dateTime)))
            g.add((date_uri,
                   RDFS.label,
                   Literal(label or "%s %s" % (month, num_to_str(year)))))
        else:
            # Just year
            g.add((date_uri, VIVO.dateTimePrecision, VIVO.yearPrecision))
            g.add((date_uri, VIVO.dateTime,
                   Literal("%s-01-01T00:00:00" % (
                       year),
                       datatype=XSD.dateTime)))
            g.add((date_uri, RDFS.label, Literal(label or num_to_str(year))))
        return True
    return False

term_re = re.compile("(Spring|Summer|Fall) (\d\d\d\d)")


def add_season_date(date_uri, date_str, g):
    """
    Parses a season date (e.g., Spring 2012) and adds tripes.

    Returns true if parse was successful.
    """
    if date_str:
        m = term_re.match(date_str)
        if m:
            season = m.group(1)
            year = m.group(2)
            return add_date(date_uri, year, g, season_to_month(season), label=date_str)
    return False


def add_date_interval(interval_uri, subject_uri, g, start_uri=None, end_uri=None):
    """
    Adds triples for a date interval.
    """
    if start_uri or end_uri:
        g.add((interval_uri, RDF.type, VIVO.DateTimeInterval))
        g.add((subject_uri, VIVO.dateTimeInterval, interval_uri))
        if start_uri:
            g.add((interval_uri, VIVO.start, start_uri))
        if end_uri:
            g.add((interval_uri, VIVO.end, end_uri))

language_map = {
    "ARAB":  "Arabic",
    "BENG": "Bengali",
    "CHIN": "Chinese",
    "FREN": "French",
    "GERM": "German",
    "HIND": "Hindi/Urdu",
    "ITAL": "Italian",
    "JAPN": "Japanese",
    "KREN": "Korean",
    "MAND": "Mandarin",
    "PORT": "Portuguese",
    "PUNJ": "Punjabi",
    "RUSS": "Russian",
    "SPAN": "Spanish"
}


def add_language(language, person_uri, g):
    language_uri = D[to_hash_identifier(PREFIX_LANGUAGE, (language,))]
    g.add((language_uri, RDF.type, LINKVOJ.Lingvo))
    g.add((language_uri, RDFS.label, Literal(language)))
    g.add((person_uri, LINKVOJ.expertUnderstanding, language_uri))


def add_multimedia(multimedia, person_uri, multimedia_predicate, g):
    if not multimedia.endswith(","):
        multimedia += ","
    for multimedia_string in re.findall(r".\|.+?\|.+?,", multimedia):
        (multimedia_type, multimedia_label, multimedia_url) = multimedia_string[:-1].split("|")
        multimedia_uri = D[to_hash_identifier(PREFIX_MULTIMEDIA, multimedia_url)]
        if multimedia_type == "A":
            multimedia_class = BIBO.AudioDocument
        elif multimedia_type == "O":
            multimedia_class = BIBO.Webpage
        else:
            multimedia_class = VIVO.Video
        g.add((multimedia_uri, RDF.type, multimedia_class))
        g.add((person_uri, multimedia_predicate, multimedia_uri))
        g.add((multimedia_uri, RDFS.label, Literal(multimedia_label)))
        g.add((multimedia_uri, VCARD.url, Literal(multimedia_url, datatype=XSD.anyURI)))


def strip_gw_prefix(string):
    if isinstance(string, basestring) and string.startswith("GW_"):
        return string[3:]
    return string


def xml_result_generator(filepath):
    """
    Returns a generator that provides maps of field names to values read from
    xml produced by mysql --xml.
    """
    # Using lxml because recover=True makes it tolerant of unicode encoding problems.
    for event, row_elem in etree.iterparse(filepath, tag="row", recover=True):
        result = {}
        for field_elem in row_elem.iter("field"):
            if "xsi:nil" in field_elem.attrib or not field_elem.text:
                value = None
            else:
                # Strip whitespace
                value = field_elem.text.strip()
            result[field_elem.get("name")] = value
        row_elem.clear()
        yield result


def remove_extra_args(func_args, func):
    """
    Removes values from map of function arguments that are not necessary to invoke the function.
    """
    (arg_names, varargs, keywords, defaults) = inspect.getargspec(func)
    for key in list(func_args.keys()):
        if key not in arg_names:
            del func_args[key]


def valid_department_name(name):
    if name and name not in ("No Department", "University-level Dept"):
        return True
    return False


def valid_college_name(name):
    if name and name not in ("University", "No College Designated"):
        return True
    return False


# Register banner dialect
csv.register_dialect("banner", delimiter="|")

# Map of banner position codes to VIVO classes
pos_code_to_classes = {
    # Research scientist or related
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
    # Postdoc
    "289A1": "Postdoc",
    "289A2": "Postdoc",
    # Librarian
    "OC221": "Librarian",
    "OC231": "Librarian",
    "OD311": "Librarian",
    "OC241": "Librarian",
    "OC211": "Librarian",
    "30401": "Librarian",
    "OC341": "Librarian",
    "OA411": "Librarian",
    "OC321": "Librarian"
}


def get_netid_lookup(data_dir):
    """
    Returns a map of gwids to netids.
    """
    netid_map = {}
    with codecs.open(os.path.join(data_dir, "vivo_demographic.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        for row in reader:
            netid_map[row["EMPLOYEEID"]] = row["NETID"]
    return netid_map


def demographic_intersection(gwids, data_dir):
    """
    Returns the intersection of a provided list of gwids and the gwids in banner
    demographic data.
    """
    demo_gwids = set()
    with codecs.open(os.path.join(data_dir, "vivo_demographic.txt"), 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, dialect="banner")
        for row in reader:
            demo_gwids.add(row["EMPLOYEEID"])
    return list(demo_gwids.intersection(gwids))


def get_non_faculty_gwids(data_dir, non_fac_limit=None):
    """
    Returns the list of non-faculty gwids.

    This is determined by taking the intersection of gwids in banner
    demographic data and gwids in mygw data and
    removing all faculty gwids.
    """
    mygw_gwids = []
    for result in xml_result_generator(os.path.join(data_dir, "mygw_users.xml")):
        mygw_gwids.append(result["gw_id"])

    # Only gwids with demographic data
    demo_gwids = demographic_intersection(mygw_gwids, data_dir)
    # Not faculty gwids
    fac_gwids = get_faculty_gwids(data_dir)
    gwids = [gw_id for gw_id in demo_gwids if gw_id not in fac_gwids]
    if non_fac_limit is not None and len(gwids) > non_fac_limit:
        return gwids[:non_fac_limit]
    else:
        return gwids


def get_faculty_gwids(data_dir, fac_limit=None):
    """
    Returns the list of faculty gwids.
    This is determined by taking the intersection of gwids in banner
    demographic data and fis_faculty in certain roles.
    """
    gwids = set()
    # fis faculty
    for result in xml_result_generator(os.path.join(data_dir, "fis_faculty.xml")):
        if result["role"] in ("Dean", "Dep Head", "Provost", "Faculty", "Faculty-COI", "CLAD"):
            gwids.add(result["gw_id"])
    demo_gwids = demographic_intersection(gwids, data_dir)
    if fac_limit is not None and len(demo_gwids) > fac_limit:
        return demo_gwids[:fac_limit]
    else:
        return demo_gwids


def mediaexpert_intersection(gwids, data_dir):
    """
    Returns the intersection of a provided list of gwids and the gwids in mediaexpert data.
    """
    mediaexpert_gwids = set()
    for result in xml_result_generator(os.path.join(data_dir, "mygw_mediaexperts.xml")):
        mediaexpert_gwids.add(result["gw_id"])
    return list(mediaexpert_gwids.intersection(gwids))


def get_skip_name_gwids(data_dir):
    """
    Returns the list of gwids for mediaexperts that have names.
    """
    skip_name_gwids = set()
    for result in xml_result_generator(os.path.join(data_dir, "mygw_mediaexperts.xml")):
        if result["last_name"]:
            skip_name_gwids.add(result["gw_id"])
    return list(skip_name_gwids)


def format_phone_number(phone_number):
    if phone_number:
        clean_phone_number = phone_number.replace("-", "").replace(" ", "")
        if len(clean_phone_number) == 10:
            return "%s-%s-%s" % (clean_phone_number[0:3], clean_phone_number[3:6], clean_phone_number[6:])
    return None


def frommysqlxml(filename):
    return MySqlXmlView(filename)

etl.frommysqlxml = frommysqlxml


class MySqlXmlView(Table):
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        yielded_field_names = False
        for event, row_elem in etree.iterparse(self.filename, tag="row", recover=True):
            field_names = []
            values = []
            for field_elem in row_elem.iter("field"):
                if "xsi:nil" in field_elem.attrib or not field_elem.text:
                    value = None
                else:
                    # Strip whitespace
                    value = unicode(field_elem.text).strip()
                field_names.append(field_elem.get("name"))
                values.append(value)
            row_elem.clear()
            if not yielded_field_names:
                yield field_names
                yielded_field_names = True
            yield values
