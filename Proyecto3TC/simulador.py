"""Simulador de terminal para MT definidas en YAML."""

import argparse
from pathlib import Path

from lector_yaml import ErrorDefinicion, cargar_maquina, cargar_proyecto
from motor import EstadoEjecucion, MaquinaTuring
from visualizacion import mostrar_configuracion, mostrar_paso, mostrar_resumen


RAIZ = Path(__file__).resolve().parent
MAQUINAS = {
    "reconocedora": RAIZ / "maquinas/reconocedora.yaml",
    "alteradora": RAIZ / "maquinas/alteradora.yaml",
}


def cargar_reconocedora() -> MaquinaTuring:
    """Conserva el punto de integración usado por el motor y sus pruebas."""
    return cargar_maquina(MAQUINAS["reconocedora"])


def mostrar_resultado(maquina: MaquinaTuring, entrada: str, max_pasos: int,
                      solo_resumen: bool = False) -> None:
    simulacion = maquina.iniciar(entrada)
    print(f"\nEntrada: {entrada!r}")
    if not solo_resumen:
        print("Paso 0: configuración inicial")
        mostrar_configuracion(simulacion.inicial)
        for _ in range(max_pasos):
            if simulacion.estado != EstadoEjecucion.EN_CURSO:
                break
            paso = simulacion.paso()
            if paso is None:
                break
            mostrar_paso(paso)
    # El límite incluye las transiciones ya mostradas; el motor distingue
    # límite, rechazo sin regla y aceptación exactamente en el último paso.
    mostrar_resumen(simulacion.ejecutar(max_pasos=max_pasos))


def mostrar_lote(maquina: MaquinaTuring, entradas: tuple[str, ...], max_pasos: int,
                 solo_resumen: bool = False) -> None:
    print(f"Entradas configuradas en YAML: {len(entradas)}")
    for numero, entrada in enumerate(entradas, 1):
        print(f"\n=== Cadena {numero}/{len(entradas)} ===")
        mostrar_resultado(maquina, entrada, max_pasos, solo_resumen)
    if not entradas:
        print("No hay cadenas configuradas en inputs.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulador de MT de una cinta desde YAML.")
    parser.add_argument("entrada", nargs="?", help="Cadena; usa comillas para conservarla.")
    seleccion = parser.add_mutually_exclusive_group()
    seleccion.add_argument("--maquina", choices=MAQUINAS, default="reconocedora")
    seleccion.add_argument("--yaml", type=Path, help="Ruta a otra definición YAML.")
    parser.add_argument("--interactivo", action="store_true", help="Abrir el menú en lugar del lote YAML.")
    parser.add_argument("--validar", action="store_true", help="Validar el YAML y salir.")
    parser.add_argument("--solo-resumen", action="store_true", help="Omitir los pasos intermedios.")
    parser.add_argument("--max-pasos", type=int, default=10_000)
    args = parser.parse_args()
    if args.max_pasos < 0:
        parser.error("--max-pasos debe ser no negativo")
    if args.interactivo and args.entrada is not None:
        parser.error("--interactivo no se combina con una entrada directa")
    ruta = args.yaml if args.yaml is not None else MAQUINAS[args.maquina]
    try:
        proyecto = cargar_proyecto(ruta)
        maquina = proyecto.maquina
    except ErrorDefinicion as error:
        parser.exit(2, f"Error de definición: {error}\n")
    if args.validar:
        print(f"YAML válido: {ruta}")
        print(f"Estados: {len(maquina.estados)} | Transiciones: {len(maquina.transiciones)}")
        if proyecto.entradas is not None:
            print(f"Entradas: {len(proyecto.entradas)}")
        return
    try:
        if args.entrada is not None:
            mostrar_resultado(maquina, args.entrada, args.max_pasos, args.solo_resumen)
            return
        if proyecto.entradas is not None and not args.interactivo:
            mostrar_lote(maquina, proyecto.entradas, args.max_pasos, args.solo_resumen)
            return
        print(f"MT cargada: {ruta.name}")
        print("Cada paso muestra la regla aplicada y la cinta; ^ señala el cabezal.")
        while True:
            print("\n1. Evaluar cadena")
            print("0. Salir")
            opcion = input("Opción: ").strip().lower()
            if opcion in {"0", "salir"}:
                print("Simulador cerrado.")
                break
            if opcion != "1":
                print("Opción inválida. Elige 1 o 0.")
                continue
            entrada = input("Cadena (o 'salir' para terminar): ")
            if entrada.strip().lower() == "salir":
                print("Simulador cerrado.")
                break
            mostrar_resultado(maquina, entrada, args.max_pasos, args.solo_resumen)
    except (EOFError, KeyboardInterrupt):
        print("\nSimulador cerrado.")


if __name__ == "__main__":
    main()
