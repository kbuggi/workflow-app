import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
import sys, os

# pip install matplotlib networkx


class SimpleDAG:
    # A wrapper around NetworkX to enable graph-centric calculation
    # NetworkX: https://aric.hagberg.org/papers/hagberg-2008-exploring.pdf
    # Aric A. Hagberg, Daniel A. Schult and Pieter J. Swart, “Exploring network structure, dynamics, and function using NetworkX”, in Proceedings of the 7th Python in Science Conference (SciPy2008), Gäel Varoquaux, Travis Vaught, and Jarrod Millman (Eds), (Pasadena, CA USA), pp. 11–15, Aug 2008

    # when calculating critical path, nx applies weights to edges not nodes.
    # this wrapper creates "fake" nodes and edges to simulate the behaviour of weights on nodes.
    # these fake nodes can be filtered out for clarity
    # no rules are enforced; checks are done by caller (like Stream)
    # possible to check if there DAG rules are adhered to by is_dag()
    # possible to sanity check DAG visually by plot()
    #

    def __init__(self):
        self.graph = nx.DiGraph()
        self.dag = self.graph
        self.current_column = 0

    def clear(self):
        self.graph.clear()

    def add_node(self, name: str, new_column=True, duration=0, column=None):
        """Add a node with a duration attribute."""
        name = str(name)
        duration = int(duration)
        if column:
            column = int(column)
        elif new_column:
            self.current_column += 1
            column = self.current_column
        else:
            column = self.current_column

        end_task = name + ".end"
        self.graph.add_node(name, duration=duration, column=column)
        self.graph.add_node(end_task, duration=0, column=column)
        self.graph.add_edge(name, end_task, weight=duration)

    def add_edge(self, from_node: str, to_node: str):
        """Add an edge if it doesn't already exist. Explicit edges/dependencies have 0 weight"""
        from_node = str(from_node)
        to_node = str(to_node)
        end_task = from_node + ".end"

        if not self.graph.has_edge(end_task, to_node):
            self.graph.add_edge(end_task, to_node, weight=0)
        else:
            print(f"Edge from {from_node} to {to_node} already exists. Skipping.")

    def add_node_following(self, name: str, duration: int, following: str):
        """Add a node with a duration attribute following a previous node."""
        name = str(name)
        duration = int(duration)
        following = str(following)

        column = self.graph.nodes[following]["column"]
        self.add_node(name, duration=duration, column=column)
        self.add_edge(following, name)

    def has_edge(self, from_node: str, to_node: str) -> bool:
        from_node = str(from_node)
        to_node = str(to_node)
        end_task = from_node + ".end"
        return self.graph.has_edge(end_task, to_node)

    def remove_edge(self, from_node: str, to_node: str) -> bool:
        from_node = str(from_node)
        to_node = str(to_node)
        self.graph.remove_edge(from_node, to_node)
        return

    def remove_in_edges(self, name: str):
        """remove all edges into node; for example a Stream node"""
        name = str(name)
        # force list to create a static copy, and avoid RuntimeError: dictionary changed size during iteration
        edges = list(self.graph.in_edges(name))
        for from_node, to_node in edges:
            self.graph.remove_edge(from_node, to_node)

    def update_duration(self, name: str, new_duration: int, floor=0):
        """Update duration of an existing node."""
        name = str(name)
        new_duration = int(new_duration)
        if new_duration < floor:
            return

        end_task = name + ".end"
        self.graph[name][end_task]["weight"] = new_duration
        self.graph.nodes[name]["duration"] = new_duration

    def critical_path_length(self) -> int:
        try:
            return nx.dag_longest_path_length(self.graph, weight="weight")
        except nx.NetworkXUnfeasible as e:
            print(f"Error calculating critical path: {e}")
            raise ValueError(e)

    def critical_path(self) -> list:
        try:
            longest_path = nx.dag_longest_path(self.graph, weight="weight")
            filtered_longest_path = [s for s in longest_path if not s.endswith(".end")]
        except nx.NetworkXUnfeasible as e:
            print(f"Error calculating critical path: {e}")
            raise ValueError(e)
        return filtered_longest_path

    def critical_path_all(self) -> list:
        longest_path = nx.dag_longest_path(self.graph, weight="weight")
        return longest_path

    def str_critical_path_all(self, multiline=True) -> str:
        if multiline:
            multiline = "\n\t"
        else:
            multiline = ""
        longest_path = nx.dag_longest_path(self.graph, weight="weight")
        if not longest_path:
            return "Critical Path: empty"
        elif len(longest_path) == 1:
            node = longest_path[0]
            return "Critical Path: {node}"
        result = "Critical Path: "
        result_weight = 0
        node = longest_path[0]
        for index in range(1, len(longest_path)):
            next_node = longest_path[index]
            weight = self.graph[node][next_node]["weight"]
            result += f"{multiline} {node} -> {next_node} = {weight} "
            result_weight += weight
            node = next_node
        result += f"\nTotal Weight: {result_weight}"
        return result

    def in_edges(self, name: str) -> list:
        """all edges into node - note this will not filter out the fake .end edges"""
        name = str(name)
        return self.graph.in_edges(name)

    def in_nodes(self, name: str) -> list:
        """all nodes into a node"""
        incoming_edges = self.in_edges(name)
        incoming_nodes = []
        for from_node, to_node in incoming_edges:
            if from_node.endswith(".end"):
                from_node = from_node[:-4]  # strip .end
                if from_node not in incoming_nodes:
                    incoming_nodes.append(from_node)
        return incoming_nodes

    def is_dag(self) -> bool:
        return nx.is_directed_acyclic_graph(self.dag)

    def find_cycle(self, verbose=True) -> list:
        try:
            cycle = nx.find_cycle(self.dag, orientation="original")
            if verbose:
                c = len(cycle)
                print(f"⚠️  {c} cycle(s) detected in DAG:", cycle)
            return cycle
        except nx.exception.NetworkXNoCycle:
            if verbose:
                print("✅ No cycle detected")
            return []

    def _old_str(self):
        nodes = list(self.graph.nodes)
        filtered_nodes = []
        for node in self.graph.nodes:
            if node.endswith(".end"):
                continue
            duration = self.graph.nodes[node]["duration"]
            node_with_duration = f"{node}( {duration} )"
            filtered_nodes.append(node_with_duration)
        s = ", ".join(filtered_nodes)
        return "Nodes (with duration):" + s

    def __str__(self):
        nodes = list(self.graph.nodes)
        columns = {}
        for node in self.graph.nodes:
            if node.endswith(".end"):
                continue
            duration = self.graph.nodes[node]["duration"]
            column = self.graph.nodes[node]["column"]
            node_with_duration = f"{node}( {duration} )"
            if column not in columns:
                columns[column] = []
            columns[column].append(node_with_duration)
        column_strings = []
        for column in columns:
            s = ", ".join(columns[column])
            s = f"column {column}: {s}"
            column_strings.append(s)
        result = ". ".join(column_strings)
        result = f"Nodes (with duration): {result}"
        return result

    def plot(self, svg_file=None, title=None):
        """plot DAG using columns defined in nodes and ordering by depth"""
        import matplotlib.pyplot as plt
        import networkx as nx

        def wrap_label(text, width=12):
            import textwrap

            text = text.replace("/", "/\n")
            text = text.replace(".", "\n.")
            return "\n".join(textwrap.wrap(text, width=width))

        if not self.is_dag():
            raise ValueError("Cannot plot: graph contains cycles.")

        if title:
            title = str(title)
        elif svg_file:
            title = os.path.basename(svg_file)
        else:
            title = "SimpleDAG Plot"

        # Calculate depth (vertical level) for each node based on longest path from root
        node_depth = {}
        for node in nx.topological_sort(self.dag):
            preds = list(self.dag.predecessors(node))
            if not preds:
                node_depth[node] = 0
            else:
                node_depth[node] = max(node_depth[p] + 1 for p in preds)

        # Compute position using column (x) and depth (y)
        x_gap, y_gap = 2.5, 2
        pos = {}
        for node in self.dag.nodes:
            col = self.dag.nodes[node].get("column", 0)
            depth = node_depth.get(node, 0)
            x = col * x_gap
            y = depth * y_gap * -1  # Y increases downward
            pos[node] = (x, y)

        # Highlight critical path
        try:
            crit_path = set(self.critical_path_all())
        except Exception:
            crit_path = set()

        node_colors = []
        node_border_colors = []
        for node in self.dag.nodes:
            node_colors.append("lightblue")
            if node in crit_path:
                node_border_colors.append("darkblue")
            else:
                node_border_colors.append("lightblue")  # softened from black

        labels = {
            node: f"{node}\n({self.dag.nodes[node].get('duration', '')})"
            for node in self.dag.nodes
        }
        labels = {
            node: f"{wrap_label(str(node))}\n({self.dag.nodes[node].get('duration', '')})"
            for node in self.dag.nodes
        }

        # Dynamically size canvas
        xs, ys = zip(*pos.values())
        width = max(xs) - min(xs) + x_gap * 2
        height = max(ys) - min(ys) + y_gap * 2
        fig, ax = plt.subplots(figsize=(width, height))

        # Draw rectangular nodes rather than circles to fix labels
        nx.draw_networkx_nodes(
            self.dag,
            pos,
            node_color=node_colors,
            edgecolors=node_border_colors,
            node_shape="s",  # square / rect node
            node_size=4000,  # larger for long text
            linewidths=2.5,
            ax=ax,
        )

        # Work out which edges are on critical path

        crit_edges = [
            (u, v) for u, v in self.dag.edges() if u in crit_path and v in crit_path
        ]
        noncrit_edges = [
            (u, v) for u, v in self.dag.edges() if (u, v) not in crit_edges
        ]

        # Draw non-critical edges in gray
        nx.draw_networkx_edges(
            self.dag,
            pos,
            edgelist=noncrit_edges,
            ax=ax,
            edge_color="gray",
            arrows=True,
            arrowstyle="-|>",
            arrowsize=25,
            min_source_margin=30,
            min_target_margin=30,
            connectionstyle="arc3,rad=0.0",
        )

        # Draw critical path edges in dark blue
        nx.draw_networkx_edges(
            self.dag,
            pos,
            edgelist=crit_edges,
            ax=ax,
            edge_color="darkblue",
            arrows=True,
            arrowstyle="-|>",
            arrowsize=25,
            min_source_margin=30,
            min_target_margin=30,
            connectionstyle="arc3,rad=0.0",
        )

        # Draw labels
        edge_labels = {
            (u, v): f"{self.dag.edges[u, v].get('weight', '')}"
            for u, v in self.dag.edges()
        }
        nx.draw_networkx_edge_labels(
            self.dag, pos, edge_labels=edge_labels, ax=ax, font_size=9
        )

        nx.draw_networkx_labels(self.dag, pos, labels, font_size=10, ax=ax)

        ax.set_title(title, fontsize=16, pad=20)

        if svg_file:
            plt.savefig(svg_file, format="svg")
            print(f"Saved DAG to: {svg_file}")
        else:
            plt.show()


