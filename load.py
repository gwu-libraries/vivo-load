from fis_entity import *
import argparse
from rdflib.compare import graph_diff
from sparql import load_previous_graph, sparql_load, sparql_delete, serialize
import fis_load
import banner_load
from collections import OrderedDict
from utility import remove_extra_args


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
            sparql_delete(g_del, local_args.username, local_args.endpoint, local_args.password,
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
    default_split_size = 10000
    parser.add_argument("--split-size", type=int, default=default_split_size,
                        help="Maximum number of triples to include in a single load. Default is %s" %
                             default_split_size)
    default_delete_split_size = 2500
    parser.add_argument("--delete-split-size", type=int, default=default_delete_split_size,
                        help="Maximum number of triples to include in a single delete. Default is %s" % default_delete_split_size)
    default_data_dir = "./data"
    parser.add_argument("--data-dir", default=default_data_dir, dest="data_dir",
                        help="Directory containing the xlsx. Default is %s" % default_data_dir)
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

    #Map of label for data type to load function.
    data_type_map = OrderedDict([
        ("b_demographic", banner_load.load_demographic),
        ("b_organization", banner_load.load_orgn),
        ("b_emplappt", banner_load.load_emplappt),
        ("b_acadappt", banner_load.load_acadappt),
        ("fis_department", fis_load.load_departments),
        ("fis_faculty", fis_load.load_faculty),
        ("fis_acadappt", fis_load.load_academic_appointment),
        ("fis_degree_ed", fis_load.load_degree_education),
        ("fis_non_degree_ed", fis_load.load_non_degree_education),
        ("fis_courses", fis_load.load_courses),
        ("fis_awards", fis_load.load_awards),
        ("fis_prof_memberships", fis_load.load_professional_memberships),
        ("fis_reviewers", fis_load.load_reviewerships),
        ("fis_presentations", fis_load.load_presentations)
        #TODO:  Rest of service and research

    ])

    data_types = list(data_type_map.keys())
    data_types.append("all")

    parser.add_argument("data_type", nargs="+", choices=data_types,
                        help="The type of data to load or all for all data.")

    #Parse
    args = parser.parse_args()

    #If all selected
    if "all" in args.data_type:
        #Forcing skipping appt for b_acadappt
        args.load_appt = False
        #Replace data types with ordered list of all data types
        args.data_type = data_type_map.keys()

    #Load each data type
    for data_type in args.data_type:
        func_args = vars(args).copy()
        args.graph = data_type
        func = data_type_map[data_type]
        #Limit to actual arguments
        remove_extra_args(func_args, func)
        g = func(**func_args)
        process_graph(g, args)
