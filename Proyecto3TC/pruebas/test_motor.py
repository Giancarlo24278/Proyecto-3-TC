"""Pruebas del motor y de la MT reconocedora de paquetes."""

import itertools
import json
from pathlib import Path
import unittest

from simulador import cargar_reconocedora
from motor import EstadoEjecucion, MaquinaTuring, Transicion


RAIZ = Path(__file__).resolve().parents[1]


def maquina_pequena(reglas, inicial="q0", aceptacion=("qa",), rechazo=("qr",)):
    return MaquinaTuring(
        estados={"q0", "q1", "qa", "qr"}, alfabeto_entrada={"0", "1"},
        alfabeto_cinta={"0", "1", "_"}, blanco="_", estado_inicial=inicial,
        estados_aceptacion=aceptacion, estados_rechazo=rechazo, transiciones=reglas,
    )


class PruebasMotor(unittest.TestCase):
    def test_cinta_negativa_y_blancos(self):
        m = maquina_pequena({
            ("q0", "0"): Transicion("q1", "_", "L"),
            ("q1", "_"): Transicion("qa", "1", "S"),
        })
        r = m.ejecutar("0")
        self.assertTrue(r.aceptada)
        self.assertEqual(r.final.cabezal, -1)
        self.assertEqual(r.final.celdas, ((-1, "1"),))
        self.assertEqual(r.final.ventana(-2, 1), ("_", "1", "_", "_"))
        self.assertEqual(r.final.leer(100), "_")
        self.assertEqual(r.final.contenido(), "1")

    def test_paso_a_paso_e_instantaneas(self):
        m = maquina_pequena({
            ("q0", "0"): Transicion("q1", "1", "R"),
            ("q1", "_"): Transicion("qa", "0", "S"),
        })
        s = m.iniciar("0")
        p1 = s.paso()
        self.assertEqual(p1.numero, 1)
        self.assertEqual(p1.simbolo_leido, "0")
        self.assertEqual(p1.antes.contenido(), "0")
        self.assertEqual(p1.despues.contenido(), "1")
        p2 = s.paso()
        self.assertEqual(p2.antes, p1.despues)
        self.assertEqual(s.resultado().final.contenido(), "10")
        self.assertEqual(p1.despues.contenido(), "1")
        self.assertIsNone(s.paso())
        self.assertEqual(len(s.resultado().pasos), 2)

    def test_limite_no_es_rechazo(self):
        m = maquina_pequena({("q0", "_"): Transicion("q0", "_", "R")})
        r = m.ejecutar("", max_pasos=4)
        self.assertEqual(r.estado, EstadoEjecucion.LIMITE_ALCANZADO)
        self.assertEqual(len(r.pasos), 4)
        self.assertEqual(r.final.cabezal, 4)

    def test_aceptar_exactamente_en_el_limite(self):
        m = maquina_pequena({("q0", "_"): Transicion("qa", "_", "S")})
        self.assertTrue(m.ejecutar("", max_pasos=1).aceptada)
        self.assertEqual(m.ejecutar("", max_pasos=0).estado, EstadoEjecucion.LIMITE_ALCANZADO)

    def test_limite_incluye_pasos_manuales(self):
        m = maquina_pequena({("q0", "_"): Transicion("q0", "_", "R")})
        s = m.iniciar("")
        s.paso()
        r = s.ejecutar(max_pasos=2)
        self.assertEqual(len(r.pasos), 2)
        self.assertEqual(r.estado, EstadoEjecucion.LIMITE_ALCANZADO)

    def test_regla_ausente_rechaza_sin_modificar_cinta(self):
        r = maquina_pequena({}).ejecutar("01", max_pasos=0)
        self.assertEqual(r.estado, EstadoEjecucion.RECHAZADA)
        self.assertIn("No hay transición", r.motivo)
        self.assertEqual(r.inicial, r.final)
        self.assertEqual(r.pasos, ())

    def test_estado_rechazo_explicito(self):
        r = maquina_pequena({("q0", "0"): Transicion("qr", "0", "S")}).ejecutar("0")
        self.assertEqual(r.estado, EstadoEjecucion.RECHAZADA)
        self.assertEqual(r.final.estado, "qr")

    def test_estado_inicial_terminal(self):
        r = maquina_pequena({}, inicial="qa").ejecutar("")
        self.assertTrue(r.aceptada)
        self.assertEqual(r.pasos, ())

    def test_entrada_invalida(self):
        r = maquina_pequena({}).ejecutar("X")
        self.assertEqual(r.estado, EstadoEjecucion.RECHAZADA)
        self.assertIn("alfabeto", r.motivo)
        self.assertEqual(r.pasos, ())

    def test_limites_invalidos(self):
        for valor in (-1, 1.5, True):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                maquina_pequena({}).ejecutar("", max_pasos=valor)

    def test_movimiento_invalido(self):
        with self.assertRaises(ValueError):
            maquina_pequena({("q0", "0"): Transicion("qa", "0", "D")})

    def test_ejecuciones_independientes(self):
        m = maquina_pequena({("q0", "0"): Transicion("qa", "1", "R")})
        self.assertEqual(m.ejecutar("0"), m.ejecutar("0"))


class PruebasReconocedora(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maquina = cargar_reconocedora()

    def test_cuatro_ejemplos_solicitados(self):
        casos = json.loads((RAIZ / "ejemplos/reconocedora.json").read_text(encoding="utf-8"))
        self.assertEqual(len(casos), 4)
        self.assertEqual(sum(c["aceptada"] for c in casos), 2)
        for caso in casos:
            with self.subTest(entrada=caso["entrada"]):
                self.assertGreaterEqual(len(caso["entrada"]), 5)
                r = self.maquina.ejecutar(caso["entrada"])
                self.assertEqual(r.aceptada, caso["aceptada"])
                self.assertNotEqual(r.estado, EstadoEjecucion.LIMITE_ALCANZADO)

    def test_exhaustivo_hasta_siete_caracteres(self):
        # Oráculo independiente: comparar formato y longitudes, sin simular marcas.
        for longitud in range(8):
            for simbolos in itertools.product("01#", repeat=longitud):
                entrada = "".join(simbolos)
                cantidad, separador, datos = entrada.partition("#")
                esperado = (separador == "#" and bool(cantidad)
                            and set(cantidad) <= {"1"}
                            and set(datos) <= {"0", "1"}
                            and len(cantidad) == len(datos))
                with self.subTest(entrada=entrada):
                    r = self.maquina.ejecutar(entrada)
                    self.assertNotEqual(r.estado, EstadoEjecucion.LIMITE_ALCANZADO)
                    self.assertEqual(r.aceptada, esperado)

    def test_paquete_mayor_y_cinta_final(self):
        r = self.maquina.ejecutar("1" * 20 + "#" + "01" * 10)
        self.assertTrue(r.aceptada)
        self.assertEqual(r.final.contenido(), "X" * 20 + "#" + "Y" * 20)

    def test_marcas_y_espacios_no_son_entrada(self):
        for entrada in ("XXX#YYY", "111#0 1", "111#01_", "111#01a"):
            with self.subTest(entrada=entrada):
                self.assertEqual(self.maquina.ejecutar(entrada).estado, EstadoEjecucion.RECHAZADA)


if __name__ == "__main__":
    unittest.main()
