import math
import os
import sys
import argparse
from hierarchy import hierarchical_eval, get_hierarchy


class HierarchyProcessor:
    def __init__(self, label_path, hierarchy_dat_path):

        tree = get_hierarchy.generate_tree(hierarchy_file=hierarchy_dat_path)
        tree.prune(threshold=5)
        tree.prune_by_names(get_hierarchy.get_20k_label_mappings(label_path))

        definitions_list = []
        tree.get_definitions(definitions_list)
        print("def list len", len(definitions_list))

        tree.assign_indices(definitions_list)

        mapping = {}
        layer, _ = tree.generate_layer(mapping)
        print("map size", len(mapping))

        reverse_tree = {}
        tree.generate_reverse_tree(reverse_tree, leaf_only=False)

        self.label_map = get_hierarchy.native_to_hierarchical_translation_map(
            tree, label_path
        )
        self.evaluator = hierarchical_eval.LayerEvaluator(layer, definitions_list)
        self.definitions_list = definitions_list
        self.tree = tree
        self.mapping = mapping
        self.mapping_layer = layer

    def compute(self, probs, priors=""):

        print(len(probs), len(self.definitions_list))

        translated_probs = [0] * len(probs)

        # Translate labels here
        for i in range(len(probs)):
            translated_probs[self.label_map[i]] = probs[i]

        top5 = [
            {"name": definitions_list[x[0]], "probability": x[1]}
            for x in sorted(enumerate(translated_probs), key=lambda x: -x[1])[:5]
        ]

        print(top5)

        canonical_priors = priors.replace(" ", ".").lower()
        print(canonical_priors)
        if canonical_priors in self.reverse_tree:
            tmp_evaluator = hierarchical_eval.LayerEvaluator(
                self.mapping_layer,
                definitions_list,
                self.reverse_tree[canonical_priors][::-1],
            )

            top_prob, top_name = tmp_evaluator.dijkstra_top(translated_probs)
            thresh_prob, thresh_name, thresh_depth = tmp_evaluator.dijkstra_threshold(
                translated_probs, 0.707
            )
        else:
            top_prob, top_name = evaluator.dijkstra_top(translated_probs)
            thresh_prob, thresh_name, thresh_depth = evaluator.dijkstra_threshold(
                translated_probs, 0.707
            )

        print(definitions_list[translated_probs.index(max(translated_probs))])

        return (
            {"name": top_name, "probability": top_prob},
            {"name": thresh_name, "probability": thresh_prob},
            top5,
        )

        # need to return top prob, name, and thresh prob, name ,and top5s

