"""Vista de terminal: índices, celdas, cabezal, estado y regla aplicada."""

from motor import Configuracion, Paso, Resultado


def mostrar_configuracion(configuracion: Configuracion) -> None:
    posiciones = [0, configuracion.cabezal]
    posiciones.extend(indice for indice, _ in configuracion.celdas)
    inicio, fin = min(posiciones) - 1, max(posiciones) + 1
    indices = list(range(inicio, fin + 1))
    ancho = max(3, len(str(inicio)), len(str(fin)))
    print(f"  Estado: {configuracion.estado} | Cabezal: {configuracion.cabezal}")
    print("  Índice: " + " ".join(f"{i:^{ancho}}" for i in indices).rstrip())
    print("  Cinta:  " + " ".join(
        f"{s:^{ancho}}" for s in configuracion.ventana(inicio, fin)
    ).rstrip())
    print("  Cabezal:" + " ".join(
        f"{'^' if i == configuracion.cabezal else '':^{ancho}}" for i in indices
    ).rstrip())


def mostrar_paso(paso: Paso) -> None:
    t = paso.transicion
    print(f"\nPaso {paso.numero}: δ({paso.antes.estado}, {paso.simbolo_leido!r})"
          f" = ({t.siguiente}, {t.escribir!r}, {t.mover})")
    mostrar_configuracion(paso.despues)


def mostrar_resumen(resultado: Resultado) -> None:
    print(f"\nResultado: {resultado.estado.value.upper()}")
    print(f"Motivo: {resultado.motivo}")
    print(f"Transiciones ejecutadas: {len(resultado.pasos)}")
    print(f"Estado final: {resultado.final.estado}")
    print(f"Cinta final: {resultado.final.contenido() or '(vacía)'}")
    print(f"Posición final del cabezal: {resultado.final.cabezal}")
    if resultado.estado.value == "limite_alcanzado":
        print("Ejecución incompleta: la cinta mostrada es parcial.")
    mostrar_configuracion(resultado.final)
    print()
