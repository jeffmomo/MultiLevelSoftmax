import collections
import csv
import functools
import os.path
import pickle
from collections import deque
from typing import Dict, List
import json
import os
from tqdm import tqdm
import argparse

from hierarchy import hierarchical_eval
from hierarchy.level_evaluate import LevelNode


class IndexedHashSet(collections.Iterable):

    def __init__(self):
        self._hs = set()
        self._ls = []

    def add(self, item):
        if item not in self._hs:
            self._hs.add(item)
            self._ls.append(item)

    def remove(self, item):
        if item in self._hs:
            self._hs.remove(item)
            self._ls.remove(item)

    def index(self, *args):
        return self._ls.index(*args)

    def __len__(self):
        assert len(self._hs) == len(self._ls), "Data structures not matching"
        return len(self._hs)

    def __iter__(self):
        return iter(self._ls)

    def __contains__(self, item):
        return item in self._hs

    def __getitem__(self, item):
        return self._hs[item]




class TaxonomyTree(object):

    join_character = '.'

    def get_full_name(self):
        return None if self.parent is None else self.parent.name + TaxonomyTree.join_character + self.name

    def children(self):
        if not len(self.subtrees):
            return [self]
        else:
            return functools.reduce(list.__add__, [x.children() for _, x in self.subtrees.items()])

    def backwards(self, current_significance: float, k: float, output: List[float], returned_from: str) -> (float, float, list, str):

        if self.index != -1:
            output[self.index] = current_significance

        for _, v in self.subtrees.items():
            # if v.name == returned_from:
            #     continue

            for child in v.children():
                print(child.index)
                output[child.index] += current_significance * self.count_ratio # normalise towards the smallest count under parent

        return current_significance * k, k, output, self.name

    def forwards(self, max_significance: float, chain: List[str], k: float, size: int) -> (float, float, list, str):
        if not len(chain):
            output = [0] * size
            return self.backwards(max_significance, k, output, self.name)

        head, *rest = chain

        current_significance, k, output, name = self.subtrees[head].forwards(max_significance, rest, k, size)

        return self.backwards(current_significance, k, output, name)

    def generate_targets(self, max_significance: float, chain: List[str], k: float, num_classes: int, normalize=True) -> (float, float, list, str):
        if self.size == -1:
            raise Exception('Tree has not been built yet. run TaxonomyTree.build')

        targets = self.forwards(max_significance, chain, k, num_classes)[2]
        if normalize:
            length = functools.reduce(lambda accum, val: val + accum, targets, 0)
            targets = [x / length for x in targets]
        return targets

    def __init__(self, name):

        self.subtrees = self._make_subtree_dict()
        self.name = name
        self.index = -1
        self.size = -1
        self.depth = -1
        self.count_at_node = 0
        self.parent = None
        self.normalised_scalar_count = 1
        self.count_ratio = 1
        self.join_character = '.'

    @staticmethod
    def _make_subtree_dict() -> Dict[str, 'TaxonomyTree']:
        return collections.OrderedDict()

    def normalise_count(self, my_norm, count_ratio):
        self.normalised_scalar_count = my_norm
        self.count_ratio = count_ratio

        if not len(self.subtrees):
            return

        min_count = functools.reduce(lambda accum, x: x if x < accum else accum, [x.count_at_node for x in self.subtrees.values()], 9999999999)


        for v in self.subtrees.values():
            v.normalise_count(v.count_at_node / self.count_at_node, min_count / v.count_at_node)

    def create_if_not_contain(self, branch_name):

        if branch_name not in self.subtrees:
            new = TaxonomyTree(branch_name)
            new.parent = self
            self.subtrees[branch_name] = new
            return new

        return self.subtrees[branch_name]

    def hierarchy_hashmap(self):
      if not len(self.subtrees):
        return self.name
      # newmap = set()
      # for k, v in self.subtrees.:
      #   newmap[v.get_full_name()] = v.to_hashmap()
      # newmap['count'] = self.count_at_node
      return {v.name: v.hierarchy_hashmap() for k, v in self.subtrees.items()}

    def to_hashmap(self):
        if not len(self.subtrees):
            return {self.get_full_name(): self.count_at_node}
        newmap = {}
        for k, v in self.subtrees.items():
            newmap[v.get_full_name()] = v.to_hashmap()
        newmap['count'] = self.count_at_node
        return newmap


    def create_chain(self, chain: List[str], accepts_incomplete_chain=True) -> None:

        self.count_at_node += 1

        if not len(chain):
            return

        head, *tail = chain

        if head == '':
            self.count_at_node -= 1
            self.create_chain(tail)

            if accepts_incomplete_chain:
                return
            else:
                raise Exception('Bad Chain. Contains empty values')

        if head in self.subtrees:
            self.subtrees[head].create_chain(tail)
        else:
            self.create_if_not_contain(head).create_chain(tail)

    def assign_indices(self, definitions: List[str]) -> None:
        if not len(self.subtrees):
            self.index = definitions.index(self.get_full_name())  # assigns index by fullname
            assert(self.index >= 0)  # make sure the name actually exists in the index
        else:
            for k, v in self.subtrees.items():
                v.assign_indices(definitions)

    def generate_reverse_tree(self, mapping, leaf_only=True):

        if not len(self.subtrees) or (not leaf_only and self.get_full_name() is not None):
            entry = []

            parent = self
            while parent.parent is not None:
                entry.append(parent.get_full_name())
                parent = parent.parent

            mapping[self.get_full_name()] = entry

            # if not len(self.subtrees):
            #     return


        for v in self.subtrees.values():
            v.generate_reverse_tree(mapping, leaf_only)

    def get_tree_index_mappings(self):
        """
        Gets the definitions lists and index mappings for the current hierarchy tree.

        :return: Returns a tuple of definitions lists and index mappings
        """
        definitions_lists = []
        index_mappings = []


        assert self.parent is None, "Has to be executed on base tree"

        self.tree_index_mappings(definitions_lists, index_mappings)

        return definitions_lists[1:], index_mappings[:-1]



    def tree_index_mappings(self, definitions_lists, index_mappings, depth = 0):

        if len(definitions_lists) <= depth:
            definitions_lists.append([])
            index_mappings.append([])

        definitions_lists[depth].append(self.get_full_name())

        if depth > 0:  # assumes if depth > 0, then the current node has a parent.
            index_mappings[depth - 1].append(definitions_lists[depth - 1].index(self.parent.get_full_name()))

        for item in self.subtrees.values():
            item.tree_index_mappings(definitions_lists, index_mappings, depth + 1)


    # def get_index_mappings(self):
    #
    #     # definitions_lists = []
    #     # index_mappings = []
    #     #
    #     # reverse_tree = collections.OrderedDict()  # to make a linked hash map with predictable iteration
    #     # self.generate_reverse_tree(reverse_tree)
    #     #
    #     # max_len = len(next(iter(reverse_tree.values())))  # assumes uniform lengths for trees
    #     #
    #     # for i in range(max_len):
    #     #     definitions_lists.append(IndexedHashSet())
    #     #     index_mappings.append([])
    #     #
    #     # for v in reverse_tree.values():
    #     #     idx = 0
    #     #     for name in reversed(v):
    #     #         definitions_lists[idx].add(name)
    #     #         if idx > 0:
    #     #             index_mappings[idx - 1]
    #     #         idx += 1
    #     #
    #     #
    #     #
    #     #
    #     #
    #     #
    #     # return definitions_lists, mappings





    def leaves(self) -> list:
        if not len(self.subtrees):
            return [self]
        else:
            return functools.reduce(list.__add__, [x.leaves() for _, x in self.subtrees.items()])

    def build(self, definitions: List[str], normalise_count=False) -> None:
        self.assign_indices(definitions)
        self.size = len(self.leaves())
        if normalise_count:
            self.normalise_count(1)

    def get_list(self):
        if not len(self.subtrees):
            return self.name
        else:
            return [x.get_list() for _, x in self.subtrees.items()]


    def get_layer_mappings(self):
        output = []

    def get_subtree_by_name(self, name):
        """
        Gets a subtree using a name
        :param name: The single name (i.e. 'animalia')
        :return: Returns a TaxonomyTree, or None if the name is not found.
        """
        lower_name = name.lower()
        queue = [self]

        while len(queue):
            frontier = queue.pop()
            if frontier.name.lower() == lower_name:
                return frontier

            for child in frontier.subtrees.values():
                queue.insert(0, child)

        return None


    ### Gets all the leaf/all nodes of the hierarchy
    def get_definitions(self, definitions, leaf_only=True, offset_by_one=False):

        if not len(self.subtrees):
            definitions.append(self.get_full_name())
        else:
            if not leaf_only and self.parent is not None:
                definitions.append(self.get_full_name())

            for k, v in self.subtrees.items():
                v.get_definitions(definitions, leaf_only)

    def _prune_by_names(self, names_to_keep):

        # z = self._make_subtree_dict()
        # z.

        if not len(self.subtrees):
            # if self.name == 'gorilla':
            #     print(self.get_full_name())
            #     pass
            if self.get_full_name() not in names_to_keep:
                # del self.parent.subtrees[self.name]
                return self.name
            else:
                names_to_keep.remove(self.get_full_name())
                return None

        to_delete = []
        for v in self.subtrees.values():
            name = v._prune_by_names(names_to_keep)
            if name:
                to_delete.append(name)

        for val in to_delete:
            del self.subtrees[val]

        if not len(self.subtrees):
            return self.name
        else:
            return None

    def prune_by_names(self, names_to_keep):

        assert self.parent is None, "Must be performed at root node"

        self._prune_by_names(names_to_keep)
        # now remove the empty branches.
        self.prune(threshold=1)

        assert len(names_to_keep) == 0, "Some names are not found"
        return names_to_keep

    def prune(self, threshold=100):
        if not len(self.subtrees):
            return

        to_remove = []
        for k, v in self.subtrees.items():
            if v.count_at_node < threshold:
                to_remove.append(k)  # remove node
            else:
                v.prune(threshold)
                if v.count_at_node < threshold:
                    to_remove.append(k)

        for item in to_remove:
            del self.subtrees[item]

        # recount
        self.count_at_node = functools.reduce(int.__add__, [v.count_at_node for v in self.subtrees.values()], 0)

    def generate_leaf_indices(self):

        leaves = []
        self.get_definitions(leaves)

        all_nodes = ['__BACKGROUND__']
        self.get_definitions(all_nodes, False)

        output = set()
        for leaf in leaves:
            output.add(all_nodes.index(leaf))

        return output

    def generate_level_nodes(self, label_list: List[str]) -> LevelNode:

        child_nodes = [x.generate_level_nodes(label_list) for x in self.subtrees.values()]
        root_node = LevelNode(-1 if self.get_full_name() is None else label_list.index(self.get_full_name()), child_nodes)

        return root_node

    def generate_layer(self, mapping: Dict[str, int]) -> (hierarchical_eval.Layer, str):
        if not len(self.subtrees):
            return (self.index, self.name)
        else:
            lst = []
            idx = 0

            # Precondition - all members of hierarchy
            # (either leaves or non-leaves) must have different name
            for k, v in self.subtrees.items():
                lst.append(v.generate_layer(mapping))
                compound = self.name + self.join_character + k
                if compound in mapping:
                    print('Duplicate naming: ' + compound)
                mapping[compound] = idx
                idx += 1

            assert all([type(x) == type(lst[0]) for x in lst])

            return (hierarchical_eval.Layer(lst, self.get_full_name()), self.name)

    def __str__(self):
        return self.name

    def _assign_depth(self, depth):
        self.depth = depth
        for v in self.subtrees.values():
            v._assign_depth(depth + 1)

    def check_depth(self, leaf_depth):
        assert self.parent is None, "Must execute on root"
        self._assign_depth(-1)
        assert all([x.depth == leaf_depth for x in self.children()])
        return True

    def bf_count(self, mapping=None):
        current_count = 0
        done_count = 0
        total_count = 0
        queue = deque()
        for k, v in self.subtrees.items():
            queue.append(v)
            total_count += 1

        done_count = total_count

        out_str = ''

        while len(queue):

            if current_count == done_count:
                print(out_str + '\n\n')
                out_str = ''
                done_count = total_count

            head = queue.popleft()
            out_str += head.name + ': ' + str(head.count_at_node) + ', '

            if mapping is not None:
                mapping[head.get_full_name()] = head.count_at_node

            current_count += 1

            for k, v in head.subtrees.items():
                queue.append(v)
                total_count += 1

        print(out_str)


