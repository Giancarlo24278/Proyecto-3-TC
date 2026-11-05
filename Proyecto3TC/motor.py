"""Motor de máquinas de Turing deterministas de una sola cinta.

No lee YAML ni imprime: recibe una definición ya normalizada y entrega datos
inmutables para que otro módulo pueda dibujar la ejecución.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping


class EstadoEjecucion(str, Enum):
    EN_CURSO = "en_curso"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    LIMITE_ALCANZADO = "limite_alcanzado"


@dataclass(frozen=True)
class Transicion:
    siguiente: str
    escribir: str
    mover: str  # L: izquierda, R: derecha, S: permanecer.


@dataclass(frozen=True)
class Configuracion:
    estado: str
    cabezal: int
    celdas: tuple[tuple[int, str], ...]  # Solo celdas no blancas, ordenadas.
    blanco: str

    def leer(self, posicion: int) -> str:
        return dict(self.celdas).get(posicion, self.blanco)

    def ventana(self, inicio: int, fin: int) -> tuple[str, ...]:
        """Contenido entre inicio y fin, ambos incluidos (también negativos)."""
        if fin < inicio:
            raise ValueError("El fin de la ventana debe ser mayor o igual al inicio.")
        cinta = dict(self.celdas)
        return tuple(cinta.get(i, self.blanco) for i in range(inicio, fin + 1))

    def contenido(self) -> str:
        """Contenido entre las celdas extremas no blancas, sin blancos exteriores."""
        if not self.celdas:
            return ""
        return "".join(self.ventana(self.celdas[0][0], self.celdas[-1][0]))


@dataclass(frozen=True)
class Paso:
    numero: int
    antes: Configuracion
    simbolo_leido: str
    transicion: Transicion
    despues: Configuracion


@dataclass(frozen=True)
class Resultado:
    estado: EstadoEjecucion
    motivo: str
    inicial: Configuracion
    final: Configuracion
    pasos: tuple[Paso, ...]

    @property
    def aceptada(self) -> bool:
        return self.estado == EstadoEjecucion.ACEPTADA


class MaquinaTuring:
    """Definición reutilizable; cada simulación tiene su propia cinta y cabezal."""

    def __init__(
        self,
        *,
        estados: Iterable[str],
        alfabeto_entrada: Iterable[str],
        alfabeto_cinta: Iterable[str],
        blanco: str,
        estado_inicial: str,
        estados_aceptacion: Iterable[str],
        estados_rechazo: Iterable[str],
        transiciones: Mapping[tuple[str, str], Transicion],
    ):
        self.estados = frozenset(estados)
        self.alfabeto_entrada = frozenset(alfabeto_entrada)
        self.alfabeto_cinta = frozenset(alfabeto_cinta)
        self.blanco = blanco
        self.estado_inicial = estado_inicial
        self.estados_aceptacion = frozenset(estados_aceptacion)
        self.estados_rechazo = frozenset(estados_rechazo)
        self.transiciones = dict(transiciones)
        self._validar_definicion()

    def _validar_definicion(self) -> None:
        """Invariantes del motor; la lectura y validación del YAML es externa."""
        if not self.estados or not all(isinstance(q, str) and q for q in self.estados):
            raise ValueError("Los estados deben ser nombres no vacíos.")
        if not all(isinstance(s, str) and len(s) == 1 for s in self.alfabeto_cinta):
            raise ValueError("Cada símbolo de cinta debe tener un carácter.")
        if self.blanco not in self.alfabeto_cinta:
            raise ValueError("El blanco debe pertenecer al alfabeto de cinta.")
        if not self.alfabeto_entrada <= self.alfabeto_cinta or self.blanco in self.alfabeto_entrada:
            raise ValueError("El alfabeto de entrada debe estar en el de cinta y excluir el blanco.")
        terminales = self.estados_aceptacion | self.estados_rechazo
        if self.estado_inicial not in self.estados or not terminales <= self.estados:
            raise ValueError("Los estados inicial y terminales deben estar declarados.")
        if self.estados_aceptacion & self.estados_rechazo:
            raise ValueError("Un estado no puede aceptar y rechazar a la vez.")
        for (origen, leido), t in self.transiciones.items():
            if origen not in self.estados or t.siguiente not in self.estados:
                raise ValueError("Una transición hace referencia a un estado no declarado.")
            if origen in terminales:
                raise ValueError("Los estados terminales no deben tener transiciones.")
            if leido not in self.alfabeto_cinta or t.escribir not in self.alfabeto_cinta:
                raise ValueError("Una transición usa símbolos no declarados.")
            if t.mover not in {"L", "R", "S"}:
                raise ValueError("El movimiento debe ser L, R o S.")

    def iniciar(self, entrada: str) -> "Simulacion":
        return Simulacion(self, entrada)

    def ejecutar(self, entrada: str, max_pasos: int = 10_000) -> Resultado:
        return self.iniciar(entrada).ejecutar(max_pasos)


class Simulacion:
    """Una ejecución paso a paso con cinta ilimitada en ambas direcciones."""

    def __init__(self, maquina: MaquinaTuring, entrada: str):
        if not isinstance(entrada, str):
            raise TypeError("La entrada debe ser una cadena.")
        self.maquina = maquina
        self._cinta = {i: s for i, s in enumerate(entrada) if s != maquina.blanco}
        self._cabezal = 0
        self._estado = maquina.estado_inicial
        self._pasos: list[Paso] = []
        self.estado = EstadoEjecucion.EN_CURSO
        self.motivo = ""
        self.inicial = self.configuracion()
        invalidos = set(entrada) - maquina.alfabeto_entrada
        if invalidos:
            self.estado = EstadoEjecucion.RECHAZADA
            self.motivo = f"Símbolos fuera del alfabeto de entrada: {sorted(invalidos)!r}."
        else:
            self._comprobar_terminal()

    def configuracion(self) -> Configuracion:
        return Configuracion(self._estado, self._cabezal,
                             tuple(sorted(self._cinta.items())), self.maquina.blanco)

    def _comprobar_terminal(self) -> None:
        if self._estado in self.maquina.estados_aceptacion:
            self.estado = EstadoEjecucion.ACEPTADA
            self.motivo = "Se alcanzó un estado de aceptación."
        elif self._estado in self.maquina.estados_rechazo:
            self.estado = EstadoEjecucion.RECHAZADA
            self.motivo = "Se alcanzó un estado de rechazo."

    def paso(self) -> Paso | None:
        """Aplica una transición; devuelve None si no se aplica ninguna."""
        if self.estado != EstadoEjecucion.EN_CURSO:
            return None
        antes = self.configuracion()
        leido = self._cinta.get(self._cabezal, self.maquina.blanco)
        transicion = self.maquina.transiciones.get((self._estado, leido))
        if transicion is None:
            self.estado = EstadoEjecucion.RECHAZADA
            self.motivo = f"No hay transición para ({self._estado}, {leido!r})."
            return None
        if transicion.escribir == self.maquina.blanco:
            self._cinta.pop(self._cabezal, None)
        else:
            self._cinta[self._cabezal] = transicion.escribir
        self._cabezal += {"L": -1, "R": 1, "S": 0}[transicion.mover]
        self._estado = transicion.siguiente
        paso = Paso(len(self._pasos) + 1, antes, leido, transicion, self.configuracion())
        self._pasos.append(paso)
        self._comprobar_terminal()
        return paso

    def resultado(self) -> Resultado:
        return Resultado(self.estado, self.motivo, self.inicial,
                         self.configuracion(), tuple(self._pasos))

    def ejecutar(self, max_pasos: int = 10_000) -> Resultado:
        """Continúa hasta detenerse o agotar el total de transiciones permitido.

        El límite cuenta desde el inicio de esta simulación, incluidos los pasos
        manuales. Alcanzarlo no demuestra rechazo y se informa por separado.
        """
        if isinstance(max_pasos, bool) or not isinstance(max_pasos, int) or max_pasos < 0:
            raise ValueError("max_pasos debe ser un entero no negativo.")
        while self.estado == EstadoEjecucion.EN_CURSO:
            # La falta de regla demuestra rechazo sin consumir otra transición.
            leido = self._cinta.get(self._cabezal, self.maquina.blanco)
            if (self._estado, leido) not in self.maquina.transiciones:
                self.paso()
                break
            if len(self._pasos) >= max_pasos:
                self.estado = EstadoEjecucion.LIMITE_ALCANZADO
                self.motivo = f"Se alcanzó el límite de {max_pasos} transiciones."
                break
            self.paso()
        return self.resultado()
