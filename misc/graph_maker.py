import pickle
import sys
from matplotlib import pyplot
import numpy

class Stats:
  def __init__(self, accuracy_per_class, count_per_class, accuracies_per_level_per_class,
               normal_accuracies_per_level_per_class):
    self.accuracy_per_class = accuracy_per_class
    self.count_per_class = count_per_class
    self.accuracies_per_level_per_class = accuracies_per_level_per_class
    self.normal_accuracies_per_level_per_class = normal_accuracies_per_level_per_class

stats = pickle.load(open(sys.argv[1], 'rb'))

# accuracy_per_class, count_per_class, accuracies_per_level_per_class, normal_accuracies_per_level_per_class
acc = stats.accuracy_per_class
counts = stats.count_per_class
aplpc = stats.accuracies_per_level_per_class
naplpc = stats.normal_accuracies_per_level_per_class

multiacc = [x.accuracy_per_class for x in [pickle.load(open(x, 'rb')) for x in sys.argv[1:]]]
multicount = [x.count_per_class for x in [pickle.load(open(x, 'rb')) for x in sys.argv[1:]]]


print(len(counts.values()))

def show_histograms():
  print(len(aplpc[-1]))
  pyplot.xticks(numpy.arange(0, 1.0001, 0.1))
  # pyplot.hist(list(acc.values()), 10, (0, 1))
  # pyplot.show()
  print(len(aplpc))
  for i in range(0, len(aplpc)):
    print(len(naplpc[i]))
    print(sum(aplpc[i].values()) / len(aplpc[i]), 'dijkstra avg')
    print(sum(naplpc[i].values()) / len(naplpc[i]), 'normal avg')

    # pyplot.hist(list(naplpc[i].values()), 10, (0, 1), histtype='bar', alpha=0.5)
    pyplot.hist(list(aplpc[i].values()), 10, (0, 1), histtype='bar')
    # pyplot.hist([list(aplpc[i].values()), list(naplpc[i].values())], color=['r', 'g'], bins=10, range=(0, 1), label=['Accuracy at parent node by child summation', 'Accuracy at parent node by ascending leaf'])
    # pyplot.legend(loc='upper right')
    pyplot.xlabel('Accuracy')
    pyplot.ylabel('Number of classes')
    pyplot.show()


def do_get_small_class_acc(idx, between=(0, 20), count_source=None):
  total = 0.0
  num_correct = 0.0

  classes_with_fewer_than = ([x for x in filter(lambda x: x[1] < between[1] and x[1] >= between[0], count_source.items())])
  for x in classes_with_fewer_than:
    # if x[0] in multiacc[idx]:
    total += (x[1] if not count_source else count_source[x[0]])
    num_correct += multiacc[idx][x[0]] * (x[1] if not count_source else count_source[x[0]])
    # print(num_correct)

  num_correct = num_correct / (total + 0.01)
  print(num_correct, total)
  print(len(multicount[idx]), len(classes_with_fewer_than), len(count_source), sum(count_source.values()))
  return num_correct

def show_multi_hist():
  pyplot.xticks(numpy.arange(0, 1.0001, 0.1))
  pyplot.hist([list(x.values()) for x in multiacc], color=['r', 'g', 'b'], bins=10, range=(0, 1), label=['Base network', 'Multi-view', 'Multi-view and hierarchical knowledge transfer'])
  pyplot.legend(loc='upper right')
  pyplot.xlabel('Accuracy')
  pyplot.ylabel('Number of classes')
  pyplot.show()

def show_small_class_compare():
  ranges = list(range(0, 1000, 80))

  count_source = multicount[2]

  # print(count_source)

  small_multiview = []
  small_multistage = []
  small_normal = []
  for i in range(0, len(ranges) - 1):
    small_normal.append(do_get_small_class_acc(0, between=(ranges[i], ranges[i+1]), count_source=count_source))
    small_multiview.append(do_get_small_class_acc(1, between=(ranges[i], ranges[i+1]), count_source=count_source))
    small_multistage.append(do_get_small_class_acc(2, between=(ranges[i], ranges[i+1]), count_source=count_source))

  ranges = ranges[:-1]
  # pyplot.plot([ranges, ranges], [small_multiview, small_multistage])
  pyplot.plot(ranges, small_normal, label='Base network') # , 'Multi-view', 'Multi-view and hierarchical knowledge transfer']
  pyplot.plot(ranges, small_multiview, label='Multi-view')
  pyplot.plot(ranges, small_multistage, label='Multi-view and hierarchical knowledge transfer')
  pyplot.legend(loc='lower right')
  pyplot.xlabel('Number of images per class')
  pyplot.ylabel('Accuracy per class')
  pyplot.show()


show_small_class_compare()
truncated_counts = {k: counts[k] for k in acc.keys()}




def show_scatter():
  scattery = [x[1] for x in sorted(list(acc.items()), key=lambda x: x[0])]
  scatterx = [x[1] for x in sorted(list(truncated_counts.items()), key=lambda x: x[0])]
  pyplot.scatter(scatterx, scattery, marker='.')
  # line = numpy.polyfit(scatterx, scattery, 1)
  # p = numpy.poly1d(line)
  # pyplot.plot(scatterx, p(scatterx), 'r-')
  pyplot.show()
# show_scatter()

# show_histograms()
# show_scatter()
show_multi_hist()
# counts = sorted([x.count_at_node for x in t.children()])

# n, bins, patches = pyplot.hist(counts, 6300 // 5)
# pyplot.plot(n)
# pyplot.show()
# print('z')
# print(n)
# print('zz')
#
# BIN_SIZE = 5
# total = t.count_at_node
# num_bins = int(6300 / BIN_SIZE)
# bins = [0] * num_bins
#
# # plots the cumulative fraction against number-of-images-in-a-class
# for count in counts:
#     bins[int(count / BIN_SIZE)] += count
#
# cumulative = 0
# for i in range(0, len(bins)):
#     cumulative += bins[i]
#     bins[i] = cumulative / total
#
#
# print(bins)
#
#
# pyplot.plot(range(0, (num_bins) * BIN_SIZE, BIN_SIZE), bins)
# pyplot.show()
#
#
#
#
