import os.path
import random
from subprocess import call

from hierarchy import get_hierarchy
from hierarchy.get_hierarchy import *


def generate_data(tree, generate=False):

    produced_files = set()
    already_produced_count = 0


    tree.prune(threshold=100)
    # print(tree.get_list())
    defs_lst = []
    tree.get_definitions(defs_lst, leaf_only=False)
    print(defs_lst)
    print(str(len(defs_lst)))
    print(tree.count_at_node)
    tree.build(defs_lst)

    mapping = {}
    tree.bf_count(mapping)
    count = 0


    obs = open('output.csv', 'r')
    classes = set()

    if not os.path.exists('generated/train'):
        os.mkdir('generated/train')
    if not os.path.exists('generated/validation'):
        os.mkdir('generated/validation')

    for label in defs_lst:
        if not os.path.exists('generated/train/' + label):
            os.mkdir('generated/train/' + label)
            os.mkdir('generated/validation/' + label)


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

        if file_name in produced_files:
            print('already produced', already_produced_count)
            already_produced_count += 1
            continue
        else:
            produced_files.add(file_name)

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

        fullname = genus + tree.join_character + species
        if fullname in defs_lst:
            # print(fullname + ":" + str(mapping[fullname]))
            classes.add(fullname)
            # print(tree.generate_targets(1, [x for x in [kingdom, phylum, cls, order, family, genus, species] if x != ''], 0.5, True))
            c_type = second_split[1].split('/')
            if len(c_type) < 2 or c_type[1] != 'jpeg':
                print('type not jpeg')
                continue


            extname = file_name + '.' + c_type[1]
            fullpath = "../images/" + extname
            label_id = defs_lst.index(fullname)
            if label_id < 0:
                print('bad label')

            if os.path.isfile(fullpath): #and cv2.imread(fullpath) is not None:

                directory = 'generated/train/' if random.random() < 0.8 else 'generated/validation/'
                call(["ln", fullpath, directory + fullname + "/" + extname])

                count += 1
            else:
                print("file not valid: " + fullpath)


            print(count)

    print('eligible records: ' + str(count))
    print('eligible classes: ' + str(len(classes)))

generate_data(get_hierarchy.generate_tree())
