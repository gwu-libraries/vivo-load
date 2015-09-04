from fis_entity import *
from namespace import D
import argparse
from rdflib.compare import graph_diff
from sparql import load_previous_graph, sparql_load, sparql_delete, serialize
import fis_load
import banner_load
import mygw_load
import orcid2vivo_loader
from collections import OrderedDict
from utility import remove_extra_args
import time
import datetime


def process_graph(g, local_args):
    if local_args.perform_diff:
        #Load the previous graph
        prev_g = load_previous_graph(local_args.graph_dir, local_args.graph)
    else:
        prev_g = Graph(namespace_manager=ns_manager)

    #Find the diff
    (g_both, g_del, g_add) = graph_diff(prev_g, g)
    g_add.namespace_manager = ns_manager
    g_del.namespace_manager = ns_manager

    #Print the diff
    print "To add %s triples." % len(g_add)
    if local_args.print_triples:
        print g_add.serialize(format="turtle")
    print "To delete %s triples." % len(g_del)
    if local_args.print_triples:
        print g_del.serialize(format="turtle")

    if local_args.perform_load:
        if len(g_add) > 0:
            sparql_load(g_add, local_args.htdocs_dir, local_args.endpoint, local_args.username, local_args.password,
                        split_size=local_args.split_size)
        if len(g_del) > 0:
            sparql_delete(g_del, local_args.endpoint, local_args.username, local_args.password,
                          split_size=local_args.delete_split_size)

    #Save to graphs archive directory
    if local_args.perform_load and local_args.perform_serialize:
        serialize(g, local_args.graph_dir, local_args.graph)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-load", action="store_false", dest="perform_load",
                        help="Generate RDF, but do not load into VIVO.")
    parser.add_argument("--skip-diff", action="store_false", dest="perform_diff",
                        help="Load everything, not just the difference with last load.")
    parser.add_argument("--skip-serialize", action="store_false", dest="perform_serialize",
                        help="Don't save the load.")
    parser.add_argument("--skip-orcid2vivo", action="store_false", dest="perform_orcid2vivo",
                        help="Skip running orcid2vivo.")
    default_split_size = 10000
    parser.add_argument("--split-size", type=int, default=default_split_size,
                        help="Maximum number of triples to include in a single load. Default is %s" %
                             default_split_size)
    default_delete_split_size = 2500
    parser.add_argument("--delete-split-size", type=int, default=default_delete_split_size,
                        help="Maximum number of triples to include in a single delete. "
                             "Default is %s" % default_delete_split_size)
    default_data_dir = "./data"
    parser.add_argument("--data-dir", default=default_data_dir, dest="data_dir",
                        help="Directory containing the data files. Default is %s" % default_data_dir)
    default_htdocs_dir = "/usr/local/apache2/htdocs"
    parser.add_argument("--htdocs-dir", default=default_htdocs_dir, dest="htdocs_dir",
                        help="Directory from which html documents are served. Default is %s." % default_htdocs_dir)
    default_graph_dir = "/usr/local/vivo/graphs"
    parser.add_argument("--graph-dir", default=default_graph_dir, dest="graph_dir",
                        help="Directory where graphs are archived. Default is %s." % default_graph_dir)
    default_username = "vivo_root@gwu.edu"
    parser.add_argument("--username", default=default_username, dest="username",
                        help="Username for VIVO root. Default is %s." % default_username)
    default_password = "password"
    parser.add_argument("--password", default=default_password, dest="password",
                        help="Password for VIVO root. Default is %s." % default_password)
    default_endpoint = "http://tomcat:8080/vivo/api/sparqlUpdate"
    parser.add_argument("--endpoint", default=default_endpoint, dest="endpoint",
                        help="Endpoint for SPARQL Update. Default is %s." % default_endpoint)
    parser.add_argument("--print-triples", action="store_true",
                        help="Print the triples to be added and deleted.")

    parser.add_argument("--limit", type=int, help="Limit to number of rows from data file to load.")
    parser.add_argument("--faculty-limit", type=int, help="Limit to number of faculty to load.", dest="fac_limit")
    parser.add_argument("--non-faculty-limit", type=int, help="Limit to number of non-faculty to load.",
                        dest="non_fac_limit")
    parser.add_argument("--skip-appt", action="store_false", dest="load_appt",
                        help="Skip loading the academic appointment for the faculty. For b_acadappt only.")
    parser.add_argument("--resume", action="store_true",
                        help="Resume loading all starting with the provided data type.")
    default_orcid2vivo_days = 7
    parser.add_argument("--orcid2vivo-days", type=int, default=default_orcid2vivo_days,
                        help="Run orcid2vivo for orcid ids that have never been loaded or have not been loaded in this "
                             "many days. Default is %s days." % default_orcid2vivo_days)

    #Map of label for data type to load function.
    data_type_map = OrderedDict([
        ("b_demographic", banner_load.load_demographic),
        ("b_organization", banner_load.load_orgn),
        ("b_emplappt", banner_load.load_emplappt),
        # ("b_acadappt", banner_load.load_acadappt),
        ("fis_department", fis_load.load_departments),
        ("fis_faculty", fis_load.load_faculty),
        ("fis_acadappt", fis_load.load_academic_appointment),
        ("fis_adminappt", fis_load.load_admin_appointment),
        ("fis_degree_ed", fis_load.load_degree_education),
        ("fis_non_degree_ed", fis_load.load_non_degree_education),
        ("fis_courses", fis_load.load_courses),
        ("fis_awards", fis_load.load_awards),
        ("fis_prof_memberships", fis_load.load_professional_memberships),
        ("fis_reviewers", fis_load.load_reviewerships),
        ("fis_presentations", fis_load.load_presentations),
        ("fis_books", fis_load.load_books),
        ("fis_reports", fis_load.load_reports),
        ("fis_articles", fis_load.load_articles),
        ("fis_acad_articles", fis_load.load_academic_articles),
        ("fis_article_abstracts", fis_load.load_article_abstracts),
        ("fis_reviews", fis_load.load_reviews),
        ("fis_ref_articles", fis_load.load_reference_articles),
        ("fis_letters", fis_load.load_letters),
        ("fis_testimony", fis_load.load_testimony),
        ("fis_chapters", fis_load.load_chapters),
        ("fis_conf_abstracts", fis_load.load_conference_abstracts),
        ("fis_patents", fis_load.load_patents),
        ("fis_grants", fis_load.load_grants),
        ("mygw_awards", mygw_load.load_awards),
        ("mygw_prof_memberships", mygw_load.load_professional_memberships),
        ("mygw_reviewers", mygw_load.load_reviewerships),
        ("mygw_presentations", mygw_load.load_presentations),
        ("mygw_users", mygw_load.load_users)
    ])

    data_types = list(data_type_map.keys())
    data_types.append("all")

    parser.add_argument("data_type", nargs="+", choices=data_types,
                        help="The type of data to load or all for all data.")

    #Parse
    args = parser.parse_args()

    #If all selected or resuming
    if "all" in args.data_type or (args.resume and len(args.data_type) == 1):
        #Forcing skipping appt for b_acadappt
        args.load_appt = False

    if "all" in args.data_type:
        print "Loading all"
        #Replace data types with ordered list of all data types
        args.data_type = data_type_map.keys()

    if args.resume and len(args.data_type) == 1:
        resume_data_type = args.data_type[0]
        print "Resuming with %s" % resume_data_type
        args.data_type = []
        found_resume_data_type = False
        for data_type in data_type_map.keys():
            if resume_data_type == data_type:
                found_resume_data_type = True
            if found_resume_data_type:
                args.data_type.append(data_type)

    start_time = time.time()

    #Load non_faculty_gwids and faculty_gwids
    non_faculty_gwids = get_non_faculty_gwids(args.data_dir, args.non_fac_limit)
    print "%s non-faculty" % len(non_faculty_gwids)
    faculty_gwids = get_faculty_gwids(args.data_dir, args.fac_limit)
    print "%s faculty" % len(faculty_gwids)

    #Setup directory for orcid2vivo
    store_dir = os.path.join(args.graph_dir, "orcid")
    print "The store path is %s" % store_dir
    if not os.path.exists(store_dir):
        os.mkdir(store_dir)

    #Load each data type
    for data_type in args.data_type:
        func_args = vars(args).copy()
        func_args["non_faculty_gwids"] = non_faculty_gwids
        func_args["faculty_gwids"] = faculty_gwids
        func_args["store_dir"] = store_dir
        args.graph = data_type
        func = data_type_map[data_type]
        #Limit to actual arguments
        remove_extra_args(func_args, func)
        graph = func(**func_args)
        process_graph(graph, args)

    #Run orcid2vivo
    if args.perform_orcid2vivo:
        print "Running orcid2vivo."
        before_datetime = datetime.datetime.now() - datetime.timedelta(days=args.orcid2vivo_days)
        orcid_ids = orcid2vivo_loader.load(store_dir, args.endpoint, args.username, args.password,
                                           limit=None, before_datetime=before_datetime, namespace=D, skip_person=True)
        print "Loaded %s orcid_ids." % len(orcid_ids)

    else:
        print "Skipping orcid2vivo."

    print "Done in %.2f seconds." % (time.time() - start_time)