import csv
import pickle
import hierarchical_eval
import functools
from typing import List, Dict
from collections import deque
import os.path
import cv2


class TaxonomyTree(object):

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
                output[child.index] += current_significance * self.normalised_scalar_count

        return current_significance * k, k, output, self.name

    def forwards(self, max_significance: float, chain: List[str], k: float, size: int) -> (float, float, list, str):
        if not len(chain):
            output = [0] * size
            return self.backwards(max_significance, k, output, self.name)

        head, *rest = chain

        current_significance, k, output, name = self.subtrees[head].forwards(max_significance, rest, k, size)

        return self.backwards(current_significance, k, output, name)

    def generate_targets(self, max_significance: float, chain: List[str], k: float, normalize=True) -> (float, float, list, str):
        if self.size == -1:
            raise Exception('Tree has not been built yet. run TaxonomyTree.build')

        targets = self.forwards(max_significance, chain, k, self.size)[2]
        if normalize:
            length = functools.reduce(lambda accum, val: val ** 2 + accum, targets, 0) ** 0.5
            targets = [x / length for x in targets]
        return targets

    def __init__(self, name):

        self.subtrees = dict()
        self.name = name
        self.index = -1
        self.size = -1
        self.count_at_node = 0
        self.parent = None
        self.normalised_scalar_count = 1

    def normalise_count(self, my_norm):
        if not len(self.subtrees):
            return

        self.normalised_scalar_count = my_norm

        for v in self.subtrees.values():
            v.normalise_count(v.count_at_node / self.count_at_node)

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
            self.index = definitions.index(self.parent.name + '-' + self.name)  # assigns index by fullname
            assert(self.index >= 0)  # make sure the name actually exists in the index
        else:
            for k, v in self.subtrees.items():
                v.assign_indices(definitions)

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

    ### Gets all the leaf nodes of the hierarchy
    def get_definitions(self, definitions=[]):
        if not len(self.subtrees):
            definitions.append(self.parent.name + '-' + self.name)
        else:
            for k, v in self.subtrees.items():
                v.get_definitions(definitions)

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

    def generate_layer(self, mapping: Dict[str, int]) -> hierarchical_eval.Layer:
        if not len(self.subtrees):
            return self.index
        else:
            lst = []
            idx = 0

            # Precondition - all members of hierarchy
            # (either leaves or non-leaves) must have different name
            for k, v in self.subtrees.items():
                lst.append(v.generate_layer(mapping))
                compound = self.name + '-' + k
                if compound in mapping:
                    print('Duplicate naming: ' + compound)
                mapping[compound] = idx
                idx += 1

            return hierarchical_eval.Layer(lst)

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
                mapping[head.parent.name + '-' + head.name] = head.count_at_node

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





def generate_tree():

    if os.path.isfile('hierarchy_file.dat'):
        t = pickle.load(open('hierarchy_file.dat', 'rb'))
    else:
        t = TaxonomyTree('init')
        f = open('observations.csv', 'r')
        count = 0
        # gets rid of headers
        f.readline()
        csv_file = csv.reader(f, delimiter=',', quotechar='"')
        for line in csv_file:
            splitted = line[26:34]

            if any([True for x in splitted if x == '']):
                print('gap in hierarchy: ' + ', '.join(splitted))
                # continue

            name, t_rank, kingdom, phylum, cls, order, family, genus = [x.lower() for x in splitted]
            if 'species' not in t_rank:
                print('strange taxonomy definition')

            duo = name.split()
            if len(duo) > 1:
                species = duo[1]
            else:
                species = duo[0]
            t.create_chain([kingdom, phylum, cls, order, family, genus, species])

            count += 1
            # print(species + ' added')
            # print(count)
        pickle.dump(t, open('hierarchy_file.dat', 'wb+'), pickle.HIGHEST_PROTOCOL)

    return t


# test()
# generate_data(generate_tree())



