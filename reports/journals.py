import sys
import os
sys.path.append(os.path.abspath('..'))
import petl as etl
#These imports are necessary to configure ETL.
import loader.utility


"""
Counts of journal names by publication year.
"""


def process(year):
    articles = etl.frommysqlxml("../data/fis_articles.xml")
    acad_articles = etl.frommysqlxml("../data/fis_acad_articles.xml")
    (etl
     .cat(articles, acad_articles)
     .selecteq("start_year", str(year))
     .valuecounts("publication_venue")
     .cutout("frequency")
     .toxlsx("journals_{}.xlsx".format(year)))

if __name__ == "__main__":
    process(2014)
    process(2015)