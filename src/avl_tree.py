from collections import deque
from typing import Optional, Any, Dict, List, Tuple, Callable
import pandas as pd

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

    def get_nodes(self) -> List[Node]:
        if self.root is None:
            return []
        
        nodes = []
        queue = deque([self.root]) 
        
        while queue:
            current = queue.popleft()
            nodes.append(current)
            
            if current.left:
                queue.append(current.left)
            if current.right:
                queue.append(current.right)
        
        return nodes

    def punto_4a(self, año: int) -> List[Tuple[str, float, float]]:
        nodos = self.get_nodes()
        
        if not nodos:
            return []
        
        if año < 1961 or año > 2022:
            raise ValueError(f"Año {año} fuera de rango (1961-2022)")

        año_str = str(año)  # Convertir a string para buscar en el diccionario
        
        temperaturas_año = []
        for nodo in nodos:
            series = nodo.data.get("series", {})  # Ahora es un diccionario
            if año_str in series:
                temp = series[año_str]
                if not pd.isna(temp):
                    temperaturas_año.append(temp)
        
        if not temperaturas_año:
            return []
        
        promedio_año = sum(temperaturas_año) / len(temperaturas_año)
        
        resultados = []
        for nodo in nodos:
            series = nodo.data.get("series", {})
            if año_str in series:
                temp_pais = series[año_str]
                if not pd.isna(temp_pais) and temp_pais > promedio_año:
                    iso3 = nodo.data.get("ISO3", "N/A")
                    resultados.append((iso3, temp_pais, promedio_año))
        
        return resultados

    def punto_4b(self, año: int) -> List[Tuple[str, float, float]]:
        nodos = self.get_nodes()
        
        if not nodos:
            return []
        
        if año < 1961 or año > 2022:
            raise ValueError(f"Año {año} fuera de rango (1961-2022)")
        
        año_str = str(año)  # Convertir a string
        
        todas_temperaturas = []
        for nodo in nodos:
            series = nodo.data.get("series", {})
            for temp in series.values():  # Iterar sobre todos los valores del diccionario
                if not pd.isna(temp):
                    todas_temperaturas.append(temp)
        
        if not todas_temperaturas:
            return []
        
        promedio_total = sum(todas_temperaturas) / len(todas_temperaturas)
        
        resultados = []
        for nodo in nodos:
            series = nodo.data.get("series", {})
            if año_str in series:
                temp_pais = series[año_str]
                if not pd.isna(temp_pais) and temp_pais < promedio_total:
                    iso3 = nodo.data.get("ISO3", "N/A")
                    resultados.append((iso3, temp_pais, promedio_total))
        
        return resultados

    def punto_4c(self, valor_umbral: float) -> List[Tuple[str, float]]:
        nodos = self.get_nodes()
        
        resultados = []
        for nodo in nodos:
            if nodo.key >= valor_umbral:
                iso3 = nodo.data.get("ISO3", "N/A")
                resultados.append((iso3, nodo.key))

        return resultados

    def mostrar_punto4a(self, año: int) -> None:
        try:
            resultados = self.punto_4a(año)
            print(f"\n{'='*60}")
            print(f"INCISO A - AÑO {año}")
            print(f"{'='*60}")
            
            # DEBUG CRÍTICO - Ver qué retorna punto_4a
            print(f"DEBUG: resultados = {resultados}")
            print(f"DEBUG: tipo de resultados = {type(resultados)}")
            print(f"DEBUG: longitud de resultados = {len(resultados)}")
            
            if not resultados:
                print("No se encontraron resultados")
                print("DEBUG: La lista 'resultados' está vacía")
                return
            
            print(f"Promedio del año {año}: {resultados[0][2]:.3f}°C")
            print("Países con temperatura mayor al promedio:")
            print("-" * 50)
            
            for i, (iso, temp, prom) in enumerate(resultados, 1):
                diferencia = temp - prom
                print(f"{i:2d}. {iso}: {temp:.3f}°C (+{diferencia:.3f}°C)")
            
            print(f"\nTotal: {len(resultados)} países")
            
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
            import traceback
            traceback.print_exc()

    def mostrar_punto4b(self, año: int) -> None:
        try:
            resultados = self.punto_4b(año)
            print(f"\n{'='*60}")
            print(f"INCISO B - AÑO {año}")
            print(f"{'='*60}")
            
            if not resultados:
                print("No se encontraron resultados")
                return
            
            print(f"Promedio total: {resultados[0][2]:.3f}°C")
            print("Países con temperatura menor al promedio total:")
            print("-" * 50)
            
            for i, (iso, temp, prom_total) in enumerate(resultados, 1):
                diferencia = prom_total - temp
                print(f"{i:2d}. {iso}: {temp:.3f}°C (-{diferencia:.3f}°C)")
            
            print(f"\nTotal: {len(resultados)} países")
            
        except ValueError as e:
            print(f"Error: {e}")

    def mostrar_punto4c(self, valor_umbral: float) -> None:
        resultados = self.punto_4c(valor_umbral)
        print(f"\n{'='*60}")
        print(f"INCISO C - TEMPERATURA MEDIA ≥ {valor_umbral}°C")
        print(f"{'='*60}")
        
        if not resultados:
            print(f"No hay países con temperatura media ≥ {valor_umbral}°C")
            return
        
        print(f"Países con temperatura media ≥ {valor_umbral}°C:")
        print("-" * 50)
        
        for i, (iso, temp_media) in enumerate(resultados, 1):
            print(f"{i:2d}. {iso}: {temp_media:.3f}°C")
        
        print(f"\nTotal: {len(resultados)} países")