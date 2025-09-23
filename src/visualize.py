from graphviz import Digraph
from typing import Optional
from src.avl_tree import Node

 #esta parte del codigo es la que se encarga de graficar el arbol

def draw_tree(root: Optional[Node], out_path: str = "tree"):

    dot = Digraph(format="png")
    dot.attr(rankdir="TB")
    dot.attr("graph", nodesep="0.3", ranksep="0.4")
    dot.attr("node", shape="box", fontsize="10")

    def add(n: Optional[Node]):
        if not n: return
        iso = n.data.get("ISO3", "")
        country = n.data.get("Country", "")
        label = f"{iso}\\n{country}\\nmean={n.key:.4f}"
        label += f"\\nBF={n.balance_factor} H={n.height}"
        dot.node(str(id(n)), label)
        if n.left:
            add(n.left); dot.edge(str(id(n)), str(id(n.left)))
        if n.right:
            add(n.right); dot.edge(str(id(n)), str(id(n.right)))
    add(root)
    dot.render(out_path, cleanup=True)  
