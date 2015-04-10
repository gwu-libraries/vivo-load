from lyterati_entity import *
import argparse
from rdflib.compare import graph_diff
from sparql import load_previous_graph, sparql_load, sparql_delete, serialize
import lyterati_load
import banner_load
import inspect
from collections import OrderedDict


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

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--limit", type=int, help="Limit to number of rows from csv to load.")

    subparsers = parser.add_subparsers(dest="graph")

    fac_parser = argparse.ArgumentParser(add_help=False)
    fac_parser.add_argument("--faculty-limit", type=int, help="Limit to number of faculty to load.", dest="fac_limit")
    non_fac_parser = argparse.ArgumentParser(add_help=False)
    non_fac_parser.add_argument("--non-faculty-limit", type=int, help="Limit to number of non-faculty to load.",
                                dest="non_fac_limit")

    faculty_parser = subparsers.add_parser("l_faculty", parents=[parent_parser, fac_parser])
    faculty_parser.add_argument("--skip-vcards", action="store_false", dest="load_vcards")
    faculty_parser.add_argument("--skip-departments", action="store_false", dest="load_departments")
    faculty_parser.add_argument("--skip-persons", action="store_false", dest="load_persons")
    faculty_parser.set_defaults(func=lyterati_load.load_faculty)

    academic_appointment_parser = subparsers.add_parser("l_academic_appointment",
                                                        parents=[parent_parser, fac_parser])
    academic_appointment_parser.set_defaults(func=lyterati_load.load_academic_appointment)

    admin_appointment_parser = subparsers.add_parser("l_admin_appointment", parents=[parent_parser, fac_parser])
    admin_appointment_parser.set_defaults(func=lyterati_load.load_admin_appointment)

    research_parser = subparsers.add_parser("l_research", parents=[parent_parser, fac_parser])
    research_parser.add_argument("--contribution-type-limit", type=int, help="Number of research entities to load.")
    research_parser.add_argument("--research-groups", nargs="+", dest="research_group_codes")
    research_parser.add_argument("--contribution-types", nargs="+", dest="contribution_type_codes")
    research_parser.set_defaults(func=lyterati_load.load_research)

    education_parser = subparsers.add_parser("l_education", parents=[parent_parser, fac_parser])
    education_parser.add_argument("--degree-type-limit", type=int, help="Number of education entities to load.")
    education_parser.add_argument("--degree-types", nargs="+", dest="degree_types")
    education_parser.set_defaults(func=lyterati_load.load_education)

    courses_parser = subparsers.add_parser("l_courses", parents=[parent_parser, fac_parser])
    courses_parser.set_defaults(func=lyterati_load.load_courses)

    service_parser = subparsers.add_parser("l_service", parents=[parent_parser, fac_parser])
    service_parser.add_argument("--service-type-limit", type=int, help="Number of service entities to load.")
    service_parser.add_argument("--service-groups", nargs="+", dest="service_group_codes")
    service_parser.set_defaults(func=lyterati_load.load_service)

    orgn_parser = subparsers.add_parser("b_organization", parents=[parent_parser])
    orgn_parser.set_defaults(func=banner_load.load_orgn)

    college_parser = subparsers.add_parser("b_college", parents=[parent_parser])
    college_parser.set_defaults(func=banner_load.load_college)

    depart_parser = subparsers.add_parser("b_department", parents=[parent_parser])
    depart_parser.set_defaults(func=banner_load.load_depart)

    demographic_parser = subparsers.add_parser("b_demographic", parents=[parent_parser, fac_parser, non_fac_parser])
    demographic_parser.set_defaults(func=banner_load.load_demographic)

    emplappt_parser = subparsers.add_parser("b_emplappt", parents=[parent_parser, non_fac_parser])
    emplappt_parser.set_defaults(func=banner_load.load_emplappt)

    acadappt_parser = subparsers.add_parser("b_acadappt", parents=[parent_parser, fac_parser])
    acadappt_parser.add_argument("--skip-appt", action="store_false", dest="load_appt",
                                 help="Skip loading the academic appointment for the faculty.")

    acadappt_parser.set_defaults(func=banner_load.load_acadappt)

    banner_courses_parser = subparsers.add_parser("b_courses", parents=[parent_parser, fac_parser])
    banner_courses_parser.set_defaults(func=banner_load.load_courses)

    all_parser = subparsers.add_parser("all", parents=[fac_parser, non_fac_parser])

    #Create map of parsers to names for use by load_all
    subparser_map = {}
    for name, subparser in subparsers.choices.items():
        subparser_map[subparser] = name

    #Parse
    args = parser.parse_args()
    func_args = vars(args).copy()

    #Remove extraneous args
    del func_args["graph"]
    del func_args["perform_load"]
    del func_args["perform_diff"]
    del func_args["perform_serialize"]
    del func_args["htdocs_dir"]
    del func_args["graph_dir"]
    del func_args["split_size"]
    del func_args["delete_split_size"]
    del func_args["username"]
    del func_args["password"]
    del func_args["endpoint"]
    del func_args["print_triples"]
    if "func" in func_args:
        del func_args["func"]

    #Map of function to map of (extra func args, graph name or none)
    #This allows for providing additional arguments and setting the graph name in load_all
    #Load all is special
    if args.graph == "all":
        funcs = OrderedDict([
            (banner_load.load_demographic, ({}, subparser_map[demographic_parser])),
            (banner_load.load_orgn, ({}, subparser_map[orgn_parser])),
            (banner_load.load_emplappt, ({}, subparser_map[emplappt_parser])),
            (banner_load.load_acadappt, ({ "skip_appt": True}, subparser_map[acadappt_parser])),
            (lyterati_load.load_faculty, ({}, subparser_map[faculty_parser])),
            (lyterati_load.load_academic_appointment, ({}, subparser_map[academic_appointment_parser])),
            (lyterati_load.load_admin_appointment, ({}, subparser_map[admin_appointment_parser])),
            (lyterati_load.load_research, ({}, subparser_map[research_parser])),
            (lyterati_load.load_education, ({}, subparser_map[education_parser])),
            (lyterati_load.load_courses, ({}, subparser_map[courses_parser])),
            (lyterati_load.load_service, ({}, subparser_map[service_parser]))
        ])
    else:
        funcs = { args.func: ({}, None)}
        
    for func, (extra_func_args, graph) in funcs.items():
        if graph:
            args.graph = graph
        merge_func_args = func_args.copy()
        if extra_func_args:
            merge_func_args.update(extra_func_args)
        #Limit to actual arguments (needed for load_all)
        keys = list(merge_func_args.keys())
        (arg_names, varargs, keywords, defaults) = inspect.getargspec(func)
        for key in keys:
            if key not in arg_names:
                del merge_func_args[key]
        g = func(**merge_func_args)
        process_graph(g, args)
