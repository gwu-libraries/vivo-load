GWU VIVO Load
-------------

A proof-of-concept tool for loading GWU data into [VIVO](http://vivoweb.org).
 
Currently supports loading data from an export from 
[Lyterati](http://www.entigence.com/#!lyterati/c6jw), the University's faculty information 
system.

This code is intended to run in the [load docker container](https://github.com/gwu-libraries/vivo-docker).

Data is loaded "as is".  **No data clean-up is performed.**

See the wiki for notes on the data load.

Running a load
===========
Notes:

* By default, the Lyterati export is expected to be in `./data`.  (Make sure to use 
non-password protected versions of the files.)  This can be overridden with `--data-dir`.
* A web server is required (to support a SPARQL Load).  The default location for the 
html document root directory is `/usr/local/apache2/htdocs`.  This can be overridden with `--htdocs-dir`.

To get help:

```
root@f318829a166d:/usr/local/vivo-load# python load.py -h                  
usage: load.py [-h] [--skip-load] [--data-dir DATA_DIR]
               [--htdocs-dir HTDOCS_DIR]
               {faculty,academic_appointment,research,education} ...

positional arguments:
  {faculty,academic_appointment,research,education}

optional arguments:
  -h, --help            show this help message and exit
  --skip-load           Generate RDF, but do not load into VIVO.
  --data-dir DATA_DIR   Directory containing the xlsx. Default is ./data
  --htdocs-dir HTDOCS_DIR
                        Directory from which html documents are served.
                        Default is /usr/local/apache2/htdocs.
root@f318829a166d:/usr/local/vivo-load# python load.py faculty -h
usage: load.py faculty [-h] [--limit LIMIT] [--skip-vcards]
                       [--skip-facilities] [--skip-departments]

optional arguments:
  -h, --help          show this help message and exit
  --limit LIMIT       Number of rows from csv to load.
  --skip-vcards
  --skip-facilities
  --skip-departments
```

Export files are loaded one at a time.  For example:

```
root@f318829a166d:/usr/local/vivo-load# python load.py -h                  
```

Generating the RDF is fast.  **Loading the RDF into VIVO is extremely slow.**  Be patient.

