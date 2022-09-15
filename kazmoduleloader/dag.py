from collections import defaultdict


class Graph:
    def __init__(self, vertices):
        self.graph = defaultdict(list)
        self.V = vertices

    def addEdge(self, u, v):
        self.graph[u].append(v)

    def topologicalSort(self):

        in_degree = [0]*(self.V)

        for i in self.graph:
            for j in self.graph[i]:
                in_degree[j] += 1

        queue = []
        for i in range(self.V):
            if in_degree[i] == 0:
                queue.append(i)

        cnt = 0
        top_order = []

        while queue:
            u = queue.pop(0)
            top_order.append(u)

            for i in self.graph[u]:
                in_degree[i] -= 1

                if in_degree[i] == 0:
                    queue.append(i)

            cnt += 1

        # Check if there was a cycle
        if cnt != self.V:
            raise Exception("Cyclical dependencies.")

        return top_order
