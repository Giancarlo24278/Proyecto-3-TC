"""Simulador de terminal de la MT reconocedora de paquetes."""

import argparse
from pathlib import Path

import yaml

from motor import MaquinaTuring, Transicion


def cargar_reconocedora() -> MaquinaTuring:
    """Carga la definición de la reconocedora incluida en el proyecto."""
    ruta = Path(__file__).resolve().parent / "maquinas/reconocedora_paquetes.yaml"
    with ruta.open(encoding="utf-8") as archivo:
        datos = yaml.safe_load(archivo)
    reglas = {}
    for regla in datos["transiciones"]:
        clave = (regla["origen"], regla["leer"])
        if clave in reglas:
            raise ValueError(f"Transición duplicada: {clave}")
        reglas[clave] = Transicion(regla["siguiente"], regla["escribir"], regla["mover"])
    return MaquinaTuring(
        estados=datos["estados"],
        alfabeto_entrada=datos["alfabeto_entrada"],
        alfabeto_cinta=datos["alfabeto_cinta"],
        blanco=datos["blanco"],
        estado_inicial=datos["estado_inicial"],
        estados_aceptacion=datos["estados_aceptacion"],
        estados_rechazo=datos["estados_rechazo"],
        transiciones=reglas,
    )


def mostrar_resultado(maquina: MaquinaTuring, entrada: str, max_pasos: int) -> None:
    resultado = maquina.ejecutar(entrada, max_pasos=max_pasos)
    print(f"\nEntrada: {entrada!r}")
    print(f"Resultado: {resultado.estado.value.upper()}")
    print(f"Motivo: {resultado.motivo}")
    print(f"Transiciones ejecutadas: {len(resultado.pasos)}")
    print(f"Estado final: {resultado.final.estado}")
    print(f"Cinta final: {resultado.final.contenido() or '(vacía)'}")
    print(f"Posición final del cabezal: {resultado.final.cabezal}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulador de la MT reconocedora de paquetes.")
    parser.add_argument("entrada", nargs="?", help="Paquete, por ejemplo '111#010'.")
    parser.add_argument("--max-pasos", type=int, default=10_000)
    args = parser.parse_args()
    if args.max_pasos < 0:
        parser.error("--max-pasos debe ser no negativo")
    maquina = cargar_reconocedora()
    if args.entrada is not None:
        mostrar_resultado(maquina, args.entrada, args.max_pasos)
        return
    print("MT reconocedora de paquetes: cantidad#datos")
    print("Ejemplo: 111#010.")
    print("Las marcas X e Y de la cinta representan unos y bits ya emparejados.")
    while True:
        try:
            print("\n1. Evaluar paquete")
            print("0. Salir")
            opcion = input("Opción: ").strip().lower()
            if opcion in {"0", "salir"}:
                print("Simulador cerrado.")
                break
            if opcion != "1":
                print("Opción inválida. Elige 1 o 0.")
                continue
            entrada = input("Paquete (o 'salir' para terminar): ")
            if entrada.strip().lower() == "salir":
                print("Simulador cerrado.")
                break
            mostrar_resultado(maquina, entrada, args.max_pasos)
        except (EOFError, KeyboardInterrupt):
            print("\nSimulador cerrado.")
            break


if __name__ == "__main__":
    main()
