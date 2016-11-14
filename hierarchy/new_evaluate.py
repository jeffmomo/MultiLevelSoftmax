from hierarchy import get_hierarchy, level_evaluate

definitions_list = ['__BACKGROUND__']

htmlout = open('new-eval.dat', 'w+')

histogramout = open('new-histogram.dat', 'w+')

layer_correct = {}
layer_total = {}
layer_class_correct = {}
layer_class_total = {}

correct_h_count = 0.0
correct_count = 0.0
total_count = 0.0

tree = get_hierarchy.generate_tree()
tree.prune(threshold=100)
tree.get_definitions(definitions_list, False)
print(len(definitions_list))

reverse_tree = {}
tree.generate_reverse_tree(reverse_tree, False)
print(reverse_tree)


def get_relevant_input():
    out = input()
    while out[0] != '>':
        out = input()

    # Need to adapt this to actually work based on the new reverse tree
    if out[1] == '#':

        # _, filename, predicted, actual = out.split(' ')
        # predicted_name = definitions_list[int(predicted) - 1]
        # actual_name = definitions_list[int(actual) - 1]
        # tree_output = []
        # reverse_tree_predicted = reverse_tree[predicted_name]
        # reverse_tree_actual = reverse_tree[actual_name]
        # for i in range(0, min(len(reverse_tree_actual), len(reverse_tree_predicted))):
        #     tree_output.append((reverse_tree_predicted[i].split('-')[0]) + ',' + (reverse_tree_actual[i].split('-')[0]))
        #
        # htmlout.write(
        #     filename.split("'")[1] + '|' + predicted_name + '|' + actual_name + '|' + '#'.join(tree_output) + "\n")
        # htmlout.flush()

        return get_relevant_input()

    elif out[1] == '$':
        # histogramout.write('\n'.join([str('layer' + str(k) + ' ') + str(
        #     layer_correct[k] / v) if k in layer_correct else str('layer' + str(k) + ' ') + str(0.0) for k, v in
        #                               sorted(layer_total.items(), key=lambda x: x[0])]))
        # histogramout.write('\n')
        #
        # for level, v in layer_class_total.items():
        #     histogramout.write('Level: ' + str(level) + '\n')
        #     for k, total in v.items():
        #         histogramout.write(str(k) + '(' + str(layer_class_total[level][k] / layer_total[level]) + '): ' + str(
        #             layer_class_correct[level][k] / layer_class_total[level][k]) + '\n')

        histogramout.close()
        quit()

    return out

evaluator = level_evaluate.Evaluator(tree.generate_level_nodes(definitions_list))
flat_evaluator = level_evaluate.FlatEvaluator(tree.generate_leaf_indices())

# flatone = []
# tree.get_definitions(flatone)
# print(len(flatone))

while True:
    vals = get_relevant_input()
    label = get_relevant_input()

    data = [float(f) for f in vals.split(' ')[1].split(',')[1:]]

    label = int(label.split(' ')[1]) - 1


    total_count += 1

    label_reverse_tree = reverse_tree[definitions_list[label]]

    # flat_eval_idx = flat_evaluator.top(data)

    ### For finding cases where my method does not work
    # if predicted_label == label:
    #     correct_h_count += 1
    # elif data[label] == max(data):
    #     [print(x) for x in dbg]
    #     print(chain)
    #     print(definitions_list[label])
    #     print(max(data))

    # for level in range(0, len(reverse_tree[definitions_list[label]])):
    #
    #     level_name = reverse_tree[definitions_list[label]][level].split('-')[0]
    #
    #     if level in layer_total:
    #         layer_total[level] += 1.0
    #     else:
    #         layer_total[level] = 1.0
    #         layer_correct[level] = 0.0
    #
    #     if level not in layer_class_total:
    #         layer_class_total[level] = {}
    #         layer_class_correct[level] = {}
    #
    #     if level_name in layer_class_total[level]:
    #         layer_class_total[level][level_name] += 1.0
    #     else:
    #         layer_class_total[level][level_name] = 1.0
    #         layer_class_correct[level][level_name] = 0.0
    #
    #     if len(reverse_tree[definitions_list[idx_of_max]]) > level and reverse_tree[definitions_list[label]][level] == \
    #             reverse_tree[definitions_list[idx_of_max]][level]:
    #
    #         if level not in layer_class_correct:
    #             layer_class_correct[level] = {}
    #
    #         if level_name in layer_class_correct[level]:
    #             layer_class_correct[level][level_name] += 1.0
    #
    #         if level in layer_correct:
    #             layer_correct[level] += 1.0
    greedy_eval = evaluator.top_greedy(data)
    # print(definitions_list[label], definitions_list[evaluated_index], 'flat', definitions_list[flat_eval_idx])
    print(definitions_list.index(label_reverse_tree[-2]), evaluator.k_deep_top_greedy(2, data))
    dijkstra_eval = evaluator.top_k_dijkstra(data)

    print(label, dijkstra_eval[0], dijkstra_eval[1], greedy_eval[0], greedy_eval[1])

    if label_reverse_tree[-2] == definitions_list[evaluator.k_deep_top_greedy(2, data)]:
        correct_h_count += 1

    if label == dijkstra_eval[1]: #reverse_tree[definitions_list[label]][0] == reverse_tree[definitions_list[idx_of_max]][0]:
        correct_count += 1
    else:
        pass
        # print('incorrect')

    print('h', correct_h_count / total_count)
    print('normal', correct_count / total_count)

