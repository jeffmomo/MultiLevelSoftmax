import csv
import pickle
import hierarchical_eval
import functools


class TaxonomyTree(object):

    def children(self):
        if not len(self.subtrees):
            return [self]
        else:
            return functools.reduce(list.__add__, [x.children() for _, x in self.subtrees.items()])

    def backwards(self, current_significance, k, output, returned_from):

        if self.index != -1:
            output[self.index] = current_significance

        for _, v in self.subtrees.items():
            if v.name == returned_from:
                continue

            for child in v.children():
                output[child.index] += current_significance

        return current_significance * k, k, output, self.name

    def forwards(self, max_significance, chain, k, size):
        if not len(chain):
            output = [0] * size

            # children = self.children()
            # if not len(children):
            #     output[self.index] = max_significance # may need to account for additional shit added on.
            # else:
            #     for child in children:
            #         output[child.index] = max_significance

            return self.backwards(max_significance, k, output, self.name)

        head, *rest = chain

        current_significance, k, output, name = self.subtrees[head].forwards(max_significance, rest, k, size)

        return self.backwards(current_significance, k, output, name)

    def generate_targets(self, max_significance, chain, k):
        return self.forwards(max_significance, chain, k, self.size)


    def __init__(self, name):
        self.subtrees = dict()
        self.name = name
        self.index = -1
        self.size = 0

    def create_if_not_contain(self, branch_name):

        if branch_name not in self.subtrees:
            new = TaxonomyTree(branch_name)
            self.subtrees[branch_name] = new
            return new

        return self.subtrees[branch_name]

    def create_chain(self, chain):
        if not len(chain):
            return

        head, *tail = chain
        if head in self.subtrees:
            self.subtrees[head].create_chain(tail)
        else:
            self.create_if_not_contain(head).create_chain(tail)

    def assign_indices(self, definitions):
        if not len(self.subtrees):
            self.index = definitions.index(self.name)  # assigns index by name
        else:
            for k, v in self.subtrees.items():
                v.assign_indices(definitions)

    def get_size(self):
        if not len(self.subtrees):
            return 1
        else:
            return functools.reduce(int.__add__, [x.get_size() for _, x in self.subtrees.items()])

    def build(self, definitions):
        self.assign_indices(definitions)
        self.size = self.get_size()

    def get_list(self):
        if not len(self.subtrees):
            return self.name
        else:
            return [x.get_list() for _, x in self.subtrees.items()]

    def generate_layer(self):
        if not len(self.subtrees):
            return self.index
        else:
            lst = [v.generate_layer() for k, v in self.subtrees.items()]
            return hierarchical_eval.Layer(lst)
            # if type(lst[0]) == hierarchical_eval.Layer:
            #     return hierarchical_eval.Layer(lst)
            # else:
            #     return lst


    def __str__(self):
        return self.name


def test():
    tt = TaxonomyTree('init')
    tt.create_chain([ 'ab', 'a'])
    tt.create_chain([ 'ab', 'b'])
    tt.create_chain(['cc', 'c'])
    tt.create_chain([ 'de', 'd'])
    tt.create_chain(['de', 'e'])
    # tt.create_chain(['a', 'f', 'i'])

    print(tt.get_list())

    tt.build(['a', 'b', 'c', 'd', 'e'])

    fw = tt.generate_targets(1, ['cc', 'c'], 0.5)
    print(fw)

    lr = tt.generate_layer()
    print(lr.evaluate([0.2, 0.4, 0.4, 0.1, 0.5]))


def generate_tree():

    t = TaxonomyTree('init')
    f = open('observations.csv', 'r')
    count = 0
    # gets rid of headers
    f.readline()
    csv_file = csv.reader(f, delimiter=',', quotechar='"')
    for line in csv_file:
        splitted = line[26:34]
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
        print(species + ' added')
        print(count)

    pickle.dump(t, open('hierarchy_file.dat', 'wb+'), pickle.HIGHEST_PROTOCOL)


test()
