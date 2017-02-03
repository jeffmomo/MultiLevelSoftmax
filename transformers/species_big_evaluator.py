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
total_depth = 0.0

tree = get_hierarchy.pruned_tree
translation_map = get_hierarchy.native_to_hierarchical_translation_map(tree)
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



class MovingAverage:

    def __init__(self, window_size=100):
        self.queue = []
        self.moving_sum = 0
        self.window_size = window_size

    def push_and_get_average(self, val):
        self.queue.append(val)
        self.moving_sum += val
        if len(self.queue) > self.window_size:
            self.moving_sum -= self.queue[0]
            self.queue = self.queue[1:]

        return self.moving_sum / len(self.queue)

    def get_average(self):
        return self.moving_sum / len(self.queue)


labelmap = {}
evaluator = hierarchical_eval.LayerEvaluator(layer, definitions_list)

learning_rate = 0.1
LEARNING_RATE_DEPTH = 0.001
per_instance_decay = 0.001
threshold = 0.9
TARGET_ACCURACY = 0.9
TARGET_DEPTH = 5.0
eps = 0.01

moving_avg = MovingAverage(100)
moving_depth = MovingAverage(100)
moving_thresh = MovingAverage(100)


moving_depth_value = 1.0
moving_acc_value = 1.0
moving_thresh_value = 1.0

while True:
    print('init')
    vals = get_relevant_input()
    label_and_filename = get_relevant_input().split(' ')

    print('zzz')

    data = [float(f) for f in vals.split(' ')[1].split(',')]
    translated_data = [0] * len(data)
    print(len(translation_map), len(data))
    for i in range(0, len(translation_map)):
        translated_data[translation_map[i]] = data[i]

    data = translated_data

    label = translation_map[int(label_and_filename[1])]
    filename = label_and_filename[2]
    print(filename)

    label_reverse_tree = reverse_tree[definitions_list[label]]

    idx_of_max, _ = functools.reduce(lambda accum, v: v if v[1] > accum[1] else accum, enumerate(data))

    total_count += 1


    def get_max_elem(root_map):
        max_elem = ('none', -99999999.0)
        for k, v in root_map.items():
            if v > max_elem[1]:
                max_elem = (k, v)
        return max_elem


    for level in range(0, len(reverse_tree[definitions_list[label]])):
        
        level_name = reverse_tree[definitions_list[label]][level].split('.')[0]

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

    probability = data[label]

    print("expected: ", label, "actual normal classified:", idx_of_max)

    print('normal prob', probability)

    thresh_result = evaluator.dijkstra_threshold(data, threshold)
    print(thresh_result)

    total_depth += thresh_result[2]

    thresh_result_is_correct = False

    if thresh_result[1] in label_reverse_tree:
        correct_z_count += 1
        thresh_result_is_correct = True

    # if reverse_tree[definitions_list[label]][-3] == reverse_tree[definitions_list[idx_of_max]][-3]:
    #     correct_count += 0#

    if label == idx_of_max:
        correct_count += 1#

    # if label == layer.evaluate(data, [], [])[0]:
    #     # print('correct')
    #     correct_h_count += 1
    # else:
    #     pass
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

    thresh_accuracy = correct_z_count / total_count

    print('h', correct_h_count / total_count)
    print('dijkstra', correct_d_count / total_count)
    print('normal', correct_count / total_count)
    print('thresh', thresh_accuracy)
    print('avg level', total_depth / total_count)

    single_acc = 1 if thresh_result_is_correct else 0

    new_thresh = moving_thresh.push_and_get_average(threshold)
    new_acc = moving_avg.push_and_get_average(single_acc)
    new_depth = moving_depth.push_and_get_average(thresh_result[2])

    d = (new_depth - moving_depth_value + eps) / (new_thresh - moving_thresh_value + eps)

    moving_acc_value = new_acc
    moving_depth_value = new_depth
    moving_thresh_value = new_thresh

    print('moving_acc', moving_acc_value)
    print('moving depth', moving_depth_value)
    print('moving thresh', moving_thresh_value)
    print('gradient', d)


    threshold += 0.01 * -(TARGET_DEPTH - moving_depth_value)

    if threshold < 0:
        threshold = 0
    elif threshold > 1:
        threshold = 1

    print("current threshold", threshold)

    learning_rate *= (1 - per_instance_decay)


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
