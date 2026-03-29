

class UnionFind:
    """
    Disjoint Set Union with Path Compression and Union by Rank.

    In the context of ResQFlow:
    - Each city location is a node in the DSU.
    - Two nodes are "connected" if they are in the same component (reachable via roads).
    - When roads are blocked (simulated), we can detect which areas become isolated.
    """

    def __init__(self, nodes):
        """
        Initialize each node as its own parent (self-loop).

        Args:
            nodes: iterable of node identifiers (location names)
        """
        self.parent = {node: node for node in nodes}
        self.rank = {node: 0 for node in nodes}
        self.component_count = len(self.parent)

    def find(self, x):
        """
        Find root of x with path compression.
        All nodes along the path directly point to the root after this call.
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]

    def union(self, x, y):
        """
        Merge sets containing x and y using union by rank.
        The tree with lower rank is attached under the higher rank root.

        Returns:
            True if x and y were in different sets (merge happened)
            False if they were already connected
        """
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False  # already connected

        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

        self.component_count -= 1
        return True

    def connected(self, x, y):
        """Check if two nodes are in the same component."""
        if x not in self.parent or y not in self.parent:
            return False
        return self.find(x) == self.find(y)

    def get_components(self):
        """
        Return all disjoint components as a dict:
        { root_id: [list of nodes in component] }
        """
        components = {}
        for node in self.parent:
            root = self.find(node)
            if root not in components:
                components[root] = []
            components[root].append(node)
        return components

    def get_component_count(self):
        """Total number of disconnected components."""
        return len(set(self.find(n) for n in self.parent))


def build_connectivity_map(graph, blocked_edges=None):
    """
    Build a Union-Find structure from the city graph.
    Optionally simulate road disruptions by blocking specific edges.

    Args:
        graph: CityGraph instance
        blocked_edges: list of (u, v) tuples representing blocked roads

    Returns:
        UnionFind instance and connectivity analysis report
    """
    blocked_set = set()
    if blocked_edges:
        for u, v in blocked_edges:
            blocked_set.add((u, v))
            blocked_set.add((v, u))

    nodes = graph.get_all_nodes()
    uf = UnionFind(nodes)

    edges_processed = 0
    edges_blocked = 0

    for node in nodes:
        for neighbor, _ in graph.get_neighbors(node):
            if (node, neighbor) not in blocked_set:
                uf.union(node, neighbor)
                edges_processed += 1
            else:
                edges_blocked += 1

    components = uf.get_components()
    component_list = [
        {"root": root, "members": sorted(members), "size": len(members)}
        for root, members in components.items()
    ]
    component_list.sort(key=lambda c: -c["size"])

    return uf, {
        "total_nodes": len(nodes),
        "total_components": len(components),
        "edges_active": edges_processed // 2,
        "edges_blocked": edges_blocked // 2,
        "components": component_list,
        "fully_connected": len(components) == 1
    }


def check_pair_connectivity(graph, location_a, location_b, blocked_edges=None):
    """
    Check if two specific locations are reachable from each other
    given current road conditions.

    Returns:
        dict with connected (bool), and full connectivity report
    """
    uf, report = build_connectivity_map(graph, blocked_edges or [])
    reachable = uf.connected(location_a, location_b)

    return {
        "location_a": location_a,
        "location_b": location_b,
        "connected": reachable,
        "connectivity_report": report
    }
