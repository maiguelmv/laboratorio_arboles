from src.dataset import (
    load_dataset, to_payload
)
from src.avl_tree import AVLTree

CSV_PATH = "dataset_climate_change.csv"

def build_tree(csv_path: str) -> tuple[AVLTree, object, float, object]:
    df, per_year_mean, global_mean = load_dataset(csv_path)
    tree = AVLTree()

    for _, row in df.iterrows():
        payload = to_payload(row)
        tree.insert(payload["mean_change"], payload)
    return tree, df, global_mean, per_year_mean

def show_node_info(tree: AVLTree, iso3: str):
    node = tree.find_by_iso3(iso3)
    if not node:
        print("No se encontró ese ISO3 en el árbol (¿lo eliminaste?).")
        return
    parent = node.parent.data["ISO3"] if node.parent else None
    gp = node.grandparent().data["ISO3"] if node.grandparent() else None
    uncle = node.uncle().data["ISO3"] if node.uncle() else None
    print(f"ISO3: {node.data['ISO3']}  Country: {node.data.get('Country')}")
    print(f"mean_change (clave): {node.key:.6f}")
    print(f"Nivel: {node.level()}  |  Balance: {node.balance_factor}")
    print(f"Padre: {parent} | Abuelo: {gp} | Tío: {uncle}")

def draw(tree: AVLTree):
    try:
        from src.visualize import draw_tree
        draw_tree(tree.root, out_path="tree")
        print("Árbol renderizado en tree.png")
    except Exception as e:
        print("No pude dibujar el árbol. Asegúrate de tener Graphviz instalado en el sistema.")
        print("Detalle:", repr(e))
        
def delete_all_by_iso3(tree, iso3: str) -> int:
    iso3 = (iso3 or "").strip().upper()
    removed = 0
    while True:
        n = tree.find_by_iso3(iso3)
        if not n: break
        tree.delete(n.key)
        removed += 1
    return removed

def level_order_recursive(tree: AVLTree):
    iso3 = tree.level_order_recursive_iso3()
    print("Recorrido por niveles (recursivo) — ISO3:")
    print(iso3)

def menu():
    print("\n=== LAB 1 — Árbol AVL con métrica = media (1961–2022) ===")
    print("1) Recorrido por niveles")
    print("2) Insertar país por ISO3")
    print("3) Eliminar país por ISO3 (usa su media como clave)")
    print("4) Buscar por MÉTRICA (media exacta)")
    print("5) Países con temperatura > promedio anual: ")
    print("6) Países con temperatura < promedio histórico:")
    print("7) Países con temperatura media ≥ valor: ")
    print("8) Ver información de un nodo (nivel, balance, padre/abuelo/tío)")
    print("9) Dibujar árbol (Graphviz)")
    print("10) Eliminar por métrica (media)")
    print("0) Salir")
    return input("Elige opción: ").strip()


if __name__ == "__main__":
    tree, df, global_mean, per_year_mean = build_tree(CSV_PATH)
    print(f"Cargado. Países: {len(df)}")

    while True:
        op = menu()
        if op == "0":
            break

        elif op == "1":
            for i, lvl in enumerate(tree.level_order_recursive_grouped_iso3()):
                print(f"Nivel {i}: {', '.join(lvl)}")


        elif op == "2":
            iso = input("ISO3 a insertar (debe existir en el CSV): ").upper().strip()
            row = df[df["ISO3"].str.upper() == iso]
            if row.empty:
                print("No encontré ese ISO3 en el CSV.")
            else:

                if tree.find_by_iso3(iso):
                    print("Ese ISO3 ya está en el árbol. (Si quieres reinsertarlo, elimínalo primero).")
                else:
                    r = row.iloc[0]
                    payload = to_payload(r)
                    tree.insert(payload["mean_change"], payload)
                    print(f"Insertado {iso}.")
                    draw(tree) 


        elif op == "3":
            iso = input("ISO3 a eliminar: ").upper().strip()
            removed = delete_all_by_iso3(tree, iso)
            if removed == 0:
                print("No está en el árbol.")
            else:
                print(f"Eliminado {iso} ({removed} nodo(s)).")
                draw(tree)


        elif op == "4":
            try:
                raw = input("Ingresa la MÉTRICA (media): ").strip()
                raw = raw.replace(",", ".")  
                val = float(raw)
            except ValueError:
                print("Valor inválido.")
                continue


            node = tree.find_by_key_approx(val, tol=1e-6)

            if not node:
                node = tree.find_by_key_rounded(val, ndigits=6)

            if node:
                print("Encontrado:", node.data["ISO3"], "| mean =", f"{node.key:.6f}")
                ver = input("¿Ver info (nivel/balance/padre/abuelo/tío)? [S/N]: ").strip().upper()
                if ver == "S":
                    show_node_info(tree, node.data["ISO3"])
            else:
                near = tree.find_nearest(val)
                if near:
                    print("No exacto. Más cercano:",
                        near.data["ISO3"], "| mean =", f"{near.key:.6f}")
                else:
                    print("No se encontró ningún nodo.")


        elif op == "5":
            try:
                año = int(input("Ingrese el año a evaluar (1961-2022): ").strip())
                tree.mostrar_punto4a(año)
            except ValueError:
                print("Año inválido. Debe ser un número entre 1961-2022.")
            except Exception as e:
                print(f"Error: {e}")            

        elif op == "6":
            try:
                año = int(input("Ingrese el año a evaluar (1961-2022): ").strip())
                tree.mostrar_punto4b(año)
            except ValueError:
                print("Año inválido. Debe ser un número entre 1961-2022.")
            except Exception as e:
                print(f"Error: {e}")


        elif op == "7":
            try:
                umbral = float(input("Ingrese el valor umbral de temperatura media: ").strip())
                tree.mostrar_punto4c(umbral)
            except ValueError:
                print("Valor inválido. Debe ser un número (ej: 15.5, 20.0, etc.)")
            except Exception as e:
                print(f"Error: {e}")


        elif op == "8":
            iso = input("ISO3 del nodo a inspeccionar: ").upper().strip()
            show_node_info(tree, iso)

        elif op == "9":
            draw(tree)
        elif op == "10":
            try:
                val = float(input("Media exacta a eliminar: ").strip())
            except ValueError:
                print("Valor inválido."); continue
            n = tree.find_by_key_approx(val, tol=1e-9)
            if not n:
                print("No se encontró nodo con esa media.")
            else:
                iso = n.data["ISO3"]
                tree.delete(n.key)    
                print(f"Eliminado {iso}.")
                draw(tree)

        else:
            print("Opción inválida.")
