import math
import sys
import functools

import hierarchy.get_hierarchy as get_hierarchy
import hierarchy.hierarchical_eval as hierarchical_eval

IS_TEST = 'test' in sys.argv
DEEP_STATS = 'deep_stats' in sys.argv

definitions_list = []

# htmlout = open('html.html', 'w+')

histogramout = open('histogram.dat', 'w+')

accuracy_depth_file = open('thresholds.dat', 'w+')

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
print(len(definitions_list))
tree.assign_indices(definitions_list)

mapping = {}
layer, _ = tree.generate_layer(mapping)
print("map size", len(mapping))

reverse_tree = {}
tree.generate_reverse_tree(reverse_tree, leaf_only=False)

# ------------STATS COLLECTION-----------------
count_map = {child.get_full_name(): child.count_at_node for child in tree.children()}
correct_map = {}
total_map = {}
automatic_specificity_depth_map = {}

total_per_class_map = [{} for x in range(0, 7)]
correct_dijskstra_per_class = [{} for x in range(0, 7)]
correct_normal_per_class = [{} for x in range(0, 7)]


# ---------------------------------------------

class Stats:
  def __init__(self, accuracy_per_class, count_per_class, accuracies_per_level_per_class,
               normal_accuracies_per_level_per_class):
    self.accuracy_per_class = accuracy_per_class
    self.count_per_class = count_per_class
    self.accuracies_per_level_per_class = accuracies_per_level_per_class
    self.normal_accuracies_per_level_per_class = normal_accuracies_per_level_per_class


def finish_up():
  histogramout.write('\n'.join([str('layer' + str(k) + ' ') + str(
    layer_correct[k] / v) if k in layer_correct else str('layer' + str(k) + ' ') + str(0.0) for k, v in
                                sorted(layer_total.items(), key=lambda x: x[0])]))
  histogramout.write('\n')

  for level, v in layer_class_total.items():
    histogramout.write('Level: ' + str(level) + '\n')
    for k, total in v.items():
      histogramout.write(str(k) + '(' + str(layer_class_total[level][k] / layer_total[level]) + '): ' + str(
        layer_class_correct[level][k] / layer_class_total[level][k]) + '\n')

  histogramout.close()

  accuracy_map = {k: correct_map.get(k, 0) / v for k, v in total_map.items()}

  per_level_dijkstra = [{k: correct_dijskstra_per_class[i].get(k, 0) / v for k, v in total_per_class_map[i].items()} for
                        i in range(0, len(total_per_class_map))]

  per_level_normal = [{k: correct_normal_per_class[i].get(k, 0) / v for k, v in total_per_class_map[i].items()} for i in
                      range(0, len(total_per_class_map))]

  # print(total_map, correct_map, accuracy_map, per_level_dijkstra, per_level_normal)
  # print(per_level_dijkstra)
  import pickle
  pickle.dump(Stats(accuracy_map, total_map, per_level_dijkstra, per_level_normal), open('stats.pickle', 'wb'))
  pickle.dump(automatic_specificity_depth_map, open('automatic_specificity_map.pickle', 'wb'))


  accuracy_depth_file.close()
  quit()


def get_relevant_input():
  try:
    out = input()
  except EOFError as e:
    finish_up()

  while out[0] != '>':
    out = input()

  # Need to adapt this to actually work based on the new reverse tree
  if out[1] == '#':
    _, filename, predicted, actual = out.split(' ')
    return get_relevant_input()
  elif out[1] == '$':
    finish_up()

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

LEARNING_RATE_INITIAL = 0.01
learning_rate = LEARNING_RATE_INITIAL
LEARNING_RATE_DEPTH = 0.001
threshold = 0.9
TARGET_ACCURACY = 0.9
TARGET_DEPTH = 5.0
eps = 0.01
OPTIMISE_SET = 100000
PRINT_PER = 100

SWITCH_EVERY_EXAMPLES = 20000
target_accuracies = [0.5, 0.6, 0.7, 0.8, 0.9, 0.92, 0.94, 0.96, 0.98, 0.99]
current_accuracy_index = 0
# TARGET_ACCURACY = target_accuracies[current_accuracy_index]

per_instance_decay = (1.0 / OPTIMISE_SET) * 3.0 # 0.00003

moving_avg = MovingAverage(100)
moving_depth = MovingAverage(100)
moving_thresh = MovingAverage(100)

moving_depth_value = 1.0
moving_acc_value = 1.0
moving_thresh_value = 1.0