if __name__ == "__main__":
    dag = SimpleDAG()

    dag.add_node("a1", duration=5, column=1)
    dag.add_node("b1", duration=3, column=2)
    dag.add_node_following("a2", 2, "a1")
    dag.add_node_following("abcdefghijdfdfd", 2, "b1")

    dag.add_edge("a1", "b1")

    # dag.add_edge("a2", "a1")
    # dag.add_edge("b1", "a1")

    print(dag)
    print(dag.is_dag())
    print(dag.find_cycle())
    dag.plot("output/plot.svg")

    print("critical_path_all", dag.critical_path_all())

    g = SimpleDAG()
    g.add_node("a1")
    g.add_node_following("a2", 2, "a1")
    g.add_node_following("a3", 2, "a2")
    g.add_node_following("a4", 2, "a3")
    g.add_node_following("a5", 2, "a4")
    g.add_node("b1")
    g.add_node_following("b2", 3, "b1")
    g.add_node_following("b3", 3, "b2")
    g.add_edge("a3", "b1")
    g.add_edge("a4", "b1")
    g.add_edge("a5", "b1")
    g.plot("output/plot2.svg")

    # create a cycle
    # g.add_edge("a5","a1")

    print(g)
    print("\n")
    print("critical_path", g.critical_path())
    print("\n")

    print("critical_path_all", g.critical_path_all())
    print("\n")

    print("critical_path_length", g.critical_path_length())
    print("\n")

    print("str_critical_path_all", g.str_critical_path_all())
    print("\n")

    print("incoming nodes to b1", g.in_nodes("b1"))
    print("\n")

    print("incoming edges to b1", g.in_edges("b1"))
    print("\n")

    g.remove_in_edges("b1")
    g.plot("output/plot3.svg")

    print("incoming edges to b1", g.in_edges("b1"))
    print("\n")
