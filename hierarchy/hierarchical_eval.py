from functools import reduce
from typing import Union, Optional, Tuple
import heapq
import random

class LayerEvaluator:

    def __init__(self, layer, definitions, conditionals=list()):
        self.root = layer
        self.definitions = definitions
        self.initial_depth = len(conditionals)

        for level in conditionals:
            print(self.root.elems)
            next_layer = [x for x, _ in self.root.elems if type(x) is Layer and x.name == level]
            if not len(next_layer):
                print("The layer condition cannot be satisfied")
                break

            self.root = next_layer[0]

    @staticmethod
    def invariant_sum(item, output):
        if type(item) is float:
            return item
        else:
            return item.sum(output)

    def dijkstra_top(self, output) -> Tuple[float, str]:
        heap = []
        # root_sum = LayerEvaluator.invariant_sum(self.root, output)
        # for item, _ in self.root.elems:
        #     heapq.heappush(heap, (LayerEvaluator.invariant_sum(-item, output) / root_sum, random.random(), item)) # use negative for max-heap

        heapq.heappush(heap, (-1, random.random(), self.root))

        while len(heap):
            negative_prob, _, lvlnode = heapq.heappop(heap)

            if type(lvlnode) is str:
                return (-negative_prob, lvlnode)

            if lvlnode.is_near_leaf():

                sum_near_leaf = LayerEvaluator.invariant_sum(lvlnode, output)
                max_elem = max([(idx, output[idx]) for idx, _ in lvlnode.elems], key=lambda x: x[1])
                heapq.heappush(heap, (negative_prob * (max_elem[1] / sum_near_leaf), random.random(), self.definitions[max_elem[0]]))
            else:
                assert all([type(x) == Layer for x, _ in lvlnode.elems])
                node_sum = LayerEvaluator.invariant_sum(lvlnode, output)

                # print(node_sum)
                for item, _ in lvlnode.elems:
                    # print(negative_prob * (item.avg(output) / node_sum), item)
                    heapq.heappush(heap, (negative_prob * (LayerEvaluator.invariant_sum(item, output) / node_sum), random.random(), item))

        return None

    @staticmethod
    def find_matching_layers(root, output, to_find, found):
        """

        :param root:
        :param output:
        :param to_find:
        :param found:
        :return: Returns list of (Probability, Layer | Index)
        """
        root, root_name = root
        if type(root) is not Layer:
            if root_name in to_find:
                to_find.remove(root_name)
                found.append(LayerEvaluator.invariant_sum(root, output), root)
            
            return

        for item, name in root.elems:
            print(item, name)
            if name in to_find:
                to_find.remove(name)
                if type(item) is Layer:
                    found.append((LayerEvaluator.invariant_sum(item, output), item))
                else:
                    found.append((LayerEvaluator.invariant_sum(item, output), item))
            else:
                LayerEvaluator.find_matching_layers((item, name), output, to_find, found)


    def dijkstra_with_initial_domain(self, domain, output, threshold=0, mindepth=None) -> (float, str):
        matches = []
        self.find_matching_layers((self.root, 'init'), output, domain, matches)

        initial_heap = map(lambda tup: (-tup[0], tup[1]) , matches)
        
        return self.dijkstra_threshold(output, threshold, mindepth, initial_heap)

    def dijkstra_with_disjoint_domain(self, domain, output, threshold=0, mindepth=None) -> (float, str):
        matches = []
        self.find_matching_layers((self.root, 'init'), output, domain, matches)

        initial_heap = map(lambda tup: (-tup[0], tup[1]), matches)

        return self.dijkstra_threshold(output, threshold, mindepth, initial_heap)




    def dijkstra_threshold(self, output, threshold=0, mindepth=None, initial_heap=None) -> (float, str):
        """
        Performs dijkstra search, given a minimum confidence threshold to satisfy, a minimum depth
        :param output: The vector of values to evaluate on
        :param threshold: Miniumum confidence threshold that must be satisfied by the returned node
        :param mindepth: Minimum depth that must be satisfied by the returned node
        :param initial_heap: Initial starting roots.??
        :return:
        """
        max_elem = None

        return_heap = []  # return heap is tuple of (negative depth, probability, string)
        def conditional_push(tup):
            nonlocal max_elem
            depth, prob, name = tup

            if mindepth is not None and depth >= mindepth:
                return (prob, name, depth)

            if max_elem is None or depth > max_elem[0] or (depth == max_elem[0] and prob > max_elem[1]):
                max_elem = (depth, prob, name)

        heap = []  
        # heap is tuple of (negative probability, Layer, depth), is minheap.
        # root_sum = self.root.sum(output)
        # for conditional_probability_neg, item in sorted([(-x.sum(output) / root_sum, x) for x, _ in self.root.elems], key=lambda z: z[0]):
        #     retval = conditional_push((self.initial_depth, -conditional_probability_neg, item.name))
        #     if retval:
        #         return retval
        #     if -conditional_probability_neg > threshold:
        #         heapq.heappush(heap, (conditional_probability_neg, random.random(), item, self.initial_depth)) # use negative for max-heap
        #
        if initial_heap is None:
            initial_item = (-1, random.random(), self.root, self.initial_depth - 1)
            heapq.heappush(heap, initial_item)
        else:
            # print('nopush')
            for item in initial_heap:
                heapq.heappush(heap, item)

        while len(heap):
            negative_prob, _, lvlnode, depth = heapq.heappop(heap)
            # print(negative_prob, lvlnode)
            # print(lvlnode.elems if type(lvlnode) != int else lvlnode)
            if type(lvlnode) == int:
                return (-negative_prob, self.definitions[lvlnode], depth)
                # retval = conditional_push((depth + 1, -negative_prob, self.definitions[lvlnode]))
                # if retval:
                #     return retval

            elif lvlnode.is_near_leaf():

                sum_near_leaf = lvlnode.sum(output)
                sorted_elems = sorted([(idx, output[idx]) for idx, _ in lvlnode.elems], key=lambda x: -x[1])

                conditional_probability_neg = negative_prob * (sorted_elems[0][1] / sum_near_leaf)

                if(-conditional_probability_neg > threshold):
                    heapq.heappush(heap, (conditional_probability_neg, random.random(), sorted_elems[0][0], depth + 1))

            else:
                assert all([type(x) == Layer for x, _ in lvlnode.elems])
                node_sum = lvlnode.sum(output)

                # print(node_sum)
                for conditional_probability_neg, item in sorted(filter(lambda x: -x[0] > threshold, [(negative_prob * (x.sum(output) / node_sum), x) for x, _ in lvlnode.elems]), key=lambda z: z[0]):
                    #conditional_probability_neg = negative_prob * (item.avg(output) / node_sum)
                    #if -conditional_probability_neg > threshold:
                    heapq.heappush(heap, (conditional_probability_neg, random.random(), item, depth + 1))
                    retval = conditional_push((depth + 1, -conditional_probability_neg, item.name))
                    if retval:
                        return retval
        if max_elem is None:
            o = self.dijkstra_threshold(output, threshold=00, mindepth=0)
            return (o[0], o[1], 0)
        return (max_elem[1], max_elem[2], max_elem[0])
        #return None if not len(return_heap) else (return_heap[0][1], return_heap[0][2], -return_heap[0][0])

class Layer:

    def __init__(self, elems: list, name: str):
        self.elems = elems
        self.name = name
        self.cached_children = None

    def listify(self):
        if type(self.elems[0]) != Layer:
            return self.elems

        return reduce(list.__add__, [x.listify() for x in self.elems], [])


    def is_near_leaf(self):
        # extract the actual element and ignore the name
        return type(self.elems[0][0]) != Layer

    def getChildren(self):
        if not self.cached_children:
            ls = []
            for x in [x.getChildren() if type(x) == Layer else [(x, name)] for (x, name) in self.elems]:
                ls.extend(x)
            self.cached_children = ls # reduce(lambda a, b: a + b, , [])
        return self.cached_children

    def sum(self, output):
        summation = 0
        children = self.getChildren()
        for (elem, name) in children:
            summation += output[elem]

        return summation

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

        mapped = sorted([(x.sum(output) if type(x) == Layer else output[x], x, idx, name) for idx, (x, name) in enumerate(self.elems)], key=lambda x: -x[0])

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