# def process():
#


def get_chain_by_name(chain, mapping):
    return [mapping[x] for x in chain]


# def filter_bad_names(name):
#     a, b = name.split('.')
#     return a != '' and b != ''
#
# def get_valid_labels(tree, threshold):
#     tree.prune(threshold)
#     defs_list = []
#     tree.get_definitions(defs_list)
#
#     return filter(filter_bad_names, defs_list)





def generate_tree(nz_only=False):

    skipped_count = 0

    if os.path.isfile('hierarchy_file.dat'):
        t = pickle.load(open('hierarchy_file.dat', 'rb'))
    else:
        t = TaxonomyTree('init')
        f = open(os.path.expanduser('~/observations.csv'), 'r')
        count = 0
        csv_file = csv.DictReader(f, delimiter=',', quotechar='"')
        for row in tqdm(csv_file):
            is_NZ = row['countryCode'] == "NZ"

            if nz_only and not is_NZ:
                continue

            taxo_names = [
                    row['scientificName'],
                    row['taxonRank'],
                    row['kingdom'],
                    row['phylum'],
                    row['class'],
                    row['order'],
                    row['family'],
                    row['genus'],
                ]

            name, t_rank, kingdom, phylum, cls, order, family, genus = taxo_names

            if not all(taxo_names):
                # print('gap in hierarchy: ' + ', '.join(taxo_names), end='\r')
                skipped_count += 1
                continue

            if 'species' not in t_rank:
                # print('strange taxonomy definition', t_rank, end='\r')
                skipped_count += 1
                continue

            duo = name.split()
            if len(duo) > 1:
                species = duo[1]
            else:
                species = duo[0]
            t.create_chain([kingdom, phylum, cls, order, family, genus, species])

            count += 1
            # print(species + ' added')
        pickle.dump(t, open('hierarchy_file.dat', 'wb+'), pickle.HIGHEST_PROTOCOL)
        print('Skipped: ' + str(skipped_count))

    return t


