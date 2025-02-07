#!/usr/bin/env python3

import owlrl
from rdflib import Graph, BNode
from rdflib.namespace import Namespace, RDF
from .bcolors import BColors
from typing import Tuple, List

SEMOPS = Namespace("http://svirgilgood.github.io/semops/onto#")


def inference_validation(data_graph: Graph, test_graph: Graph) -> List[Tuple[bool, str]]:
    owlrl.DeductiveClosure(
        owlrl.OWLRL_Extension,
        rdfs_closure=True,
        axiomatic_triples=True,
        datatype_axioms=True,
        improved_datatypes=True).expand(data_graph)
    inference_result: List[Tuple[bool, str]] = []
    for test_node in test_graph.subjects(predicate=RDF.type, object=SEMOPS.InferenceTest):
        expected_classes = set(list(test_graph.objects(
            subject=test_node, predicate=SEMOPS.expectedClass)))
        inferred_classes = set(filter(lambda x: (type(x) is not BNode), list(data_graph.objects(
            subject=test_node, predicate=RDF.type))))
        is_valid = True
        additional_iclasses = inferred_classes - expected_classes
        if len(additional_iclasses) > 0:
            print("More Classes inferred than expected")
            for aclass in additional_iclasses:
                print(type(aclass))
            is_valid = False
            print(data_graph.query(f"DESCRIBE {test_node.n3()}").serialize(
                format="longturtle").decode("utf-8"))
        missing_inferred_class = expected_classes - inferred_classes
        if len(missing_inferred_class) > 0:
            print("missing inferred class")
            is_valid = False
            print(f"{BColors.WARNING}Missing Inferred Classes{BColors.ENDC}")
            for iclass in missing_inferred_class:
                print(iclass)
        inference_result.append((is_valid, test_node.n3()))
        # print(data_graph.serialize(format="trig"))

    print("End of inference")
    return inference_result
    # print(data_graph.serialize(format="trig"))
