from functools import reduce





class Layer:


    def __init__(self, elems):
        self.elems = elems

    def getChildren(self):

        if type(self.elems[0]) != Layer:
            return self.elems

        return reduce(lambda a, b: a + b, [x.getChildren() for x in self.elems], [])

    def avg(self, output):
        summation = 0
        children = self.getChildren()
        for elem in children:
            summation += output[elem]

        return summation / len(children)

    def evaluateWithPrior(self, priors, output):
        layer = self.elems
        for idx in priors[:-1]:
            layer = layer[idx].elems

        layer = layer[priors[-1]]

        return layer.evaluate(output)

    def evaluate(self, output):

        if type(self.elems[0]) != Layer:
            mapped = sorted([(output[x], x) for x in self.getChildren()], key=lambda x: -x[0])
            return mapped[0][1]

        mapped = sorted([(x.avg(output), x) for x in self.elems], key=lambda x: -x[0])

        # if mapped[0][1] != None:
        return mapped[0][1].evaluate(output)

    # return mapped[0].getChildren[0]


print(Layer([Layer([2, 3, 4]), Layer([1,0,5])]).evaluate([1,2,3,4,5,6]))

print(
    Layer([
        Layer([
            Layer([2, 0]),
            Layer([4])
        ]),
        Layer([1, 3, 5])
    ])
    .evaluateWithPrior([0, 0], [1, 2, 3, 4, 4, 6]))

# .evaluate([1,2,3,4,4,6]))


# print(Layer([Layer([1,2]), Layer([3, 4])]).evaluate([0, 3, 3.1, 4, 1]))




# To get the top k probabilities, may need to perform djikstra/A* search through the hierarchy.
# first we need to actually derive probabilities instead of just producing the top result



