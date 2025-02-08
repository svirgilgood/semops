#!/usr/bin/evn python3

from rdflib import Graph
from rdflib.exceptions import ParserError
import os
from . import shacl_validate
from . import query_validation
from . import owl_inference
from .bcolors import BColors
from typing import List
import sys


def import_rdf(path_item: str, graph: Graph) -> Graph:
    if os.path.isdir(path_item):
        for item in os.listdir(path_item):
            graph = import_rdf(os.path.join(path_item, item), graph)
        return graph
    if os.path.isfile(path_item):
        try:
            graph.parse(path_item)
        except ParserError as error:
            print(error)
        return graph
    print(f"Path Item is not a file or directory: {path_item}")
    return graph


def validation_formatting(is_valid: bool, name: str, results: List[str]) -> List[str]:
    validation_result = f"{BColors.OKGREEN}ok{BColors.ENDC}"
    if not is_valid:
        validation_result = f"{BColors.FAIL}ERROR{BColors.ENDC}"
    results.append(f"{name} .... {validation_result}")
    return results


def main():
    """Import and infer triples"""

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data", nargs="+",
                        help="Point to the different rdf files or directory for the data to validate and test.")
    parser.add_argument('-s', "--shape", nargs="*", help="")
    parser.add_argument('-q', "--query-directory", nargs="*",
                        help="the directory that contains the sparql query files.")
    parser.add_argument('-t', '--test-data', nargs="*",
                        help="Directory or files which contains rdf files that contain test data.")
    parser.add_argument("--shacl-validate",
                        action="store_true", help="run shacl validation")
    parser.add_argument("--query-validate", action="store_true",
                        help="run queries to validate shacl")
    parser.add_argument("--run-inference", action="store_true",
                        help="run inference on data files")
    parser.add_argument("-a", '--all', action="store_true",
                        help="run all of the validation checks: inference, queries, and shacl shapes")

    args = parser.parse_args()

    data_graph = Graph()
    shape_graph = Graph()

    results: List[str] = []

    is_valid = True

    for d_files in args.data:
        data_graph = import_rdf(d_files, data_graph)

    if args.shape:
        for s_files in args.shape:
            shape_graph = import_rdf(s_files, shape_graph)

    if args.shacl_validate or args.all:
        isConforming, result_graph = shacl_validate.validate(
            data_graph, shape_graph)
        validation_result = f"{BColors.OKGREEN}ok{BColors.ENDC}"
        if not isConforming:
            print(f"{BColors.FAIL}SHACL Errors{BColors.ENDC}\n",
                  result_graph.serialize(format="longturtle"))
            validation_result = f"{BColors.FAIL}ERROR{BColors.ENDC}"
            is_valid = False

        results.append(
            f"SHACL Validation run .... {validation_result}"
        )
    combined_graph = data_graph + shape_graph

    if args.query_validate or args.all:
        for query_dir in args.query_directory:
            q_validation_results = query_validation.validate(
                query_dir, combined_graph)
            for valid, name in q_validation_results:
                results = validation_formatting(
                    valid, f"Query {name}", results)
                if not valid:
                    is_valid = False

    if args.run_inference or args.all and args.test_data:
        if not args.test_data:
            print(f"{BColors.WARNING}No test data specified{BColors.ENDC}")
            pass
        test_data = Graph()
        for dir in args.test_data:
            test_data = import_rdf(dir, test_data)
        new_graph = combined_graph + test_data
        for valid, name in owl_inference.inference_validation(new_graph, test_data):
            print(name)
            results = validation_formatting(
                valid, f"Inference for {name}", results)
            if not valid:
                is_valid = False

    for res in results:
        print(res)

    if not is_valid:
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    main()
