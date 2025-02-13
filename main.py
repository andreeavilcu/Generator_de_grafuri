import tkinter as tk
from tkinter import messagebox, ttk
import random
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Graph Generator and MST")

        self.layouts = {
            "Circular": nx.circular_layout,
            "Spring": nx.spring_layout,
            "Spectral": nx.spectral_layout,
            "Shell": nx.shell_layout
        }

        self.create_frames()
        self.create_controls()
        self.create_stats_panel()
        self.create_canvas()

        self.current_graph = None
        self.mst_edges = None
        self.show_nodes = True
        self.show_weights = True
        self.zoom_level = 1.0

    def create_frames(self):
        self.left_frame = tk.Frame(self.root, width=300, bg="lightgrey")
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(side="right", fill="both", expand=True)

        self.canvas_frame = tk.Frame(self.right_frame)
        self.canvas_frame.pack(fill="both", expand=True)

    def create_controls(self):
        tk.Label(self.left_frame, text="Number of nodes:").grid(row=0, column=0, padx=5, pady=5)
        self.node_entry = tk.Entry(self.left_frame)
        self.node_entry.insert(0, "10")
        self.node_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.left_frame, text="Density (p):").grid(row=1, column=0, padx=5, pady=5)
        self.density_entry = tk.Entry(self.left_frame)
        self.density_entry.insert(0, "0.3")
        self.density_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.left_frame, text="Layout:").grid(row=2, column=0, padx=5, pady=5)
        self.layout_var = tk.StringVar(value="Circular")
        self.layout_menu = ttk.Combobox(self.left_frame, textvariable=self.layout_var,
                                        values=list(self.layouts.keys()))
        self.layout_menu.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(self.left_frame, text="MST Algorithm:").grid(row=3, column=0, padx=5, pady=5)
        self.mst_var = tk.StringVar(value="Kruskal")
        self.mst_menu = ttk.Combobox(self.left_frame, textvariable=self.mst_var,
                                     values=["Kruskal", "Prim", "Boruvka"])
        self.mst_menu.grid(row=3, column=1, padx=5, pady=5)

        buttons_frame = tk.Frame(self.left_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=10)

        tk.Button(buttons_frame, text="Generate Graph",
                  command=self.generate_graph).pack(fill="x", pady=2)
        tk.Button(buttons_frame, text="Compute MST",
                  command=self.compute_mst).pack(fill="x", pady=2)
        tk.Button(buttons_frame, text="Toggle Nodes",
                  command=self.toggle_nodes).pack(fill="x", pady=2)
        tk.Button(buttons_frame, text="Toggle Weights",
                  command=self.toggle_weights).pack(fill="x", pady=2)

        zoom_frame = tk.Frame(self.left_frame)
        zoom_frame.grid(row=5, column=0, columnspan=2, pady=5)
        tk.Button(zoom_frame, text="Zoom -",
                  command=lambda: self.zoom(1.2)).pack(side="left", padx=5)
        tk.Button(zoom_frame, text="Zoom +",
                  command=lambda: self.zoom(0.8)).pack(side="left", padx=5)

    def create_stats_panel(self):
        self.stats_frame = tk.LabelFrame(self.left_frame, text="Graph Statistics")
        self.stats_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")
        self.stats_label = tk.Label(self.stats_frame, text="No graph generated")
        self.stats_label.pack(padx=5, pady=5)

    def create_canvas(self):
        self.fig = Figure(figsize=(6, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def generate_erdos_renyi_graph(self, n, p):
        while True:
            G = nx.DiGraph()
            for i in range(n):
                G.add_node(i)

            for i in range(n):
                for j in range(i + 1, n):
                    if random.random() < p:
                        weight = random.randint(1, 10)
                        G.add_edge(i, j, weight=weight)
                        G.add_edge(j, i, weight=weight)

            if nx.is_strongly_connected(G):
                return G

            if p < 0.9:
                p = min(1.0, p + 0.1)
            else:
                messagebox.showwarning("Warning",
                                       "Could not generate connected graph. Trying again...")

    def boruvka_mst(self, G):
        mst_edges = set()
        components = [{node} for node in G.nodes()]

        while len(components) > 1:
            min_edges = []

            for comp in components:
                min_edge = None
                min_weight = float('inf')

                for u in comp:
                    for v, data in G[u].items():
                        if v not in comp and data['weight'] < min_weight:
                            min_weight = data['weight']
                            min_edge = (u, v)

                if min_edge:
                    min_edges.append(min_edge)

            if not min_edges:
                break

            for edge in min_edges:
                mst_edges.add(edge)
                comp1 = next(c for c in components if edge[0] in c)
                comp2 = next(c for c in components if edge[1] in c)
                if comp1 != comp2:
                    comp1.update(comp2)
                    components.remove(comp2)

        return list(mst_edges)

    def compute_mst(self):
        if not self.current_graph:
            messagebox.showerror("Error", "Generate a graph first")
            return

        try:
            G_undirected = self.current_graph.to_undirected()

            if not nx.is_connected(G_undirected):
                raise nx.NetworkXError("Graph is not connected")

            algorithm = self.mst_var.get().lower()
            if algorithm == "boruvka":
                self.mst_edges = self.boruvka_mst(G_undirected)
            else:
                mst = nx.minimum_spanning_tree(G_undirected, algorithm=algorithm)
                self.mst_edges = list(mst.edges())

            self.plot_graph()

        except nx.NetworkXError as e:
            messagebox.showerror("Error", f"MST computation failed: {str(e)}")

    def plot_graph(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        pos = self.layouts[self.layout_var.get()](self.current_graph)

        if self.show_nodes:
            nx.draw_networkx_nodes(self.current_graph, pos,
                                   node_color='violet',
                                   node_size=500,
                                   ax=ax)
            nx.draw_networkx_labels(self.current_graph, pos, ax=ax)

        nx.draw_networkx_edges(self.current_graph, pos,
                               edge_color='black',
                               width=1,
                               arrowsize=20,
                               arrowstyle='->',
                               ax=ax)

        if hasattr(self, 'mst_edges') and self.mst_edges:
            nx.draw_networkx_edges(self.current_graph, pos,
                                   edgelist=self.mst_edges,
                                   edge_color='violet',
                                   width=2,
                                   ax=ax)

        if self.show_weights:
            labels = nx.get_edge_attributes(self.current_graph, 'weight')
            nx.draw_networkx_edge_labels(self.current_graph, pos,
                                         edge_labels=labels,
                                         ax=ax)

        ax.set_xlim(ax.get_xlim()[0] * self.zoom_level,
                    ax.get_xlim()[1] * self.zoom_level)
        ax.set_ylim(ax.get_ylim()[0] * self.zoom_level,
                    ax.get_ylim()[1] * self.zoom_level)

        self.canvas.draw()
        self.update_stats()

    def generate_graph(self):
        try:
            n = int(self.node_entry.get())
            p = float(self.density_entry.get())

            if not (0 <= p <= 1):
                raise ValueError("Density must be between 0 and 1")

            self.current_graph = self.generate_erdos_renyi_graph(n, p)
            self.mst_edges = None
            self.plot_graph()

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def update_stats(self):
        if self.current_graph:
            stats = f"""Nodes: {self.current_graph.number_of_nodes()}
Edges: {self.current_graph.number_of_edges()}
Density: {nx.density(self.current_graph):.3f}
Connected: {nx.is_strongly_connected(self.current_graph)}"""
            self.stats_label.config(text=stats)

    def toggle_nodes(self):
        self.show_nodes = not self.show_nodes
        if self.current_graph:
            self.plot_graph()

    def toggle_weights(self):
        self.show_weights = not self.show_weights
        if self.current_graph:
            self.plot_graph()

    def zoom(self, factor):
        self.zoom_level *= factor
        if self.current_graph:
            self.plot_graph()


if __name__ == "__main__":
    root = tk.Tk()
    app = GraphApp(root)
    root.mainloop()