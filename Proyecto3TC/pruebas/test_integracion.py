"""Pruebas del lector, la alteradora y la interfaz de terminal."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

from lector_yaml import ErrorDefinicion, cargar_maquina, validar_definicion
from motor import Configuracion, EstadoEjecucion
from simulador import MAQUINAS, mostrar_resultado
from visualizacion import mostrar_configuracion


RAIZ = Path(__file__).resolve().parents[1]


class PruebasLector(unittest.TestCase):
    def setUp(self):
        self.datos = yaml.safe_load((RAIZ / 'maquinas/alteradora_incremento.yaml').read_text(encoding='utf-8'))

    def cargar_texto(self, texto):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'maquina.yaml'
            ruta.write_text(texto, encoding='utf-8')
            return cargar_maquina(ruta)

    def test_ambas_definiciones_y_nombre_opcional(self):
        for ruta in MAQUINAS.values():
            self.assertTrue(cargar_maquina(ruta).estados)
        del self.datos['nombre']
        self.assertTrue(validar_definicion(self.datos).ejecutar('0').aceptada)

    def test_raiz_vacia_lista_escalar_y_campos(self):
        for texto in ('', '[]', 'hola', 'null', 'nombre: incompleta'):
            with self.subTest(texto=texto), self.assertRaises(ErrorDefinicion):
                self.cargar_texto(texto)
        for cambio in ({'nombre': 17}, {'extra': 'error'}, {'estados': None},
                       {'transiciones': {}}, {'blanco': True}, {'estado_inicial': ''}):
            datos = deepcopy(self.datos)
            datos.update(cambio)
            with self.subTest(cambio=cambio), self.assertRaises(ErrorDefinicion):
                validar_definicion(datos)
        for campo in self.datos:
            if campo == 'nombre':
                continue
            datos = deepcopy(self.datos)
            del datos[campo]
            with self.subTest(faltante=campo), self.assertRaises(ErrorDefinicion):
                validar_definicion(datos)

    def test_listas_simbolos_y_duplicados(self):
        for campo, valor in (
            ('estados', []), ('estados', ['q_inicio', 'q_inicio']),
            ('estados', ['']), ('alfabeto_entrada', [0, 1]),
            ('alfabeto_entrada', [False]), ('alfabeto_cinta', ['00', '_']),
            ('alfabeto_cinta', ['0', '1']), ('alfabeto_entrada', ['_']),
            ('estados_aceptacion', ['q_ausente']),
            ('estados_rechazo', ['q_aceptar']), ('estado_inicial', 'q_ausente'),
        ):
            datos = deepcopy(self.datos)
            datos[campo] = valor
            with self.subTest(campo=campo, valor=valor), self.assertRaises(ErrorDefinicion):
                validar_definicion(datos)

    def test_reglas_invalidas(self):
        for cambio in ({'origen': 'q_ausente'}, {'siguiente': 'q_ausente'},
                       {'origen': 'q_aceptar'}, {'leer': 'X'}, {'escribir': 'X'},
                       {'mover': 'D'}, {'leer': 0}, {'mover': None}, {'extra': 'X'}):
            datos = deepcopy(self.datos)
            datos['transiciones'][0].update(cambio)
            with self.subTest(cambio=cambio), self.assertRaisesRegex(ErrorDefinicion, 'transiciones'):
                validar_definicion(datos)
        for regla in (None, [], 'regla', {'origen': 'q_inicio'}):
            datos = deepcopy(self.datos)
            datos['transiciones'] = [regla]
            with self.subTest(regla=regla), self.assertRaises(ErrorDefinicion):
                validar_definicion(datos)
        self.datos['transiciones'].append(deepcopy(self.datos['transiciones'][0]))
        with self.assertRaisesRegex(ErrorDefinicion, 'transición duplicada'):
            validar_definicion(self.datos)

    def test_yaml_invalido_duplicados_y_etiquetas(self):
        texto = yaml.safe_dump(self.datos)
        for invalido in ('estados: [', texto + '\nblanco: X\n',
                         texto.replace('origen: q_inicio', 'origen: q_inicio\n  origen: q_inicio', 1),
                         '!!python/object/apply:os.system ["echo no_ejecutar"]',
                         '? [clave, compuesta]\n: valor', 'true: valor',
                         texto + '\n---\n' + texto):
            with self.subTest(texto=invalido[:80]), self.assertRaises(ErrorDefinicion):
                self.cargar_texto(invalido)
        with self.assertRaisesRegex(ErrorDefinicion, 'línea 1, columna'):
            self.cargar_texto('estados: [')

    def test_archivo_inexistente_y_codificacion(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'maquina.yaml'
            with self.assertRaisesRegex(ErrorDefinicion, 'No se pudo leer'):
                cargar_maquina(ruta)
            ruta.write_bytes(b'\xff\xfe')
            with self.assertRaises(ErrorDefinicion):
                cargar_maquina(ruta)

    def test_reglas_parciales_y_terminales_vacios(self):
        self.datos['transiciones'] = []
        self.datos['estados_aceptacion'] = []
        self.datos['estados_rechazo'] = []
        resultado = validar_definicion(self.datos).ejecutar('0')
        self.assertEqual(resultado.estado, EstadoEjecucion.RECHAZADA)
        self.assertIn('No hay transición', resultado.motivo)


class PruebasAlteradora(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maquina = cargar_maquina(MAQUINAS['alteradora'])

    def test_cuatro_cadenas_de_minimo_cinco(self):
        casos = json.loads((RAIZ / 'ejemplos/alteradora.json').read_text(encoding='utf-8'))
        self.assertEqual(len(casos), 4)
        self.assertEqual(len({c['entrada'] for c in casos}), 4)
        for caso in casos:
            with self.subTest(entrada=caso['entrada']):
                self.assertGreaterEqual(len(caso['entrada']), 5)
                r = self.maquina.ejecutar(caso['entrada'])
                self.assertEqual(r.aceptada, caso['aceptada'])
                self.assertEqual(r.final.contenido(), caso['salida'])
                self.assertEqual(len(r.pasos), caso['pasos'])
        self.assertEqual(self.maquina.ejecutar('11111').final.cabezal, -1)

    def test_oraculo_aritmetico_hasta_ocho_bits(self):
        for longitud in range(1, 9):
            for bits in itertools.product('01', repeat=longitud):
                entrada = ''.join(bits)
                esperado = format(int(entrada, 2) + 1, 'b').zfill(longitud)
                with self.subTest(entrada=entrada):
                    r = self.maquina.ejecutar(entrada, max_pasos=2 * longitud + 2)
                    self.assertTrue(r.aceptada)
                    self.assertEqual(r.final.contenido(), esperado)

    def test_entradas_invalidas_y_limite(self):
        for entrada in ('', '1010x', '10#01', '_', '101 01'):
            with self.subTest(entrada=entrada):
                self.assertEqual(self.maquina.ejecutar(entrada).estado, EstadoEjecucion.RECHAZADA)
        r = self.maquina.ejecutar('11111', max_pasos=11)
        self.assertEqual(r.estado, EstadoEjecucion.LIMITE_ALCANZADO)
        self.assertTrue(self.maquina.ejecutar('11111', max_pasos=12).aceptada)


class PruebasInterfaz(unittest.TestCase):
    def ejecutar_cli(self, *args, entrada=None):
        return subprocess.run([sys.executable, str(RAIZ / 'simulador.py'), *args],
                              input=entrada, text=True, capture_output=True, cwd=RAIZ.parent)

    def test_pasos_final_y_resumen(self):
        r = self.ejecutar_cli('--maquina', 'alteradora', '11111')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('Paso 0:', r.stdout)
        for numero in range(1, 13):
            self.assertIn(f'Paso {numero}: δ(', r.stdout)
        self.assertEqual(r.stdout.count('δ('), 12)
        self.assertIn('Cinta final: 100000', r.stdout)
        self.assertIn('Cabezal: -1', r.stdout)
        r = self.ejecutar_cli('--maquina', 'alteradora', '11111', '--solo-resumen')
        self.assertNotIn('Paso ', r.stdout)
        self.assertIn('Cinta final: 100000', r.stdout)

    def test_limite_y_cero_pasos(self):
        for limite in ('0', '11'):
            r = self.ejecutar_cli('--maquina', 'alteradora', '11111', '--max-pasos', limite)
            self.assertIn('LIMITE_ALCANZADO', r.stdout)
            self.assertIn('Ejecución incompleta', r.stdout)
        r = self.ejecutar_cli('--maquina', 'alteradora', '11111', '--max-pasos', '12')
        self.assertIn('Resultado: ACEPTADA', r.stdout)
        self.assertEqual(r.stdout.count('δ('), 12)

    def test_validar_y_errores_sin_traceback(self):
        r = self.ejecutar_cli('--yaml', str(MAQUINAS['alteradora']), '--validar')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('YAML válido', r.stdout)
        for args in (('--yaml', 'inexistente.yaml'), ('--max-pasos', '-1'),
                     ('--maquina', 'alteradora', '--yaml', str(MAQUINAS['alteradora']))):
            r = self.ejecutar_cli(*args)
            self.assertEqual(r.returncode, 2)
            self.assertNotIn('Traceback', r.stderr)
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'invalido.yaml'
            ruta.write_text('estados: [', encoding='utf-8')
            r = self.ejecutar_cli('--yaml', str(ruta), '--validar')
            self.assertEqual(r.returncode, 2)
            self.assertIn('línea', r.stderr)
            self.assertNotIn('Traceback', r.stderr)

    def test_reconocedora_compatible_y_menu(self):
        r = self.ejecutar_cli('111#010', '--solo-resumen')
        self.assertIn('Resultado: ACEPTADA', r.stdout)
        self.assertIn('Cinta final: XXX#YYY', r.stdout)
        r = self.ejecutar_cli('--maquina', 'alteradora', '--interactivo', entrada='1\n10100\n0\n')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('Cinta final: 10101', r.stdout)
        self.assertIn('Simulador cerrado', r.stdout)

    def test_cabezal_y_espacios_en_cinta(self):
        for c in (Configuracion('q', -12, ((0, '1'),), '_'),
                  Configuracion('q', 15, ((0, '1'),), '_'),
                  Configuracion('q', 0, (), '_')):
            with self.subTest(cabezal=c.cabezal):
                salida = io.StringIO()
                with redirect_stdout(salida):
                    mostrar_configuracion(c)
                lineas = salida.getvalue().splitlines()
                ancho = max(3, len(str(min(0, c.cabezal) - 1)),
                            len(str(max(0, c.cabezal) + 1)))
                columna = 10 + (c.cabezal - (min(0, c.cabezal) - 1)) * (ancho + 1) + (ancho - 1) // 2
                self.assertEqual(lineas[3].index('^'), columna)
                self.assertIn(str(c.cabezal), lineas[1])

    def test_vista_regla_ausente_y_rechazo_inicial(self):
        datos = yaml.safe_load((RAIZ / 'maquinas/alteradora_incremento.yaml').read_text(encoding='utf-8'))
        datos['transiciones'] = []
        for maquina, entrada in ((validar_definicion(datos), '0'),
                                 (cargar_maquina(MAQUINAS['alteradora']), 'X')):
            salida = io.StringIO()
            with redirect_stdout(salida):
                mostrar_resultado(maquina, entrada, 10)
            self.assertIn('Resultado: RECHAZADA', salida.getvalue())
            self.assertNotIn('Paso 1:', salida.getvalue())


if __name__ == '__main__':
    unittest.main()
