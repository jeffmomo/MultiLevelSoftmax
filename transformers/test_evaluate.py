import math
import sys
import functools

import hierarchy.get_hierarchy as get_hierarchy
import hierarchy.hierarchical_eval as hierarchical_eval

definitions_list = []

htmlout = open('html.html', 'w+')

histogramout = open('histogram.dat', 'w+')

layer_correct = {}
layer_total = {}
layer_class_correct = {}
layer_class_total = {}

correct_h_count = 0.0
correct_count = 0.0
correct_d_count = 0.0
correct_z_count = 0.0
total_count = 0.0

tree = get_hierarchy.generate_tree()
tree.prune(threshold=100)
tree.get_definitions(definitions_list)
# print(definitions_list)
print(len(definitions_list))

tree.assign_indices(definitions_list)



mapping = {}
layer, _ = tree.generate_layer(mapping)
print("map size", len(mapping))

# print(layer.listify())
#print(layer.getChildren())

reverse_tree = {}
tree.generate_reverse_tree(reverse_tree, leaf_only=False)
# print(reverse_tree)


def get_relevant_input():
    out = input()
    while out[0] != '>':
        out = input()

    # Need to adapt this to actually work based on the new reverse tree
    if out[1] == '#':
        _, filename, predicted, actual = out.split(' ')
        return get_relevant_input()
    elif out[1] == '$':
        histogramout.write('\n'.join([str('layer' + str(k) + ' ') + str(layer_correct[k] / v) if k in layer_correct else str('layer' + str(k) + ' ') + str(0.0) for k, v in sorted(layer_total.items(), key=lambda x: x[0])]))
        histogramout.write('\n')

        for level, v in layer_class_total.items():
            histogramout.write('Level: ' + str(level) + '\n')
            for k, total in v.items():
                histogramout.write(str(k) + '(' + str(layer_class_total[level][k] / layer_total[level]) + '): ' + str(layer_class_correct[level][k] / layer_class_total[level][k]) + '\n')

        histogramout.close()
        quit()

    return out


def reduction_builder(position=-1):

        def reduce_root(accum, val):
            idx, value = val
            leaf_name = definitions_list[idx]

            if position < -len(reverse_tree[leaf_name]):
                return accum

            leaf_root = reverse_tree[leaf_name][position]

            accum[leaf_root] = value if leaf_root not in accum else accum[leaf_root] + value

            return accum

        return reduce_root

def filter_builder(match, position=-1):

    def filter_items(val):
        idx, value = val
        leaf_name = definitions_list[idx]

        if position < -len(reverse_tree[leaf_name]):
            return False

        leaf_root = reverse_tree[leaf_name][position]
        if leaf_root != match:
            return False

        return True

    return filter_items


