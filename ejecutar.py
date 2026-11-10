"""Demostración de las ocho cadenas del proyecto desde la raíz del repositorio."""

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description='Ejecutar los lotes YAML de las máquinas de Turing.')
    parser.add_argument('maquina', nargs='?', choices=('ambas', 'reconocedora', 'alteradora'), default='ambas')
    parser.add_argument('--solo-resumen', action='store_true')
    parser.add_argument('--max-pasos', type=int, default=10_000)
    args = parser.parse_args()
    if args.max_pasos < 0:
        parser.error('--max-pasos debe ser no negativo')
    raiz = Path(__file__).resolve().parent
    if importlib.util.find_spec('yaml') is None:
        print('Falta PyYAML. Instala las dependencias con el mismo Python:', file=sys.stderr)
        print(f'"{sys.executable}" -m pip install -r "{raiz / "Proyecto3TC/requirements-dev.txt"}"', file=sys.stderr)
        return 2
    maquinas = ('reconocedora', 'alteradora') if args.maquina == 'ambas' else (args.maquina,)
    for maquina in maquinas:
        print(f'\n========== MT {maquina.upper()} ==========', flush=True)
        comando = [sys.executable, str(raiz / 'Proyecto3TC/simulador.py'),
                   '--maquina', maquina, '--max-pasos', str(args.max_pasos)]
        if args.solo_resumen:
            comando.append('--solo-resumen')
        resultado = subprocess.run(comando)
        if resultado.returncode:
            return resultado.returncode
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\nDemostración interrumpida.')
        raise SystemExit(130)
