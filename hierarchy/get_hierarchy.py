import collections
import csv
import functools
import os.path
import pickle
from collections import deque
from typing import Dict, List

from hierarchy import hierarchical_eval
from hierarchy.level_evaluate import LevelNode


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
        self.count_at_node = 0
        self.parent = None
        self.normalised_scalar_count = 1
        self.count_ratio = 1
        self.join_character = '.'

    def _make_subtree_dict(self) -> Dict[str, 'TaxonomyTree']:
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

        # if not len(self.subtrees):
        #     entry = []
        #
        #     parent = self
        #     while parent.parent is not None:
        #         entry.append(parent.get_full_name())
        #         parent = parent.parent
        #
        #     mapping[self.get_full_name()] = entry
        #     return

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

    ### Gets all the leaf/all nodes of the hierarchy
    def get_definitions(self, definitions, leaf_only=True, offset_by_one=False):

        if not len(self.subtrees):
            definitions.append(self.get_full_name())
        else:
            if not leaf_only and self.parent is not None:
                definitions.append(self.get_full_name())

            for k, v in self.subtrees.items():
                v.get_definitions(definitions, leaf_only)

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

def test():
    tt = TaxonomyTree('init')

    tt.create_chain(['ab', 'a'])
    tt.create_chain(['ab', 'b'])
    tt.create_chain(['cc', 'c'])
    tt.create_chain(['de', 'd'])
    tt.create_chain(['de', 'e'])
    # tt.create_chain(['a', 'f', 'i'])

    print(tt.get_list())

    tt.build(['a', 'b', 'c', 'd', 'e'])

    fw = tt.generate_targets(1, ['cc', 'c'], 0.5)
    print(fw)

    mapping = {}
    lr = tt.generate_layer(mapping)
    print(lr.evaluateWithPrior(get_chain_by_name(['de'], mapping), [0.2, 0.4, 0.4, 0.1, 0.5]))

    tt.bf_count()


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
        f = open('/home/dm116/Workspace/MultiLevelSoftmax/observations.csv', 'r')
        count = 0
        # gets rid of headers
        f.readline()
        csv_file = csv.reader(f, delimiter=',', quotechar='"')
        for line in csv_file:
            is_NZ = line[21] == "NZ"

            if nz_only and not is_NZ:
                continue
                
            splitted = line[26:34]

            if any([True for x in splitted if x == '']):
                print('gap in hierarchy: ' + ', '.join(splitted))
                skipped_count += 1
                continue

            name, t_rank, kingdom, phylum, cls, order, family, genus = [x.lower() for x in splitted]
            if 'species' not in t_rank:
                print('strange taxonomy definition')
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
