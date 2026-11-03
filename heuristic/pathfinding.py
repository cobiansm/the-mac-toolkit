import math
# dropdown menu
HEURISTICS = ["Dijkstra (none)", "Manhattan", "Euclidean"]

def manhattan_distance(node, end):
  return abs(node[0] - end[0]) + abs(node[1] - end[1])

def euclidean_distance(node, end):
  return math.sqrt((node[0] - end[0])**2+(node[1] - end[1])**2)

def no_heuristic(node, end):
  # plain dijkstra: no estimation
  return 0

# dropdown name -> heuristic function
HEURISTIC_FUNCTIONS = {
  "Dijkstra (none)": no_heuristic,
  "Manhattan": manhattan_distance,
  "Euclidean": euclidean_distance,
}

# moves allowed in the grid: up, down, left, right
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def dijkstra(graph, start, end , heuristic):
  # graph: grid as list of lists of bool (True = obstacle)
  # start, end: (row, col); heuristic: one of the names in HEURISTICS
  # returns (visited_order, path); path is [] if there is no path
  # get the size of the graph (grid)
  size = len(graph)
  distances = {}
  visited = {}

  # heuristic function selected in the dropdown
  h = HEURISTIC_FUNCTIONS[heuristic]

  # initialize start node with distance 0 and frontier with start node
  # frontier stores (node, priority) where priority = g + h
  distances[start] = 0
  frontier = [(start, 0)]

  # track visited nodes and previous node
  visited_order = []
  previous = {}

  # continue until frontier is empty
  while frontier:
    min_dist = 0

    # search for the lowest cost (manual priority queue)
    for i in range(1, len(frontier)):
      if frontier[i][1] < frontier[min_dist][1]:
        min_dist = i

    # remove the node with the minimum cost
    node, cost = frontier.pop(min_dist)

    # skip if already visited
    if visited.get(node, False):
      continue

    # else mark it as visited and save the order for the animation
    visited[node] = True
    visited_order.append(node)

    # stop when the end is reached: its distance is already the shortest
    if node == end:
      break

    # explore the 4 neighbors of the current node
    for move in MOVES:
      neighbor = (node[0] + move[0], node[1] + move[1])

      # skip neighbors outside the grid, obstacles and visited nodes
      if not (0 <= neighbor[0] < size and 0 <= neighbor[1] < size):
        continue
      if graph[neighbor[0]][neighbor[1]] or visited.get(neighbor, False):
        continue

      # each step costs 1
      new_cost = distances[node] + 1

      # update if a shorter path is found
      if new_cost < distances.get(neighbor, float('inf')):
        distances[neighbor] = new_cost
        previous[neighbor] = node

        # add the neighbor to the frontier with priority g + h
        frontier.append((neighbor, new_cost + h(neighbor, end)))

  # no path: the end was never reached
  if end not in visited:
    return visited_order, []

  # rebuild the path going back from the end to the start
  path = [end]
  while path[-1] != start:
    path.append(previous[path[-1]])
  path.reverse()

  return visited_order, path
