import sys
import os
sys.path.append(os.path.abspath('..'))
import petl as etl
#These imports are necessary to configure ETL.
import loader.utility
import csv


"""
These are to pull reports requested by Himmelfarb Library on publications from the
School of Medicine and Health Sciences', Milken Institute School of Public Health, and School of Nursing.
"""


def process(pub_type):
    print pub_type
    output_dir = "med"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    demographics = (etl
                    .fromcsv("../data/vivo_demographic.txt", delimiter="|")
                    .cut("EMPLOYEEID", "FIRST_NAME", "MIDDLE_NAME", "LAST_NAME")
                    .rename({"FIRST_NAME": "first_name", "MIDDLE_NAME": "middle_name", "LAST_NAME": "last_name"}))
    limited_faculty = (etl
                       .frommysqlxml("../data/fis_faculty.xml")
                       .selectin("home_college", (u'School of Medicine and Health Sciences',
                                                  u'Milken Institute School of Public Health',
                                                  u'School of Nursing'))
                       .cut("gw_id", "home_department", "home_college"))
    limited_demographics = etl.join(demographics, limited_faculty, lkey="EMPLOYEEID", rkey="gw_id")
    (etl
           .frommysqlxml("../data/fis_{}.xml".format(pub_type))
           .join(limited_demographics, lkey="gw_id", rkey="EMPLOYEEID")
           .cutout("gw_id")
           .movefield("first_name", 0)
           .movefield("middle_name", 1)
           .movefield("last_name", 2)
           .toxlsx("{}/{}.xlsx".format(output_dir, pub_type)))


if __name__ == "__main__":

    process("acad_articles")
    process("articles")
    process("books")
    process("chapters")
    process("conf_abstracts")
    process("conf_papers")
    process("conf_posters")
    process("letters")
    process("ref_articles")
    process("reports")
    process("reviews")
    process("testimony")
