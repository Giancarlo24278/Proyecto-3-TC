"""Lectura segura y validación del formato YAML compartido por las MT."""

from dataclasses import dataclass
from pathlib import Path

import yaml

from motor import MaquinaTuring, Transicion


class ErrorDefinicion(ValueError):
    """Archivo ilegible o definición de MT inválida, con diagnóstico legible."""


class _CargadorSinDuplicados(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        claves = set()
        for clave_nodo, _ in node.value:
            clave = self.construct_object(clave_nodo, deep=deep)
            if not isinstance(clave, str):
                raise yaml.constructor.ConstructorError(
                    None, None, "Las claves deben ser cadenas.", clave_nodo.start_mark
                )
            if clave in claves:
                raise yaml.constructor.ConstructorError(
                    None, None, f"Clave YAML duplicada: {clave!r}.", clave_nodo.start_mark
                )
            claves.add(clave)
        return super().construct_mapping(node, deep=deep)


_LISTAS = {
    "estados", "alfabeto_entrada", "alfabeto_cinta",
    "estados_aceptacion", "estados_rechazo",
}
_ESCALARES = {"blanco", "estado_inicial"}
_CAMPOS = _LISTAS | _ESCALARES | {"transiciones"}
_REGLA = {"origen", "leer", "siguiente", "escribir", "mover"}


def _campos(datos, requeridos, opcionales, contexto):
    if not isinstance(datos, dict):
        raise ErrorDefinicion(f"{contexto}: se esperaba un mapa de campos.")
    if not all(isinstance(clave, str) for clave in datos):
        raise ErrorDefinicion(f"{contexto}: las claves deben ser cadenas.")
    faltantes = requeridos - datos.keys()
    desconocidos = datos.keys() - requeridos - opcionales
    if faltantes:
        raise ErrorDefinicion(f"{contexto}: faltan campos {sorted(faltantes)}.")
    if desconocidos:
        raise ErrorDefinicion(f"{contexto}: campos desconocidos {sorted(desconocidos)}.")


def _cadena(valor, contexto, simbolo=False):
    if not isinstance(valor, str) or not valor.strip():
        raise ErrorDefinicion(
            f"{contexto}: se esperaba una cadena no vacía; escribe los símbolos entre comillas."
        )
    if simbolo and len(valor) != 1:
        raise ErrorDefinicion(f"{contexto}: cada símbolo debe tener un carácter.")


def _validar_modelo(datos) -> MaquinaTuring:
    """Valida estructura y semántica antes de construir la máquina del motor.

    Las listas de estados terminales y las reglas pueden estar vacías. Las
    transiciones parciales son válidas: una regla ausente implica rechazo.
    """
    _campos(datos, _CAMPOS, {"nombre"}, "Definición")
    if "nombre" in datos:
        _cadena(datos["nombre"], "nombre")
    for campo in sorted(_LISTAS):
        valores = datos[campo]
        if not isinstance(valores, list):
            raise ErrorDefinicion(f"{campo}: se esperaba una lista.")
        vistos = set()
        for indice, valor in enumerate(valores, 1):
            _cadena(valor, f"{campo}[{indice}]", campo.startswith("alfabeto_"))
            if valor in vistos:
                raise ErrorDefinicion(f"{campo}: valor duplicado {valor!r}.")
            vistos.add(valor)
    for campo in sorted(_ESCALARES):
        _cadena(datos[campo], campo, campo == "blanco")
    if not isinstance(datos["transiciones"], list):
        raise ErrorDefinicion("transiciones: se esperaba una lista de reglas.")

    reglas = {}
    for indice, regla in enumerate(datos["transiciones"], 1):
        contexto = f"transiciones[{indice}]"
        _campos(regla, _REGLA, set(), contexto)
        for campo in sorted(_REGLA):
            _cadena(regla[campo], f"{contexto}.{campo}", campo in {"leer", "escribir"})
        clave = (regla["origen"], regla["leer"])
        if clave in reglas:
            raise ErrorDefinicion(f"{contexto}: transición duplicada para {clave!r}.")
        if regla["origen"] not in datos["estados"] or regla["siguiente"] not in datos["estados"]:
            raise ErrorDefinicion(f"{contexto}: estado no declarado.")
        if regla["origen"] in datos["estados_aceptacion"] + datos["estados_rechazo"]:
            raise ErrorDefinicion(f"{contexto}: un estado terminal no puede tener reglas de salida.")
        if regla["leer"] not in datos["alfabeto_cinta"] or regla["escribir"] not in datos["alfabeto_cinta"]:
            raise ErrorDefinicion(f"{contexto}: símbolo no declarado en alfabeto_cinta.")
        if regla["mover"] not in {"L", "R", "S"}:
            raise ErrorDefinicion(f"{contexto}.mover: debe ser L, R o S.")
        reglas[clave] = Transicion(regla["siguiente"], regla["escribir"], regla["mover"])
    try:
        return MaquinaTuring(
            **{campo: datos[campo] for campo in _LISTAS | _ESCALARES},
            transiciones=reglas,
        )
    except ValueError as error:
        raise ErrorDefinicion(f"Definición inválida: {error}") from error


@dataclass(frozen=True)
class ProyectoMT:
    """Una definición validada y las entradas que acompañan al YAML.

    None indica un archivo antiguo sin entradas; () un lote configurado vacío.
    """

    maquina: MaquinaTuring
    entradas: tuple[str, ...] | None


def _normalizar_pdf(datos):
    _campos(datos, {"mt"}, set(), "Definición")
    mt = datos["mt"]
    requeridos = {
        "states", "input_alphabet", "tape_alphabet", "initial_state",
        "accept_states", "transitions", "inputs",
    }
    _campos(mt, requeridos, {"name", "blank_symbol", "reject_states"}, "mt")
    if not isinstance(mt["inputs"], list):
        raise ErrorDefinicion("mt.inputs: se esperaba una lista de cadenas.")
    for indice, entrada in enumerate(mt["inputs"], 1):
        if not isinstance(entrada, str):
            raise ErrorDefinicion(
                f"mt.inputs[{indice}]: se esperaba una cadena; usa comillas para los binarios."
            )
    normalizado = {
        "estados": mt["states"], "alfabeto_entrada": mt["input_alphabet"],
        "alfabeto_cinta": mt["tape_alphabet"],
        "estado_inicial": mt["initial_state"],
        "estados_aceptacion": mt["accept_states"],
        "estados_rechazo": mt.get("reject_states", []),
        "blanco": mt.get("blank_symbol", "B"), "transiciones": [],
    }
    if "name" in mt:
        normalizado["nombre"] = mt["name"]
    if not isinstance(mt["transitions"], list):
        raise ErrorDefinicion("mt.transitions: se esperaba una lista de reglas.")
    reglas = {}
    for indice, regla in enumerate(mt["transitions"], 1):
        contexto = f"mt.transitions[{indice}]"
        _campos(regla, {"state", "read", "write", "move", "next"}, set(), contexto)
        for campo in ("state", "move", "next"):
            _cadena(regla[campo], f"{contexto}.{campo}")
        leidos, escritos = regla["read"], regla["write"]
        if isinstance(leidos, list) or isinstance(escritos, list):
            if (not isinstance(leidos, list) or not isinstance(escritos, list)
                    or not leidos or len(leidos) != len(escritos)):
                raise ErrorDefinicion(
                    f"{contexto}: read y write deben ser listas no vacías de igual longitud."
                )
        else:
            leidos, escritos = [leidos], [escritos]
        for leido, escrito in zip(leidos, escritos):
            _cadena(leido, f"{contexto}.read", simbolo=True)
            _cadena(escrito, f"{contexto}.write", simbolo=True)
            nueva = {
                "origen": regla["state"], "leer": leido,
                "siguiente": regla["next"], "escribir": escrito, "mover": regla["move"],
            }
            clave = (regla["state"], leido)
            if clave in reglas:
                if reglas[clave] != nueva:
                    raise ErrorDefinicion(
                        f"{contexto}: transición duplicada incompatible para {clave!r}."
                    )
                # El ejemplo del documento repite exactamente la regla de B.
                # Reutilizar la misma regla no introduce no determinismo.
                continue
            reglas[clave] = nueva
            normalizado["transiciones"].append(nueva)
    return normalizado, tuple(mt["inputs"])


def validar_proyecto(datos) -> ProyectoMT:
    """Acepta el esquema mt del proyecto y conserva el formato español anterior."""
    if isinstance(datos, dict) and "mt" in datos:
        modelo, entradas = _normalizar_pdf(datos)
    else:
        modelo, entradas = datos, None
    return ProyectoMT(_validar_modelo(modelo), entradas)


def validar_definicion(datos) -> MaquinaTuring:
    """API compatible: valida cualquiera de los formatos y devuelve la MT."""
    return validar_proyecto(datos).maquina


def cargar_proyecto(ruta: str | Path) -> ProyectoMT:
    """Lee UTF-8 con un SafeLoader que detecta claves repetidas."""
    ruta = Path(ruta)
    try:
        with ruta.open(encoding="utf-8") as archivo:
            datos = yaml.load(archivo, Loader=_CargadorSinDuplicados)
    except (OSError, UnicodeError) as error:
        raise ErrorDefinicion(f"No se pudo leer {ruta}: {error}") from error
    except yaml.YAMLError as error:
        marca = getattr(error, "problem_mark", None)
        ubicacion = f" (línea {marca.line + 1}, columna {marca.column + 1})" if marca else ""
        detalle = getattr(error, "problem", None) or str(error)
        raise ErrorDefinicion(f"YAML inválido en {ruta}{ubicacion}: {detalle}") from error
    try:
        return validar_proyecto(datos)
    except ErrorDefinicion as error:
        raise ErrorDefinicion(f"{ruta}: {error}") from error


def cargar_maquina(ruta: str | Path) -> MaquinaTuring:
    """API compatible para consumidores que solo necesitan la máquina."""
    return cargar_proyecto(ruta).maquina
