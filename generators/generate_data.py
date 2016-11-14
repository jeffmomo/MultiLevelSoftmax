import os.path

import cv2

from hierarchy import get_hierarchy
from hierarchy.get_hierarchy import *


def generate_data(tree, generate=False):

    tree.prune(threshold=1000)
    # print(tree.get_list())
    defs_lst = []
    tree.get_definitions(defs_lst)
    print(defs_lst)
    print(str(len(defs_lst)))
    print(tree.count_at_node)
    z = []
    tree.build(defs_lst)
    # tree.generate_layer({})

    mapping = {}
    tree.bf_count(mapping)
    print(type(tree.subtrees))
    count = 0

    return

    obs = open('output.csv', 'r')
    classes = set()
    usable_records = open('usables.csv', 'w+')


    for line in obs:
        first_split = line[:-1].split('|_|')

        if len(first_split) < 2:
            print(line)
            continue

        hierarchy = first_split[0].split('_._')[26:34]
        second_split = first_split[1].split('_._')
        if len(second_split) < 2:
            print(line)
        file_name = second_split[2]

        splitted = line[26:34]

        if len(hierarchy) < 8:
            print(line)
            continue

        name, t_rank, kingdom, phylum, cls, order, family, genus = [x.lower() for x in hierarchy]
        if 'species' not in t_rank:
            # print('strange taxonomy definition')
            pass

        duo = name.split()
        if len(duo) > 1:
            species = duo[1]
        else:
            species = duo[0]

        fullname = genus + '.' + species
        if fullname in mapping:
            # print(fullname + ":" + str(mapping[fullname]))
            classes.add(fullname)
            # print(tree.generate_targets(1, [x for x in [kingdom, phylum, cls, order, family, genus, species] if x != ''], 0.5, True))
            c_type = second_split[1].split('/')
            if len(c_type) < 2 or c_type[1] != 'jpeg':
                print('type not jpeg')
                continue


            extname = file_name + '.' + c_type[1]
            fullpath = "../images/" + extname
            label_id = defs_lst.index(genus + '.' + species)
            if label_id < 0:
                print('bad label')

            if os.path.isfile(fullpath) and cv2.imread(fullpath) is not None:
                outstr = ','.join([extname, kingdom, phylum, cls, order, family, genus, species, str(label_id)])
                usable_records.write(outstr + '\n')
                # print(outstr)
                count += 1


            print(count)

    print('eligible records: ' + str(count))
    print('eligible classes: ' + str(len(classes)))
    usable_records.close()

generate_data(get_hierarchy.generate_tree())
