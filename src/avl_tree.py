from collections import deque
from typing import Optional, Any, Dict, List, Tuple, Callable

class Node:
    def __init__(self, key: float, payload: Dict[str, Any]):
        self.key = float(key)                    # MÉTRICA: media de cambio de temperatura
        self.data = payload                      # {ISO3, Country, mean_change, series, ...}
        self.left: Optional["Node"] = None
        self.right: Optional["Node"] = None
        self.parent: Optional["Node"] = None
        self.height = 1

    @property
    def balance_factor(self) -> int:
        return (self.right.height if self.right else 0) - (self.left.height if self.left else 0)


    def level(self) -> int:
        lvl, cur = 0, self
        while cur.parent is not None:
            lvl += 1
            cur = cur.parent
        return lvl

    def grandparent(self) -> Optional["Node"]:
        return self.parent.parent if self.parent else None

    def uncle(self) -> Optional["Node"]:
        gp = self.grandparent()
        if not gp or not self.parent:
            return None
        return gp.right if gp.left is self.parent else gp.left


class AVLTree:
    def __init__(self):
        self.root: Optional[Node] = None


    def _h(self, n: Optional[Node]) -> int:
        return n.height if n else 0

    def _update(self, n: Node) -> None:
        n.height = 1 + max(self._h(n.left), self._h(n.right))

    def _rot_right(self, y: Node) -> Node:
        x = y.left
        T2 = x.right if x else None

        x.right = y
        x.parent = y.parent
        y.parent = x
        y.left = T2
        if T2: T2.parent = y

        self._update(y)
        self._update(x)
        return x

    def _rot_left(self, x: Node) -> Node:
        y = x.right
        T2 = y.left if y else None

        y.left = x
        y.parent = x.parent
        x.parent = y
        x.right = T2
        if T2: T2.parent = x

        self._update(x)
        self._update(y)
        return y

    def _rebalance(self, n: Node) -> Node:
        self._update(n)
        b = n.balance_factor

        # Right heavy
        if b > 1:
            if n.right and n.right.balance_factor < 0:   
                n.right = self._rot_right(n.right)
                if n.right: n.right.parent = n
            return self._rot_left(n)                     
        
        # left heavy
        if b < -1:
            if n.left and n.left.balance_factor > 0:     
                n.left = self._rot_left(n.left)
                if n.left: n.left.parent = n
            return self._rot_right(n)                    

        return n



    def insert(self, key: float, payload: Dict[str, Any]) -> None:
        """Inserta por la MÉTRICA (media). Si hay empate exacto, empuja a la derecha con epsilon."""
        def _ins(r: Optional[Node], k: float, p: Dict[str, Any]) -> Node:
            if not r:
                return Node(k, p)
            if k < r.key:
                r.left = _ins(r.left, k, p); r.left.parent = r
            elif k > r.key:
                r.right = _ins(r.right, k, p); r.right.parent = r
            else:
                # mismo valor de media: mantener propiedad BST con un pequeño desplazamiento
                r.right = _ins(r.right, k + 1e-9, p); r.right.parent = r
            return self._rebalance(r)
        self.root = _ins(self.root, float(key), payload)

    def _min_node(self, n: Node) -> Node:
        cur = n
        while cur.left:
            cur = cur.left
        return cur

    def delete(self, key: float) -> None:

        def _del(r: Optional[Node], k: float) -> Optional[Node]:
            if not r:
                return None
            if k < r.key:
                r.left = _del(r.left, k)
                if r.left: r.left.parent = r
            elif k > r.key:
                r.right = _del(r.right, k)
                if r.right: r.right.parent = r
            else:
                # nodo encontrado
                if not r.left or not r.right:
                    child = r.left if r.left else r.right
                    if child: child.parent = r.parent
                    return child
                # dos hijos: usar sucesor en in-order
                succ = self._min_node(r.right)
                r.key, r.data = succ.key, succ.data
                r.right = _del(r.right, succ.key)
                if r.right: r.right.parent = r
            return self._rebalance(r) if r else None

        self.root = _del(self.root, float(key))

    def find_by_key(self, key: float) -> Optional[Node]:
        cur = self.root
        t = float(key)
        while cur:
            if t < cur.key:
                cur = cur.left
            elif t > cur.key:
                cur = cur.right
            else:
                return cur
        return None

    def find_by_key_approx(self, key: float, tol: float = 1e-6):

        n = self.find_by_key(key)
        if n:
            return n

  
        t = float(key)
        def _search(nd):
            if not nd:
                return None
            if abs(nd.key - t) <= tol:
                return nd
            if t < nd.key - tol:
                return _search(nd.left)
            if t > nd.key + tol:
                return _search(nd.right)

            return _search(nd.left) or _search(nd.right)

        return _search(self.root)

    def find_by_key_rounded(self, key: float, ndigits: int = 6):

        tgt = round(float(key), ndigits)
        return self._dfs_find(self.root, lambda nd: round(nd.key, ndigits) == tgt)

    def find_nearest(self, key: float):

        cur, best, best_diff = self.root, None, float("inf")
        t = float(key)
        while cur:
            d = abs(cur.key - t)
            if d < best_diff:
                best, best_diff = cur, d
            cur = cur.left if t < cur.key else cur.right
        return best


    def _dfs_find(self, n: Optional[Node], pred: Callable[[Node], bool]) -> Optional[Node]:
        if not n: return None
        if pred(n): return n
        left = self._dfs_find(n.left, pred)
        if left: return left
        return self._dfs_find(n.right, pred)

    def find_by_iso3(self, iso3: str) -> Optional[Node]:
        iso3 = (iso3 or "").strip().upper()
        return self._dfs_find(
            self.root,
            lambda nd: (str(nd.data.get("ISO3") or "").strip().upper()) == iso3
        )

    def level_order_recursive_grouped_iso3(self):
        res = []
        def dfs(n, d):
            if not n: return
            if len(res) == d: res.append([])
            res[d].append(n.data.get("ISO3",""))
            dfs(n.left, d+1); dfs(n.right, d+1)
        dfs(self.root, 0)
        return res