labelmap = {}
evaluator = hierarchical_eval.LayerEvaluator(layer, definitions_list)
while True:
    print('init')
    vals = get_relevant_input()
    label_and_filename = get_relevant_input().split(' ')

    print('zzz')

    data = [float(f) for f in vals.split(' ')[1].split(',')[1:]]
    data_exp_sum = sum([math.exp(x) for x in data])
    data = [math.exp(x) / data_exp_sum for x in data]

    label = int(label_and_filename[1]) - 1
    filename = label_and_filename[2]
    print(filename)

    label_reverse_tree = reverse_tree[definitions_list[label]]

    idx_of_max, _ = functools.reduce(lambda accum, v: v if v[1] > accum[1] else accum, enumerate(data))

    total_count += 1

    print('--')
    dbg = []
    predicted_label, chain = layer.evaluate(data, [], dbg)

    


    def get_max_elem(root_map):
        max_elem = ('none', -99999999.0)
        for k, v in root_map.items():
            if v > max_elem[1]:
                max_elem = (k, v)
        return max_elem


    itemset = [x for x in enumerate(data)]
    root_map = {}
    initial_position = -1
    while initial_position >= -len(reverse_tree[definitions_list[label]]):
        #print(itemset)
        # if len(reverse_tree[definitions_list[label]]) >= -initial_position:
        red_fn = reduction_builder(initial_position)
        root_map = functools.reduce(red_fn, itemset, {})
        #print(root_map)
        root_map_max_elem = get_max_elem(root_map)
        #print(root_map_max_elem)

        # if reverse_tree[definitions_list[label]][initial_position] == root_map_max_elem[0]:
        #     if initial_position in layer_correct:
        #         layer_correct[initial_position] += 1.0
        #     else:
        #         layer_correct[initial_position] = 1.0
        #
        # if initial_position in layer_total:
        #     layer_total[initial_position] += 1.0
        # else:
        #     layer_total[initial_position] = 1.0

        filter_fn = filter_builder(root_map_max_elem[0], initial_position)

        itemset = [x for x in itemset if filter_fn(x)]
        initial_position -= 1


    #print(itemset)


    ### For finding cases where my method does not work
    # if predicted_label == label:
    #     correct_h_count += 1
    # elif data[label] == max(data):
    #     [print(x) for x in dbg]
    #     print(chain)
    #     print(definitions_list[label])
    #     print(max(data))

    for level in range(0, len(reverse_tree[definitions_list[label]])):
        
        level_name = reverse_tree[definitions_list[label]][level].split('-')[0]

        if level in layer_total:
            layer_total[level] += 1.0
        else:
            layer_total[level] = 1.0
            layer_correct[level] = 0.0

        if level not in layer_class_total:
            layer_class_total[level] = {}
            layer_class_correct[level] = {}

        if level_name in layer_class_total[level]:
            layer_class_total[level][level_name] += 1.0
        else:
            layer_class_total[level][level_name] = 1.0
            layer_class_correct[level][level_name] = 0.0

        if len(reverse_tree[definitions_list[idx_of_max]]) > level and reverse_tree[definitions_list[label]][level] == reverse_tree[definitions_list[idx_of_max]][level]:

            if level not in layer_class_correct:
                layer_class_correct[level] = {}

            if level_name in layer_class_correct[level]:
                layer_class_correct[level][level_name] += 1.0


            if level in layer_correct:
                layer_correct[level] += 1.0

    if label in labelmap:
        labelmap[label] += 1.0
    else:
        labelmap[label] = 1.0

    print('total clss', len(labelmap.keys()))
    print('max fraction', max(labelmap.values()) / float(total_count))

    # if label == layer.evaluate(data, [], [])[0]: #itemset[0][0]:
    probability = data[label]

    print('normal prob', probability)

    result = evaluator.dijkstra_top(data)
    print(result)
    thresh_result = evaluator.dijkstra_threshold(data, 0.2)
    print(thresh_result)
    if result[1] in label_reverse_tree:
    # if reverse_tree[definitions_list[label]][0] == root_map_max_elem[0]:
        correct_d_count += 1

    if thresh_result[1] in label_reverse_tree:
        correct_z_count += 1

    if reverse_tree[definitions_list[label]][-3] == reverse_tree[definitions_list[idx_of_max]][-3]:
        correct_count += 0#

    if label == idx_of_max:
        correct_count += 1#

    if label == layer.evaluate(data, [], [])[0]:
        # print('correct')
        correct_h_count += 1
    else:
        pass
        # print('incorrect')

    
    predicted_name = thresh_result[1]
    actual_name = definitions_list[label]
    tree_output = []
    reverse_tree_predicted = reverse_tree[predicted_name]
    reverse_tree_actual = reverse_tree[actual_name]
    print(reverse_tree_actual)
    print(reverse_tree_predicted)
    for i in range(-1, -min(len(reverse_tree_actual), len(reverse_tree_predicted)) - 1, -1):
        tree_output.append((reverse_tree_predicted[i].split(tree.join_character)[1]) + ',' + (reverse_tree_actual[i].split(tree.join_character)[1]))

    htmlout.write('|'.join([filename, predicted_name, actual_name, '#'.join(tree_output), str(thresh_result[0]), str(thresh_result[1] in label_reverse_tree), str(thresh_result[2])]) + "\n")
    htmlout.flush()
    
    print('h', correct_h_count / total_count)
    print('dijkstra', correct_d_count / total_count)
    print('normal', correct_count / total_count)
    print('thresh', correct_z_count / total_count)






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
count = 0
