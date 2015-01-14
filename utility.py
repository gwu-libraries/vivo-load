from numbers import Number
import hashlib
from rdflib import Literal, RDF, RDFS, XSD
from namespace import *
import re

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


def to_identifier(prefix, string):
    """
    Converts a string into an identifier with an optional prefix.

    A string is converted into an identifier by removing spaces, title casing,
    and cleaning up newlines.
    """
    return "%s-%s" % (prefix, string.replace("\n", " ").title().replace(" ", ""))


def to_hash_identifier(prefix, parts):
    """
    Return an identifier composed of the prefix and hash of the parts.
    """
    hash_parts = hashlib.md5("".join([part for part in parts if part]).encode("utf-8"))
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


def month_str_to_month_int(month_str):
    """
    Converts a month name to the corresponding month number.
    """
    if isinstance(month_str, Number):
        return month_str

    return ("January",
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
            "December").index(month_str)+1


def add_date(date_uri, start_year, g, start_month=None, label=None):
    """
    Adds triples for a date.
    """
    #Date
    if start_year:
        g.add((date_uri, RDF.type, VIVO.DateTimeValue))
        #Month and year
        if start_month:
            g.add((date_uri, VIVO.dateTimePrecision, VIVO.yearMonthPrecision))
            g.add((date_uri, VIVO.dateTime,
                   Literal("%s-%02d-01T00:00:00" % (
                       start_year, month_str_to_month_int(start_month)),
                       datatype=XSD.dateTime)))
            g.add((date_uri,
                   RDFS.label,
                   Literal(label or "%s %s" % (start_month, num_to_str(start_year)))))
        else:
            #Just year
            g.add((date_uri, VIVO.dateTimePrecision, VIVO.yearPrecision))
            g.add((date_uri, VIVO.dateTime,
                   Literal("%s-01-01T00:00:00" % (
                       start_year),
                       datatype=XSD.dateTime)))
            g.add((date_uri, RDFS.label, Literal(label or num_to_str(start_year))))

term_re = re.compile("(Spring|Summer|Fall) (\d\d\d\d)")


def add_season_date(date_uri, date_str, g):
    """
    Parses a season date (e.g., Spring 2012) and adds tripes.

    Returns true if parse was successful.
    """
    m = term_re.match(date_str)
    if m:
        season = m.group(1)
        year = m.group(2)
        add_date(date_uri, year, g, season_to_month(season), date_str)
        return True
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