while True:

  # test HERE ------------------------------------------------------------------------------------------------------
  if IS_TEST and total_count >= 1000:
    finish_up()

  vals = get_relevant_input()
  label_and_filename = get_relevant_input().split(' ')

  data = [float(f) for f in vals.split(' ')[1].split(',')]
  translated_data = [0] * len(data)
  # print(len(translation_map), len(data))
  for i in range(0, len(translation_map)):
    translated_data[translation_map[i]] = data[i]

  data = translated_data

  label = translation_map[int(label_and_filename[1])]
  filename = label_and_filename[2] if len(label_and_filename) > 2 else ''
  # print(filename)


  idx_of_max = 0
  max = -9999999.9
  for i in range(0, len(data)):
    if data[i] > max:
      idx_of_max = i
      max = data[i]

  actual_name = definitions_list[label]
  label_reverse_tree = reverse_tree[actual_name]


  total_count += 1

  if DEEP_STATS:
    for level in range(0, len(total_per_class_map)):

      current_actual_name = label_reverse_tree[-(level+1)]


      total_per_class_map[level][current_actual_name] = total_per_class_map[level].get(current_actual_name, 0) + 1

      _, level_predicted_name, _ = evaluator.dijkstra_threshold(data, mindepth=level)

      # print(level_predicted_name, current_actual_name)

      if level_predicted_name == current_actual_name:
        correct_dijskstra_per_class[level][current_actual_name] = correct_dijskstra_per_class[level].get(current_actual_name, 0) + 1

      if reverse_tree[definitions_list[idx_of_max]][-(level+1)] == current_actual_name:
        correct_normal_per_class[level][current_actual_name] = correct_normal_per_class[level].get(current_actual_name, 0) + 1

  if label in labelmap:
    labelmap[label] += 1.0
  else:
    labelmap[label] = 1.0

  probability = data[label]

  thresh_result = evaluator.dijkstra_threshold(data, threshold)
  # print(thresh_result)

  total_depth += thresh_result[2]

  thresh_result_is_correct = False

  if thresh_result[1] in label_reverse_tree:
    correct_z_count += 1
    thresh_result_is_correct = True

  if label == idx_of_max:
    correct_count += 1
    correct_map[actual_name] = correct_map.get(actual_name, 0) + 1

  dijkstra_predicted_name = thresh_result[1]

  automatic_specificity_depth_map[actual_name] = automatic_specificity_depth_map.get(actual_name, 0) + thresh_result[2]

  total_map[actual_name] = total_map.get(actual_name, 0) + 1


  thresh_accuracy = correct_z_count / total_count

  single_acc = 1 if thresh_result_is_correct else 0

  new_thresh = moving_thresh.push_and_get_average(threshold)
  new_acc = moving_avg.push_and_get_average(single_acc)
  new_depth = moving_depth.push_and_get_average(thresh_result[2])

  d = (new_depth - moving_depth_value + eps) / (new_thresh - moving_thresh_value + eps)

  moving_acc_value = new_acc
  moving_depth_value = new_depth
  moving_thresh_value = new_thresh

  if int(total_count) % PRINT_PER == 0:
    print('h', correct_h_count / total_count)
    print('dijkstra', correct_d_count / total_count)
    print('normal', correct_count / total_count)
    print('thresh', thresh_accuracy)
    print('avg depth', total_depth / total_count)

    print('moving_acc', moving_acc_value)
    print('moving depth', moving_depth_value)
    print('moving thresh', moving_thresh_value)
    print('gradient', d)
    print("current threshold", threshold)
    print("target accuracy", TARGET_ACCURACY)

    print('learning rate', learning_rate)

    print('total count', total_count)

  # threshold = thresholds[int(total_count) // SWITCH_EVERY_EXAMPLES]

  # if int(total_count) == SWITCH_EVERY_EXAMPLES:
  #   accuracy_depth_file.write(','.join([str(thresh_accuracy), str(total_depth / total_count)]) + '\n')
  #   current_accuracy_index += 1
  #   if current_accuracy_index == len(target_accuracies):
  #     finish_up()
  #   TARGET_ACCURACY = target_accuracies[current_accuracy_index]
  #   total_count = 0
  #   correct_count = 0
  #   correct_z_count = 0
  #   total_depth = 0
  #   learning_rate = LEARNING_RATE_INITIAL

  print('total', total_count)
  print('correct', correct_count)

  if int(total_count) == OPTIMISE_SET:
    total_count = 0
    correct_count = 0
    correct_z_count = 0
    total_depth = 0
    learning_rate = 0

  threshold += learning_rate * (TARGET_ACCURACY - moving_acc_value)

  if threshold < 0:
    threshold = 0
  elif threshold > 1:
    threshold = 1

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
