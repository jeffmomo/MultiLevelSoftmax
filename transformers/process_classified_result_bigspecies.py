import math
import os
import sys

from hierarchy import hierarchical_eval, get_hierarchy

###########


tree = get_hierarchy.pruned_tree
definitions_list = []
tree.get_definitions(definitions_list)
# print(definitions_list)
print(len(definitions_list))

tree.assign_indices(definitions_list)



mapping = {}
layer, _ = tree.generate_layer(mapping)
print("map size", len(mapping))

reverse_tree = {}
tree.generate_reverse_tree(reverse_tree, leaf_only=False)

evaluator = hierarchical_eval.LayerEvaluator(layer, definitions_list)

####################



#################
#pipe stuff here#
#################

TO_WEB_SERVER_PIPE = '/home/jeff/Workspace/models/slim/done_pipe.fifopipe'

try:
  os.mkfifo(TO_WEB_SERVER_PIPE)
except Exception as e:
  pass

def pipe_write(content):
  outpipe = open(TO_WEB_SERVER_PIPE, 'w')
  outpipe.write(content + '>>>EOF<<<')
  outpipe.close()
###

label_map = get_hierarchy.native_to_hierarchical_translation_map(tree)

for line in sys.stdin:
    values = line
    
    if (not len(values)) or values[0] != '>':
        print('not gucci')
        print(values)
        continue

    print('gucc')
    splitted = values[1:].split('|')
    orig_data = [float(f) for f in splitted[0].split(',')]

    data = [0] * len(orig_data)

    for i in range(len(orig_data)):
        data[label_map[i]] = (orig_data[i])





    # data_exp_sum = sum([math.exp(x) for x in data])
    # data = [math.exp(x) / data_exp_sum for x in data]
    #

    top5 = []
    for name, prob in [(definitions_list[x[0]], x[1]) for x in sorted(list(enumerate(data)), key=lambda x: -x[1])[0:5]]:
        top5.append(name)
        top5.append(prob)
    print(top5)



    index = int(splitted[1])
    name = '.'.join(map(lambda x: x.lower(), splitted[3].replace("\n", "").replace(' ', '.').split('.')))
    priors_used = ''

    if name in reverse_tree:
        priors_used = name
        tmp_evaluator = hierarchical_eval.LayerEvaluator(layer, definitions_list, reverse_tree[name][::-1])
        result = tmp_evaluator.dijkstra_top(data)
        thresh_result = tmp_evaluator.dijkstra_threshold(data, 0.707)
        del tmp_evaluator
        pass
    else:
        result = evaluator.dijkstra_top(data)
        #thresh_result = evaluator.dijkstra_with_initial_domain(['animalia.chordata'], data, 0.5)
        thresh_result = evaluator.dijkstra_threshold(data, 0.707)
        pass


    print(index)
    print(result)

    print(thresh_result)
    print(definitions_list[data.index(max(data))])
    print(name)

    pipe_write(",".join([str(x) for x in ([result[0], result[1], thresh_result[0], thresh_result[1], thresh_result[2], index, splitted[2], priors_used] + top5 + [splitted[4]])]))
