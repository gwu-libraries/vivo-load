GWU VIVO Load
-------------

A proof-of-concept tool for loading GWU data into [VIVO](http://vivoweb.org).
 
Currently supports loading data from an export from 
[Lyterati](http://www.entigence.com/#!lyterati/c6jw), the University's faculty information 
system, and [Banner](https://banweb.gwu.edu), the University's business operations system.

This code is intended to run in the [load docker container](https://github.com/gwu-libraries/vivo-docker).

Data is loaded "as is".  **No data clean-up is performed.**

Running a load
===========
Notes:

* By default, the Lyterati and Banner export is expected to be in `./data`.  (Make sure to use 
non-password protected versions of the files.)  This can be overridden with `--data-dir`.
* A web server is required (to support a SPARQL Load).  The default location for the 
html document root directory is `/usr/local/apache2/htdocs`.  This can be overridden with `--htdocs-dir`.
* To support only loading diffs, previously loaded graphs are stored.  The default location is `/usr/local/vivo/graphs`.
This can be overridden with `--graph-dir`.
* The default username for the VIVO root account is `vivo_root@gwu.edu`.  This can be overridden with `--username`.
* The default password for the VIVO root password is `password`.  This can be overridden with `--password`.

To get help:

```
root@e0ce83c6824b:/usr/local/vivo-load# python load.py -h
usage: load.py [-h] [--skip-load] [--skip-diff] [--skip-serialize]
               [--split-size SPLIT_SIZE]
               [--delete-split-size DELETE_SPLIT_SIZE] [--data-dir DATA_DIR]
               [--htdocs-dir HTDOCS_DIR] [--graph-dir GRAPH_DIR]
               {l_faculty,l_academic_appointment,l_admin_appointment,l_research,l_education,l_courses,l_service,b_orgn,b_college,b_department,b_demographic,b_emplappt,b_acadappt,b_courses}
               ...

positional arguments:
  {l_faculty,l_academic_appointment,l_admin_appointment,l_research,l_education,l_courses,l_service,b_orgn,b_college,b_department,b_demographic,b_emplappt,b_acadappt,b_courses}

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
  --data-dir DATA_DIR   Directory containing the xlsx. Default is ./data
  --htdocs-dir HTDOCS_DIR
                        Directory from which html documents are served.
                        Default is /usr/local/apache2/htdocs.
  --graph-dir GRAPH_DIR
                        Directory where graphs are archived. Default is
                        /usr/local/vivo/graphs.
root@e0ce83c6824b:/usr/local/vivo-load# python load.py l_faculty -h
usage: load.py l_faculty [-h] [--limit LIMIT] [--skip-vcards]
                         [--skip-departments] [--skip-persons]

optional arguments:
  -h, --help          show this help message and exit
  --limit LIMIT       Number of rows from csv to load.
  --skip-vcards
  --skip-departments
  --skip-persons

```

Export files are loaded one at a time.  For the current recommended order for loading exports, see 
[Load order](https://github.com/gwu-libraries/vivo-load/wiki/Load-order).

Generating the RDF is fast.  **Loading the RDF into VIVO is extremely slow.**  Be patient.

