import math
from typing import List, Dict, Tuple, Optional
import heapq

class LevelNode:

    def __init__(self, index, members: List['LevelNode']):
        self.members = members  # members is list of LevelNodes
        self.index = index  # corresponds to the index of the output vector.
        # If index_offset, then we assume there is a background class at idx=0
        pass

    def get_members(self) -> List['LevelNode']:
        return self.members
        pass

    def is_leaf(self) -> bool:
        return not len(self.members)
        pass

    def top_member(self, output) -> Optional['LevelNode']:
        sorted_members = self.get_sorted_members(output)

        return sorted_members[0][1] if len(sorted_members) > 0 else None

    def get_value(self, output) -> float:
        return output[self.index]
        pass

    def get_logistic_value(self, output) -> float:
        return math.exp(self.get_value(output))

    def get_member_logistic_sum(self, output: List[float]) -> float:
        return sum([x.get_logistic_value(output) for x in self.members])


    def get_sorted_members(self, output) -> List[Tuple[float, 'LevelNode']]:
        """

        :param output:
        :return: Sorted list of tuples (normed_probability, LevelNode) ordered descending
        """
        return sorted([(x.get_logistic_value(output) / self.get_member_logistic_sum(output), x) for x in self.members],
                      key=lambda x: -x[0])
        pass

class FlatEvaluator:
    def __init__(self, leaf_indices):
        self.leaf_indices = leaf_indices

    def top(self, output_vector):
        print(len(output_vector), len(self.leaf_indices))
        sorted_tuples = sorted([(output_vector[x], x) for x in self.leaf_indices], key=lambda x: x[0])
        print(sorted_tuples)
        return sorted_tuples[0][1]



class Evaluator:
    def __init__(self, root_node: LevelNode):
        self.root = root_node

        pass

    def k_deep_top_greedy(self, k, output_vector):

        current_node = self.root
        for i in range(0, k):
            current_node = current_node.top_member(
                output_vector)  # this cannot be None, as a non-leaf node must at least have 1 member

        return current_node.index


    def top_greedy(self, output_vector):
        current_node = self.root
        current_probability = 1
        while not current_node.is_leaf():
            sum_prob = current_node.get_member_logistic_sum(output_vector)
            current_node = current_node.top_member(output_vector) # this cannot be None, as a non-leaf node must at least have 1 member
            current_probability *= current_node.get_logistic_value(output_vector) / sum_prob

        return (current_probability, current_node.index)

    def top_dijkstra(self):

        pass


    def top_k_dijkstra(self, output_vector):

        """
        performs Dijkstra search down the tree.

        :return:
        """
        heap = []
        root_sum = self.root.get_member_logistic_sum(output_vector)
        for item in self.root.get_members():
            heapq.heappush(heap, (-item.get_logistic_value(output_vector) / root_sum, item)) # use negative for max-heap

        while len(heap):
            negative_prob, lvlnode = heapq.heappop(heap)
            if lvlnode.is_leaf():
                return (-negative_prob, lvlnode.index)

            node_sum = lvlnode.get_member_logistic_sum(output_vector)
            for item in lvlnode.get_members():
                heapq.heappush(heap, (negative_prob * item.get_logistic_value(output_vector) / node_sum, item))

        return None