# test()
# generate_data(generate_tree())

def native_to_hierarchical_translation_map(tree: TaxonomyTree, labels_path: str):
    native = get_20k_label_mappings(labels_path)
    hierarchical = []
    tree.get_definitions(hierarchical)
    mapping = []
    for name in native:
        mapping.append(hierarchical.index(name))

    return mapping


def hierarchical_to_native_translation_map(tree: TaxonomyTree, labels_path: str):
    native = get_20k_label_mappings(labels_path)
    hierarchical = []
    tree.get_definitions(hierarchical)
    mapping = []
    for name in hierarchical:
        mapping.append(native.index(name))

    return mapping



def translate_to_level(index_mappings, level_from_root, index):
    level_from_leaf = len(index_mappings) - level_from_root
    current_idx = index

    for i in range(1, level_from_leaf):
        current_idx = index_mappings[-i][current_idx]

    assert current_idx < len(index_mappings[-level_from_leaf]), "Invalid index"
    return current_idx

def get_20k_label_mappings(labels_path):
    f = open(labels_path)
    names = []
    for line in f:
        splitted = line.split(":")
        name = splitted[1][:-1]
        names.append(name)

    return names

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--labels', help='Where to load labels txt file from')
    args = parser.parse_args()

    t = generate_tree()
    t.prune(threshold=5)
    t.prune_by_names(get_20k_label_mappings(args.labels))

    pruned_tree = t

    # print(t.hierarchy_hashmap())

    def_l, i_m = t.get_tree_index_mappings()
    s = set()

    # print(json.dumps(t.to_hashmap()))


    # print((def_l))
    # print(len(t.children()))
    #
    # for i in t.children(): s.add(i.get_full_name())
    # for i in get_20k_label_mappings(): s.remove(i)
    # # bads = []
    # # for item in t.children():
    # #     if item.get_full_name() in s:
    # #         bads.append(item)
    # #         print(item.count_at_node)
    # #         print(item.subtrees)
    # # print(bads)
    # print(s)

