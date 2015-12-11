import sys
import os
sys.path.append(os.path.abspath('..'))
import petl as etl
#These imports are necessary to configure ETL.
import loader.utility


"""
Counts of publications by year.
"""


def process(publication_type):
    print publication_type
    print (etl
     .frommysqlxml("../data/fis_{}.xml".format(publication_type))
     .valuecounts("start_year")
     .cutout("frequency")
     .lookall())

if __name__ == "__main__":
    process("books")
    process("articles")
    process("acad_articles")
