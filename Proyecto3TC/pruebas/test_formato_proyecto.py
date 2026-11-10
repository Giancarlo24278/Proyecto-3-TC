"""Pruebas del contrato YAML del PDF y de la demostración de las ocho cadenas."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

from lector_yaml import (
    ErrorDefinicion, cargar_maquina, cargar_proyecto, validar_definicion, validar_proyecto,
)
from simulador import MAQUINAS


RAIZ = Path(__file__).resolve().parents[1]
REPOSITORIO = RAIZ.parent

# Transcripción del ejemplo del documento: incluye la regla B equivalente repetida.
EJEMPLO_PDF = '''mt:
  states: [q0, q1, q2, qf]
  input_alphabet: [a, b]
  tape_alphabet: [a, b, B, X, Y]
  initial_state: q0
  accept_states: [qf]
  transitions:
    - state: q0
      read: [a, B]
      write: [a, B]
      move: R
      next: q1
    - state: q0
      read: [b, B]
      write: [b, B]
      move: R
      next: q1
  inputs:
    - "aabb"
    - "ab"
    - "aaabbb"
'''


class PruebasFormatoProyecto(unittest.TestCase):
    def setUp(self):
        self.datos = yaml.safe_load(EJEMPLO_PDF)

    def test_ejemplo_exacto_del_pdf_una_cinta_y_blanco_B(self):
        proyecto = validar_proyecto(self.datos)
        self.assertEqual(proyecto.entradas, ('aabb', 'ab', 'aaabbb'))
        self.assertEqual(proyecto.maquina.blanco, 'B')
        self.assertEqual(len(proyecto.maquina.transiciones), 3)
        resultado = proyecto.maquina.ejecutar('aabb')
        self.assertFalse(resultado.aceptada)  # El ejemplo no da salidas desde q1.
        self.assertEqual(resultado.final.cabezal, 1)
        self.assertEqual(resultado.final.contenido(), 'aabb')
        self.assertEqual(len(resultado.pasos), 1)

    def test_reglas_en_listas_leen_y_escriben_una_celda(self):
        self.datos['mt']['transitions'] = [
            {'state': 'q0', 'read': ['a', 'B'], 'write': ['X', 'Y'], 'move': 'S', 'next': 'qf'}
        ]
        maquina = validar_definicion(self.datos)
        for entrada, esperado in (('a', 'X'), ('', 'Y')):
            with self.subTest(entrada=entrada):
                r = maquina.ejecutar(entrada)
                self.assertTrue(r.aceptada)
                self.assertEqual(r.final.contenido(), esperado)
                self.assertEqual(r.final.cabezal, 0)
                self.assertEqual(len(r.pasos), 1)

    def test_simbolos_individuales_y_blanco_personalizado(self):
        self.datos['mt'].update({
            'tape_alphabet': ['a', 'b', '_'], 'blank_symbol': '_',
            'transitions': [{'state': 'q0', 'read': 'a', 'write': 'b', 'move': 'R', 'next': 'qf'}],
        })
        proyecto = validar_proyecto(self.datos)
        self.assertTrue(proyecto.maquina.ejecutar('a').aceptada)
        self.assertEqual(proyecto.maquina.blanco, '_')

    def test_reglas_conflictivas_se_rechazan(self):
        self.datos['mt']['transitions'][1]['write'][1] = 'X'
        with self.assertRaisesRegex(ErrorDefinicion, 'duplicada incompatible'):
            validar_proyecto(self.datos)

    def test_listas_mal_formadas_y_simbolos_invalidos(self):
        for leer, escribir in (([], []), (['a'], ['a', 'B']), (['a'], 'a'),
                               ('a', ['a']), ([1], ['a']), (['a'], [False]),
                               (['a'], ['XX']), (None, 'a')):
            datos = deepcopy(self.datos)
            datos['mt']['transitions'][0].update({'read': leer, 'write': escribir})
            with self.subTest(leer=leer, escribir=escribir), self.assertRaises(ErrorDefinicion):
                validar_proyecto(datos)

    def test_inputs_deben_ser_cadenas_y_permiten_vacio(self):
        for valor in ('aabb', None, [10101], [False], [None], [[]]):
            datos = deepcopy(self.datos)
            datos['mt']['inputs'] = valor
            with self.subTest(valor=valor), self.assertRaisesRegex(ErrorDefinicion, 'inputs'):
                validar_proyecto(datos)
        self.datos['mt']['inputs'] = ['', 'x']
        p = validar_proyecto(self.datos)
        self.assertEqual(p.entradas, ('', 'x'))
        self.assertFalse(p.maquina.ejecutar('x').aceptada)
        self.datos['mt']['inputs'] = []
        self.assertEqual(validar_proyecto(self.datos).entradas, ())

    def test_campos_del_formato_y_semantica(self):
        for campo in self.datos['mt']:
            datos = deepcopy(self.datos)
            del datos['mt'][campo]
            with self.subTest(faltante=campo), self.assertRaises(ErrorDefinicion):
                validar_proyecto(datos)
        for cambio in ({'states': None}, {'transitions': {}}, {'initial_state': 'ausente'},
                       {'extra': 0}, {'blank_symbol': 'Z'}, {'reject_states': ['qf']}):
            datos = deepcopy(self.datos)
            datos['mt'].update(cambio)
            with self.subTest(cambio=cambio), self.assertRaises(ErrorDefinicion):
                validar_proyecto(datos)
        for mt in (None, [], 'maquina'):
            with self.subTest(mt=mt), self.assertRaises(ErrorDefinicion):
                validar_proyecto({'mt': mt})
        with self.assertRaises(ErrorDefinicion):
            validar_proyecto({**self.datos, 'inputs': []})

    def test_errores_de_reglas_y_claves_duplicadas(self):
        for cambio in ({'state': 'qf'}, {'next': 'ausente'}, {'read': ['Z', 'B']},
                       {'move': 'D'}, {'extra': 'X'}):
            datos = deepcopy(self.datos)
            datos['mt']['transitions'][0].update(cambio)
            with self.subTest(cambio=cambio), self.assertRaises(ErrorDefinicion):
                validar_proyecto(datos)
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'duplicado.yaml'
            ruta.write_text(EJEMPLO_PDF.replace('  states:', '  states: [q0]\n  states:', 1))
            with self.assertRaisesRegex(ErrorDefinicion, 'duplicada'):
                cargar_proyecto(ruta)

    def test_compatibilidad_con_yaml_original(self):
        ruta = RAIZ / 'maquinas/alteradora_incremento.yaml'
        self.assertIsNone(cargar_proyecto(ruta).entradas)
        self.assertEqual(cargar_maquina(ruta).ejecutar('11111').final.contenido(), '100000')

    def test_ejemplos_estan_dentro_de_ambos_yaml(self):
        for nombre, ruta in MAQUINAS.items():
            casos = json.loads((RAIZ / f'ejemplos/{nombre}.json').read_text())
            proyecto = cargar_proyecto(ruta)
            self.assertEqual(proyecto.entradas, tuple(c['entrada'] for c in casos))
            self.assertEqual(len(proyecto.entradas), 4)
            for caso in casos:
                with self.subTest(maquina=nombre, entrada=caso['entrada']):
                    self.assertGreaterEqual(len(caso['entrada']), 5)
                    r = proyecto.maquina.ejecutar(caso['entrada'])
                    self.assertEqual(r.aceptada, caso['aceptada'])
                    if 'salida' in caso:
                        self.assertEqual(r.final.contenido(), caso['salida'])


class PruebasLotesYDemostracion(unittest.TestCase):
    def ejecutar(self, script, *args, entrada=None):
        return subprocess.run([sys.executable, str(script), *args], cwd=REPOSITORIO.parent,
                              input=entrada, text=True, capture_output=True, timeout=10)

    def test_cada_lote_tiene_cuatro_ids_iniciales_y_resultados(self):
        for nombre, aceptadas in (('reconocedora', 2), ('alteradora', 4)):
            r = self.ejecutar(RAIZ / 'simulador.py', '--yaml', str(MAQUINAS[nombre]))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.count('Paso 0:'), 4)
            self.assertEqual(r.stdout.count('Cinta final:'), 4)
            self.assertEqual(r.stdout.count('Resultado: ACEPTADA'), aceptadas)
            self.assertEqual(r.stdout.count('Resultado: RECHAZADA'), 4 - aceptadas)
            self.assertIn('Cadena 4/4', r.stdout)
            for cadena in cargar_proyecto(MAQUINAS[nombre]).entradas:
                self.assertIn(f'Entrada: {cadena!r}', r.stdout)

    def test_entrada_directa_sustituye_lote_y_limite_es_por_cadena(self):
        r = self.ejecutar(RAIZ / 'simulador.py', '--maquina', 'alteradora', '10100')
        self.assertEqual(r.stdout.count('Cinta final:'), 1)
        self.assertIn('Cinta final: 10101', r.stdout)
        r = self.ejecutar(RAIZ / 'simulador.py', '--maquina', 'alteradora', '--max-pasos', '1')
        self.assertEqual(r.stdout.count('Resultado: LIMITE_ALCANZADO'), 4)
        self.assertEqual(r.stdout.count('Transiciones ejecutadas: 1'), 4)

    def test_lote_vacio_no_abre_menu_y_validacion_informa_entradas(self):
        datos = yaml.safe_load(MAQUINAS['alteradora'].read_text())
        datos['mt']['inputs'] = []
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'vacio.yaml'
            ruta.write_text(yaml.safe_dump(datos))
            r = self.ejecutar(RAIZ / 'simulador.py', '--yaml', str(ruta))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('No hay cadenas', r.stdout)
            self.assertNotIn('Opción:', r.stdout)
        r = self.ejecutar(RAIZ / 'simulador.py', '--maquina', 'alteradora', '--validar')
        self.assertIn('Entradas: 4', r.stdout)

    def test_error_de_inputs_en_cli_y_conflicto_interactivo(self):
        datos = yaml.safe_load(MAQUINAS['alteradora'].read_text())
        datos['mt']['inputs'] = [10101]
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'invalido.yaml'
            ruta.write_text(yaml.safe_dump(datos))
            r = self.ejecutar(RAIZ / 'simulador.py', '--yaml', str(ruta))
            self.assertEqual(r.returncode, 2)
            self.assertIn('inputs', r.stderr)
            self.assertNotIn('Traceback', r.stderr)
        r = self.ejecutar(RAIZ / 'simulador.py', '10100', '--interactivo')
        self.assertEqual(r.returncode, 2)

    def test_lanzador_ejecuta_las_ocho_cadenas_desde_otra_carpeta(self):
        r = self.ejecutar(REPOSITORIO / 'ejecutar.py', '--solo-resumen')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count('Cinta final:'), 8)
        self.assertEqual(r.stdout.count('Resultado: ACEPTADA'), 6)
        self.assertEqual(r.stdout.count('Resultado: RECHAZADA'), 2)
        self.assertIn('Cinta final: 100000', r.stdout)
        r = self.ejecutar(REPOSITORIO / 'ejecutar.py', 'alteradora', '--solo-resumen')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count('Cinta final:'), 4)
        self.assertNotIn('MT RECONOCEDORA', r.stdout)
        r = self.ejecutar(REPOSITORIO / 'ejecutar.py', '--max-pasos', '-1')
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()
