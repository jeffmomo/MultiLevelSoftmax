import csv
import pickle


class TaxonomyTree(object):



    def __init__(self, name):
        self.subtrees = dict()
        self.name = name


    def create_if_not_contain(self, branch_name):

        if branch_name not in self.subtrees:
            new = TaxonomyTree(branch_name)
            self.subtrees[branch_name] = new
            return new

        return self.subtrees[branch_name]

    def create_chain(self, chain):

        if not len(chain):
            return

        branch = chain[0]

        if branch in self.subtrees:
            self.subtrees[branch].create_chain(chain[1:])
        else:
            self.create_if_not_contain(branch).create_chain(chain[1:])

    # def __hash__(self):
    #     return hash(self.name)
    #
    # def __eq__(self, other):
    #     return self.name == other.name


    def __str__(self):
        return self.name


    #
    # def __str__(self):
    #     out = self.itemlist()
    #     for k, v in self.subtrees.items():
    #
    #
    # def itemlist(self):
    #     out = ""
    #     for k, v in self.subtrees.items():
    #         out += k + " "
    #     return out
    #


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


