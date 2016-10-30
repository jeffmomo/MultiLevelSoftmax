import get_hierarchy




def generate_data(tree, generate=False):

    produced_files = set()
    already_produced_count = 0


    tree.prune(threshold=100)
    # print(tree.get_list())
    defs_lst = []
    defs_leaf = []
    tree.get_definitions(defs_leaf, leaf_only=True)
    tree.get_definitions(defs_lst, leaf_only=False)
    print(defs_lst)
    print(str(len(defs_lst)))
    print(str(len(defs_leaf)))
    print(tree.count_at_node)
    z = []
    tree.build(defs_lst)
    # tree.generate_layer({})

    mapping = {}
    tree.bf_count(mapping)
    count = 0

    reverse_mapping = {}
    tree.generate_reverse_tree(reverse_mapping, False)

    print(reverse_mapping)


    """ Need to increase class count by 1, to account for tensorflow's background default class
    """
    embeddings = []
    #embeddings.append([0] * (len(defs_lst) + 1))
    embeddings.append([0] * (len(defs_leaf) + 1))


    for item in defs_lst:
        #output = [0] * (len(defs_lst) + 1)
        output = [0] * (len(defs_leaf) + 1)
        # reverse_list = reverse_mapping[item]
        # for name in reverse_list:
        #     idx = defs_lst.index(name) + 1
        #     assert idx > 0
        #     output[idx] = 1.0 / len(reverse_list)
        if item in defs_leaf:
            idx = defs_leaf.index(item) + 1
            assert idx > 0
            output[idx] = 1

        embeddings.append(output)


        # chain = ['-'.join(x.split('-')[:-1]) for x in reverse_mapping[x][::-1]]
        # embeddings.append(tree.generate_targets(1, chain, 0.5))
        pass

    with open('index_map.dat', 'w+') as map_file:

        # for tensorflow background class
        map_file.write(str(0) + '\n')
        for i in range(0, len(defs_lst)):
            leaf_idx = -1 if defs_lst[i] not in defs_leaf else defs_leaf.index(defs_lst[i])
            assert leaf_idx < len(defs_leaf)
            # For tensorflow background class
            map_file.write(str(leaf_idx + 1) + '\n')


    with open('embeddings.dat', 'w+') as embeddings_file:
        for line in embeddings:
            embeddings_file.write(','.join([str(x) for x in line]) + '\n')

generate_data(get_hierarchy.generate_tree())
