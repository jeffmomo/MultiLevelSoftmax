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

multistats = [list(x.accuracy_per_class.values()) for x in [pickle.load(open(x, 'rb')) for x in sys.argv[1:]]]

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

def show_multi_hist():
  pyplot.xticks(numpy.arange(0, 1.0001, 0.1))
  pyplot.hist(multistats, color=['r', 'g', 'b'], bins=10, range=(0, 1), label=['Base network', 'Multi-view', 'Multi-view and hierarchical knowledge transfer'])
  pyplot.legend(loc='upper right')
  pyplot.xlabel('Accuracy')
  pyplot.ylabel('Number of classes')
  pyplot.show()


truncated_counts = {k: counts[k] for k in acc.keys()}


def show_scatter():
  scattery = [x[1] for x in sorted(list(acc.items()), key=lambda x: x[0])]
  scatterx = [x[1] for x in sorted(list(truncated_counts.items()), key=lambda x: x[0])]
  pyplot.scatter(scatterx, scattery, marker='.')
  # line = numpy.polyfit(scatterx, scattery, 1)
  # p = numpy.poly1d(line)
  # pyplot.plot(scatterx, p(scatterx), 'r-')
  pyplot.show()

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
