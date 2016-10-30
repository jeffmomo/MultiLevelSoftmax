from functools import reduce
from typing import Union, Optional, Tuple
import heapq
import random

class LayerEvaluator:

    def __init__(self, layer, definitions, conditionals = []):
        self.root = layer
        self.definitions = definitions
        self.initial_depth = len(conditionals)

        for level in conditionals:
            next_layer = [x for x, _ in self.root.elems if x.name == level]
            assert len(next_layer) > 0, "The layer condition cannot be satisfied"
            self.root = next_layer[0]

    def dijkstra_top(self, output) -> Tuple[float, str]:
        heap = []
        root_sum = self.root.avg(output)
        for item, _ in self.root.elems:
            heapq.heappush(heap, (-item.avg(output) / root_sum, random.random(), item)) # use negative for max-heap

        while len(heap):
            negative_prob, _, lvlnode = heapq.heappop(heap)
            # print(negative_prob, lvlnode)

            if type(lvlnode) is str:
                return (-negative_prob, lvlnode)

            if lvlnode.is_near_leaf():

                sum_near_leaf = lvlnode.avg(output)
                max_elem = max([(idx, output[idx]) for idx, _ in lvlnode.elems], key=lambda x: x[1])
                heapq.heappush(heap, (negative_prob * (max_elem[1] / sum_near_leaf), random.random(), self.definitions[max_elem[0]]))
            else:
                assert all([type(x) == Layer for x, _ in lvlnode.elems])
                node_sum = lvlnode.avg(output)

                # print(node_sum)
                for item, _ in lvlnode.elems:
                    # print(negative_prob * (item.avg(output) / node_sum), item)
                    heapq.heappush(heap, (negative_prob * (item.avg(output) / node_sum), random.random(), item))

        return None

    def dijkstra_threshold(self, output, threshold=0, mindepth=None) -> (float, str):

        max_elem = None

        return_heap = []  # return heap is tuple of (negative depth, probability, string)
        def conditional_push(tup):
            nonlocal max_elem
            depth, prob, name = tup

            if mindepth is not None and depth >= mindepth:
                return (prob, name, depth)

            if max_elem is None or depth > max_elem[0] or (depth == max_elem[0] and prob > max_elem[1]):
                max_elem = (depth, prob, name)
            #if not len(return_heap) or neg_depth < return_heap[0][0] or (neg_depth == return_heap[0][0] and prob > return_heap[0][1]):
            #    heapq.heappush(return_heap, (neg_depth, prob, name))

        heap = []  # heap is tuple of (negative probability, Layer, depth), is minheap.
        root_sum = self.root.avg(output)
        for conditional_probability_neg, item in sorted([(-x.avg(output) / root_sum, x) for x, _ in self.root.elems], key=lambda z: z[0]):
            retval = conditional_push((self.initial_depth, -conditional_probability_neg, item.name))
            if retval:
                return retval
            if -conditional_probability_neg > threshold:
                heapq.heappush(heap, (conditional_probability_neg, random.random(), item, self.initial_depth)) # use negative for max-heap


        while len(heap):
            negative_prob, _, lvlnode, depth = heapq.heappop(heap)
            # print(negative_prob, lvlnode)

            if type(lvlnode) == int:
                return (-negative_prob, self.definitions[lvlnode], depth)
                # retval = conditional_push((depth + 1, -negative_prob, self.definitions[lvlnode]))
                # if retval:
                #     return retval

            elif lvlnode.is_near_leaf():

                sum_near_leaf = lvlnode.avg(output)
                sorted_elems = sorted([(idx, output[idx]) for idx, _ in lvlnode.elems], key=lambda x: -x[1])

                conditional_probability_neg = negative_prob * (sorted_elems[0][1] / sum_near_leaf)

                if(-conditional_probability_neg > threshold):
                    heapq.heappush(heap, (conditional_probability_neg, random.random(), sorted_elems[0][0], depth + 1))

            else:
                assert all([type(x) == Layer for x, _ in lvlnode.elems])
                node_sum = lvlnode.avg(output)

                # print(node_sum)
                for conditional_probability_neg, item in sorted(filter(lambda x: -x[0] > threshold, [(negative_prob * (x.avg(output) / node_sum), x) for x, _ in lvlnode.elems]), key=lambda z: z[0]):
                    #conditional_probability_neg = negative_prob * (item.avg(output) / node_sum)
                    #if -conditional_probability_neg > threshold:
                    heapq.heappush(heap, (conditional_probability_neg, random.random(), item, depth + 1))
                    retval = conditional_push((depth + 1, -conditional_probability_neg, item.name))
                    if retval:
                        return retval
        return (max_elem[1], max_elem[2], max_elem[0])
        #return None if not len(return_heap) else (return_heap[0][1], return_heap[0][2], -return_heap[0][0])

class Layer:

    def __init__(self, elems: list, name: str):
        self.elems = elems
        self.name = name

    def listify(self):
        if type(self.elems[0]) != Layer:
            return self.elems

        return reduce(list.__add__, [x.listify() for x in self.elems], [])


    def is_near_leaf(self):
        # extract the actual element and ignore the name
        return type(self.elems[0][0]) != Layer

    def getChildren(self):

        #if type(self.elems[0][0]) != Layer:
        #    return self.elems
        return reduce(lambda a, b: a + b, [x.getChildren() if type(x) == Layer else [(x, name)] for (x, name) in self.elems], [])

    def avg(self, output):
        summation = 0
        children = self.getChildren()
        for (elem, name) in children:
            summation += output[elem]

        return summation#(summation / len(children))# + m

    def evaluateWithPrior(self, priors: list, output: list, chain: list) -> (int, list):
        layer = self.elems
        for idx in priors[:-1]:
            chain.append(idx)
            layer = layer[idx].elems

        chain.append(priors[-1])
        layer = layer[priors[-1]]

        return layer.evaluate(output, chain)

    # Mutable list argument
    def evaluate(self, output: list, chain: list, debug: list) -> (int, list):
        # elems are each a tuple of (list | Layer, name)
        #if type(self.elems[0][0]) != Layer:

        mapped = sorted([(x.avg(output) if type(x) == Layer else output[x], x, idx, name) for idx, (x, name) in enumerate(self.elems)], key=lambda x: -x[0])

        chain.append(mapped[0][3])
        debug.append(mapped)

        if type(mapped[0][1]) != Layer:
            return (mapped[0][1], chain)
        else:
            return mapped[0][1].evaluate(output, chain, debug)


        #mapped = sorted([(x.avg(output), x, idx, name) for idx, (x, name) in enumerate(self.elems)], key=lambda x: -x[0])
        #chain.append(mapped[0][3])

        #debug.append(mapped)

        #return mapped[0][1].evaluate(output, chain, debug)


# print(Layer([Layer([2, 3, 4]), Layer([1,0,5])]).evaluate([1,2,3,4,5,6], []))
#
# print(
#     Layer([
#         Layer([
#             Layer([2, 0]),
#             Layer([4])
#         ]),
#         Layer([1, 3, 5])
#     ])
#     .evaluateWithPrior([0, 0], [1, 2, 3, 4, 4, 6], []))

# .evaluate([1,2,3,4,4,6]))


# print(Layer([Layer([1,2]), Layer([3, 4])]).evaluate([0, 3, 3.1, 4, 1]))




