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
        tree.insert(round(payload["mean_change"], 6), payload)
    return tree, df, global_mean, per_year_mean

def show_metrics(df):

    print("\n=== Métricas disponibles ===")
    for _, row in df.iterrows():
        print(f"{row['ISO3']} - {row['Country']} - Media: {row['mean_change']:.6f}")

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

def searchh_mean(tree: AVLTree, value: float):

    nodes = tree.get_nodes()

    value_str = str(value)
    

    matching_nodes = [
        (node, node.key) for node in nodes if str(node.key).startswith(value_str)
    ]
    

    if not matching_nodes:
        print(f"No se encontraron nodos con métricas que comiencen con {value_str}.")
        return


    matching_nodes.sort(key=lambda x: x[1])

    print(f"\nPaíses con métricas que comienzan con '{value_str}':")

    for node, diff in matching_nodes:
        iso3 = node.data.get("ISO3")
        country = node.data.get("Country")
        print(f"ISO3: {iso3} | País: {country} | Media: {node.key:.6f}")
    
    print(f"\nTotal de países encontrados: {len(matching_nodes)}")

def menu():
    print("\n=== LAB 1 — Árbol AVL con métrica = media (1961–2022) ===")
    print("1) Recorrido por niveles")
    print("2) Insertar país por ISO3")
    print("3) Eliminar país por ISO3")
    print("4) Buscar por MÉTRICA (media exacta)")
    print("5) Países con temperatura > promedio anual: ")
    print("6) Países con temperatura < promedio histórico:")
    print("7) Países con temperatura media ≥ valor: ")
    print("8) Ver información de un nodo (nivel, balance, padre/abuelo/tío)")
    print("9) Dibujar árbol (Graphviz)")
    print("10) Eliminar por métrica (media)")
    print("11) Consultar todas las métricas disponibles")
    print("12) Insertar país manualmente (datos completos)")
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
                    tree.insert(round(payload["mean_change"], 6), payload)  
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

            node = tree.find_by_key_approx(round(val, 6), tol=1e-6)

            if not node:
                node = tree.find_by_key_rounded(val, ndigits=6)

            if node:
                print(f"Encontrado: {node.data['ISO3']} | País: {node.data.get('Country')} | media = {node.key:.6f}")
                ver = input("¿Ver info detallada (nivel/balance/padre/abuelo/tío)? [S/N]: ").strip().upper()
                if ver == "S":
                    show_node_info(tree, node.data["ISO3"])

            else:
 
                near = tree.find_nearest(val)
                if near:
                    print(f"No exacto. Más cercano: {near.data['ISO3']} | País: {near.data.get('Country')} | media = {near.key:.6f}")
                    a = input("¿Es este el país/dato que busca? [S/N]: ").strip().upper()
                    if a == "S":
                        show_node_info(tree, near.data["ISO3"])
                    else:

                        searchh_mean(tree, val)
                        b = input("¿Es alguno de estos el país/dato que busca? [S/N]: ").strip().upper()
                        if b == "S":
                            c = input("¿Desea ver info detallada (nivel/balance/padre/abuelo/tío)? [S/N]: ").strip().upper()
                            if c == "S":
                                d = input("Ingrese el ISO de interés: ").strip().upper()
                                node = tree.find_by_iso3(d)
                                if node:
                                    show_node_info(tree, node.data["ISO3"])
                                else:
                                    print("El ISO ingresado es incorrecto.")
                            else:
                                print("De vuelta al menú principal.") 
                        else:
                            print("Intente de nuevo con un valor diferente.") 

                else:
                    print("No se encontró ningún nodo.")

        elif op == "5":
            try:
                año = int(input("Ingrese el año a evaluar (1961-2022): ").strip())
                resultados = tree.punto_4a(año) 
                tree.mostrar_punto4a(año)
                ver_info= "no"
                if resultados:
                    print("\n" + "="*50)
                    ver_info = input("¿Desea ver la información de algún país de la lista? (si/no): ").strip().lower()
                if ver_info == 'si':
                    while True:
                        iso_buscar = input("Ingrese el ISO3 del país (o 'salir' para terminar): ").strip().upper()
                        if iso_buscar == 'SALIR':
                            break
                        
                        iso_en_resultados = any(iso == iso_buscar for iso, _, _ in resultados)
                        
                        if iso_en_resultados:
                            print("\n" + "="*40)
                            print(f"INFORMACIÓN DEL NODO: {iso_buscar}")
                            print("="*40)
                            show_node_info(tree, iso_buscar)
                            print("="*40)
                            
                            otro = input("¿Ver otro país? (si/no): ").strip().lower()
                            if otro != 'si':
                                break
                        else:
                            print(f"El código {iso_buscar} no está en la lista de resultados.")
                            print("   Solo puede buscar países que cumplen el criterio del punto 4a.")
                            continuar = input("¿Intentar con otro código? (si/no): ").strip().lower()
                            if continuar != 'si':
                                break

            except ValueError:
                print("Año inválido. Debe ser un número entre 1961-2022.")
            except Exception as e:
                print(f"Error: {e}")           

        elif op == "6":
            try:
                año = int(input("Ingrese el año a evaluar (1961-2022): ").strip())
                resultados = tree.punto_4b(año)
                tree.mostrar_punto4b(año)

                ver_info = "no"
                if resultados:
                    print("\n" + "="*50)
                    ver_info = input("¿Desea ver la información de algún país de la lista? (si/no): ").strip().lower()
                if ver_info == 'si':
                    while True:
                        iso_buscar = input("Ingrese el ISO3 del país (o 'salir' para terminar): ").strip().upper()
                        if iso_buscar == 'SALIR':
                            break
                        
                        iso_en_resultados = any(iso == iso_buscar for iso, _, _ in resultados)
                        
                        if iso_en_resultados:
                            print("\n" + "="*40)
                            print(f"INFORMACIÓN DEL NODO: {iso_buscar}")
                            print("="*40)
                            show_node_info(tree, iso_buscar)
                            print("="*40)
                            
                            otro = input("¿Ver otro país? (si/no): ").strip().lower()
                            if otro != 'si':
                                break
                        else:
                            print(f"El código {iso_buscar} no está en la lista de resultados.")
                            print("   Solo puede buscar países que cumplen el criterio del punto 4b.")
                            continuar = input("¿Intentar con otro código? (si/no): ").strip().lower()
                            if continuar != 'si':
                                break

            except ValueError:
                print("Año inválido. Debe ser un número entre 1961-2022.")
            except Exception as e:
                print(f"Error: {e}")

        elif op == "7":
            try:
                umbral = float(input("Ingrese el valor umbral de temperatura media: ").strip())
                resultados = tree.punto_4c(umbral)
                tree.mostrar_punto4c(umbral)

                ver_info = "no"
                if resultados:
                    print("\n" + "="*50)
                    ver_info = input("¿Desea ver la información de algún país de la lista? (si/no): ").strip().lower()
                if ver_info == 'si':
                    while True:
                        iso_buscar = input("Ingrese el ISO3 del país (o 'salir' para terminar): ").strip().upper()
                        if iso_buscar == 'SALIR':
                            break
                        
                        iso_en_resultados = any(iso == iso_buscar for iso, _ in resultados)
                        
                        if iso_en_resultados:
                            print("\n" + "="*40)
                            print(f"INFORMACIÓN DEL NODO: {iso_buscar}")
                            print("="*40)
                            show_node_info(tree, iso_buscar)
                            print("="*40)
                            
                            otro = input("¿Ver otro país? (si/no): ").strip().lower()
                            if otro != 'si':
                                break
                        else:
                            print(f"El código {iso_buscar} no está en la lista de resultados.")
                            print("   Solo puede buscar países que cumplen el criterio del punto 4c.")
                            continuar = input("¿Intentar con otro código? (si/no): ").strip().lower()
                            if continuar != 'si':
                                break


            except ValueError:
                print("Valor inválido. Debe ser un número (ej: 15.5, 20.0, etc.)")
            except Exception as e:
                print(f"Error: {e}")

        elif op == "8":
            iso = input("ISO3 del nodo a inspeccionar: ").upper().strip()
            show_node_info(tree, iso)

        elif op == "9":
            draw(tree)

        elif op == "10":
            try:
                val = float(input("Métrica (media) a eliminar: ").strip().replace(",", "."))
            except ValueError:
                print("Valor inválido.")
                continue
            removed = tree.delete_all_by_key(round(val, 6), tol=1e-6)
            if removed == 0:
                print("Ingresar el valor exacto de la media a eliminar.")
            else:
                print(f"Eliminados {removed} nodo(s) con métrica ≈ {val:.6f}.")
                draw(tree)
        elif op == "11":
            show_metrics(df)
        elif op == "12":
            tree.insertar_manual()
            draw(tree)
        else:
            print("Opción inválida.")
    