def check_tree(labels_path):
    print(t.check_depth(leaf_depth=6))

    nm = native_to_hierarchical_translation_map(t, labels_path)
    hm = hierarchical_to_native_translation_map(t, labels_path)

    assert all([x == hm[nm[x]] and x == nm[hm[x]] for x in range(0, len(nm))]) and len(nm) == len(hm), "Mapping not well defined"

def do_plots():
    from matplotlib import pyplot
    import numpy as np

    counts = sorted([x.count_at_node for x in t.children()])

    n, bins, patches = pyplot.hist(counts, 6300 // 20)
    pyplot.xlabel('Number of images per class')
    pyplot.ylabel('Number of classes')
    # pyplot.plot(n)
    pyplot.show()
    print('z')
    print(n)
    print('zz')

    BIN_SIZE = 5
    total = t.count_at_node
    num_bins = int(6300 / BIN_SIZE)
    bins = [0] * num_bins

    # plots the cumulative fraction against number-of-images-in-a-class
    for count in counts:
        bins[int(count / BIN_SIZE)] += count

    cumulative = 0
    for i in range(0, len(bins)):
        cumulative += bins[i]
        bins[i] = cumulative / total
    print(bins)
    pyplot.plot(range(0, (num_bins) * BIN_SIZE, BIN_SIZE), bins)
    pyplot.xlabel('Number of images per class')
    pyplot.ylabel('Cumulative fraction of total dataset represented')
    pyplot.show()

# do_plots()
# print((i_m))
#
# print(translate_to_level(i_m, 0, 2061))
