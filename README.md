GWU VIVO Load
-------------

A proof-of-concept tool for loading GWU data into [VIVO](http://vivoweb.org).
 
Currently supports loading data from an export from [Banner](https://banweb.gwu.edu), 
the University's business operations system, and the University's faculty information 
system.

This code is intended to run in the [load docker container](https://github.com/gwu-libraries/vivo-docker).

Data is loaded "as is".  **No data clean-up is performed.**

Running a load
===========
Notes:

* By default, the exports are expected to be in `./data`.  (Make sure to use 
non-password protected versions of the files.)  This can be overridden with `--data-dir`.
* A web server is required (to support a SPARQL Load).  The default location for the 
html document root directory is `/usr/local/apache2/htdocs`.  This can be overridden with `--htdocs-dir`.
* To support only loading diffs, previously loaded graphs are stored.  The default location is `/usr/local/vivo/graphs`.
This can be overridden with `--graph-dir`.
* The default endpoint for SPARQL Update is `http://tomcat:8080/vivo/api/sparqlUpdate`.  This can be overridden with `--endpoint`.
* The default username for the VIVO root account is `vivo_root@gwu.edu`.  This can be overridden with `--username`.
* The default password for the VIVO root password is `password`.  This can be overridden with `--password`.
* To load all data in the recommended order, use `all` as the data type.

To get help:

```
root@ec55c8bc01ee:/usr/local/vivo-load# python load.py -h                                           
usage: load.py [-h] [--skip-load] [--skip-diff] [--skip-serialize]
               [--split-size SPLIT_SIZE]
               [--delete-split-size DELETE_SPLIT_SIZE] [--data-dir DATA_DIR]
               [--htdocs-dir HTDOCS_DIR] [--graph-dir GRAPH_DIR]
               [--username USERNAME] [--password PASSWORD]
               [--endpoint ENDPOINT] [--print-triples] [--limit LIMIT]
               [--faculty-limit FAC_LIMIT] [--non-faculty-limit NON_FAC_LIMIT]
               [--skip-appt]
               {b_demographic,b_organization,b_emplappt,b_acadappt,fis_department,fis_faculty,fis_acadappt,fis_degree_ed,fis_non_degree_ed,fis_courses,fis_awards,fis_prof_memberships,fis_reviewers,fis_presentations,fis_books,fis_reports,fis_articles,fis_acad_articles,fis_article_abstracts,fis_reviews,fis_ref_articles,fis_letters,fis_testimony,fis_chapters,fis_conf_abstracts,fis_patents,fis_grants,all}
               [{b_demographic,b_organization,b_emplappt,b_acadappt,fis_department,fis_faculty,fis_acadappt,fis_degree_ed,fis_non_degree_ed,fis_courses,fis_awards,fis_prof_memberships,fis_reviewers,fis_presentations,fis_books,fis_reports,fis_articles,fis_acad_articles,fis_article_abstracts,fis_reviews,fis_ref_articles,fis_letters,fis_testimony,fis_chapters,fis_conf_abstracts,fis_patents,fis_grants,all} ...]

positional arguments:
  {b_demographic,b_organization,b_emplappt,b_acadappt,fis_department,fis_faculty,fis_acadappt,fis_degree_ed,fis_non_degree_ed,fis_courses,fis_awards,fis_prof_memberships,fis_reviewers,fis_presentations,fis_books,fis_reports,fis_articles,fis_acad_articles,fis_article_abstracts,fis_reviews,fis_ref_articles,fis_letters,fis_testimony,fis_chapters,fis_conf_abstracts,fis_patents,fis_grants,all}
                        The type of data to load or all for all data.

optional arguments:
  -h, --help            show this help message and exit
  --skip-load           Generate RDF, but do not load into VIVO.
  --skip-diff           Load everything, not just the difference with last
                        load.
  --skip-serialize      Don't save the load.
  --split-size SPLIT_SIZE
                        Maximum number of triples to include in a single load.
                        Default is 10000
  --delete-split-size DELETE_SPLIT_SIZE
                        Maximum number of triples to include in a single
                        delete. Default is 2500
  --data-dir DATA_DIR   Directory containing the data files. Default is ./data
  --htdocs-dir HTDOCS_DIR
                        Directory from which html documents are served.
                        Default is /usr/local/apache2/htdocs.
  --graph-dir GRAPH_DIR
                        Directory where graphs are archived. Default is
                        /usr/local/vivo/graphs.
  --username USERNAME   Username for VIVO root. Default is vivo_root@gwu.edu.
  --password PASSWORD   Password for VIVO root. Default is password.
  --endpoint ENDPOINT   Endpoint for SPARQL Update. Default is
                        http://tomcat:8080/vivo/api/sparqlUpdate.
  --print-triples       Print the triples to be added and deleted.
  --limit LIMIT         Limit to number of rows from data file to load.
  --faculty-limit FAC_LIMIT
                        Limit to number of faculty to load.
  --non-faculty-limit NON_FAC_LIMIT
                        Limit to number of non-faculty to load.
  --skip-appt           Skip loading the academic appointment for the faculty.
                        For b_acadappt only.
```

Generating the RDF is fast.  **Loading the RDF into VIVO is extremely slow.**  Be patient.

