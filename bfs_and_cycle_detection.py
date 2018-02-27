
def BFS(root, target):
    queue = [root]      # using list as a queue (first in first out)
    visited = set()
    while queue:        # while there is still have node
        current = queue.pop(0)        # get first one
        if current is target:        # check if it is target
            return current
        visited.add(current)          # mark as visited
        for node in current.connected:   
        # Added all not visited connected nodes to queue
            if node not in visited:
                queue.append(node)


def cycle_detector(root, current_path, result):
    if root in current_path:             # check if it is a cycle or not
        # if it is a cycle, add path of cycle to result.
        result.append(current_path[current_path.index(root):])
    else:
        # if it is not a cycle, add this node to path list
        current_path.append(root)
    for node in root.connected:  # check all connected node
        # recursive with connected node
        cycle_detector(node, current_path, result)


def cycle_detection(root):
    """
    Find all cycle in a graph
    :param root: graph
    :return: a list of cycle path list
    """
    result = []
    cycle_detector(root, [], result)
    return result
