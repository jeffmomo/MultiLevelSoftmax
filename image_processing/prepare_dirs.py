import os.path
import shutil
import random
from subprocess import call

from hierarchy import get_hierarchy
from hierarchy.get_hierarchy import *


def generate_data(tree, generate=False):

    produced_files = set()
    already_produced_count = 0


    tree.prune(threshold=5)
    # print(tree.get_list())
    defs_lst = []
    tree.get_definitions(defs_lst, leaf_only=False)
    # print(defs_lst)
    # print(str(len(defs_lst)))
    print(tree.count_at_node)
    tree.build(defs_lst)

    mapping = {}
    tree.bf_count(mapping)
    count = 0

    for folder in os.listdir('.'):

      if os.path.isfile(folder):
        continue

      splitted = folder.split('.')

      if len(splitted) > 2:
        two_part_name = '.'.join(splitted[0:2])
        if not os.path.exists(two_part_name):
          print('mkdir', two_part_name)
          os.mkdir(two_part_name)

        for f in os.listdir(folder):
          print("cp " + folder + "/" + f + " " + two_part_name + "/" + f, "r")
          shutil.move(folder + "/" + f, two_part_name + "/" + f)

        print('mv', folder, '../')
        shutil.move(folder, "../" + folder)

      elif len(splitted) == 1:
        two_part_name = '.'.join(splitted * 2)
        if not os.path.exists(two_part_name):
          os.mkdir(two_part_name)

        for f in os.listdir(folder):
          if not os.path.isfile(f):
            continue

          print("cp " + folder + "/" + f + " " + two_part_name + "/" + f, "r")
          shutil.move(folder + "/" + f, two_part_name + "/" + f)

        print('mv', folder, '../')
        shutil.move(folder, "../" + folder)



    for leaf in tree.children():
      os.popen(" ".join(["mv", leaf.get_full_name(), 'good/' + leaf.get_full_name()]), "r")



    print(count)

    print('eligible records: ' + str(count))

generate_data(get_hierarchy.generate_tree())
