# Lectura del YAML y visualización

## Parte implementada

Se completó la integración que faltaba sobre el motor existente:

| Archivo | Responsabilidad |
| --- | --- |
| `lector_yaml.py` | Leer UTF-8, validar estructura y reglas, construir `MaquinaTuring`. |
| `visualizacion.py` | Dibujar índices, símbolos, cabezal y estado; imprimir cada regla y resultado. |
| `simulador.py` | Seleccionar máquina o archivo, validar, ejecutar y ofrecer el menú. |
| `maquinas/alteradora_incremento.yaml` | Definir la MT que incrementa un binario. |
| `ejemplos/alteradora.json` | Registrar cuatro entradas, salidas, pasos y explicación. |
| `pruebas/test_integracion.py` | Verificar lector, alteradora e interfaz junto a las pruebas existentes. |

`motor.py` conserva su implementación y sus objetos `Configuracion`, `Paso` y
`Resultado`. `cargar_reconocedora()` permanece disponible para las integraciones
previas, pero ahora usa el lector general. No se añaden dependencias aparte de
PyYAML, ya requerido por el proyecto.

## Formato YAML

La raíz debe ser un mapa. Campos obligatorios:

| Campo | Tipo y significado |
| --- | --- |
| `estados` | Lista de nombres de estados, no vacía y sin duplicados. |
| `alfabeto_entrada` | Lista de símbolos de un carácter, sin duplicados. |
| `alfabeto_cinta` | Lista de símbolos de un carácter, sin duplicados; incluye al blanco y al alfabeto de entrada. |
| `blanco` | Símbolo de un carácter; no pertenece al alfabeto de entrada. |
| `estado_inicial` | Nombre de un estado declarado. |
| `estados_aceptacion` | Lista de estados declarados que detienen con aceptación. |
| `estados_rechazo` | Lista de estados declarados que detienen con rechazo. |
| `transiciones` | Lista de mapas con los cinco campos de cada regla. |

`nombre` es opcional y, si aparece, debe ser una cadena no vacía. No se admiten
campos desconocidos, nombres vacíos ni valores compuestos solo de espacios.
Las listas de aceptación, rechazo y transiciones pueden estar vacías. Las listas
de estados y alfabetos contienen cadenas; escribe `'0'`, `'1'` y `'#'` entre
comillas para que YAML no los interprete como números, booleanos o comentarios.
El índice de una regla en los diagnósticos empieza en 1.

```yaml
- origen: q_sumar
  leer: '0'
  siguiente: q_aceptar
  escribir: '1'
  mover: S
```

Cada regla debe contener exactamente `origen`, `leer`, `siguiente`, `escribir` y
`mover`, todos cadenas. Los estados y símbolos deben estar declarados, los
movimientos son `L`, `R` o `S` y los terminales no admiten reglas de salida.
Aceptación y rechazo son conjuntos disjuntos. Solo puede existir una regla por
par `(origen, leer)`: se detecta el duplicado antes de crear el diccionario.
Se permiten tablas parciales; una regla ausente significa rechazo, según el
contrato del motor.

También se rechazan **claves YAML repetidas**, tanto en la raíz como dentro de
una regla. El lector deriva de `yaml.SafeLoader`, por lo que las etiquetas de
objetos Python no se ejecutan. No se permiten claves no textuales ni varios
documentos dentro de un mismo archivo.

## Flujo y diagnósticos

1. `cargar_maquina(ruta)` lee el archivo UTF-8 con el cargador seguro.
2. `validar_definicion(datos)` comprueba los campos, sus tipos y cada regla.
3. Se crea `MaquinaTuring`; el motor comprueba además sus invariantes semánticas.
4. La interfaz recibe la máquina validada y comienza la simulación.

Los problemas se exponen mediante `ErrorDefinicion`, derivada de `ValueError`.
Un error de sintaxis incluye archivo, línea y columna cuando PyYAML las aporta.
Los errores de estructura identifican el campo o la regla; los errores
semánticos del motor conservan su explicación. Un archivo inexistente o con
codificación inválida también produce un diagnóstico controlado. La interfaz
escribe el error en stderr y sale con código 2, sin traceback.

```python
from lector_yaml import cargar_maquina

maquina = cargar_maquina('maquinas/alteradora_incremento.yaml')
resultado = maquina.ejecutar('11111', max_pasos=100)
assert resultado.final.contenido() == '100000'
```

## Visualización de la ejecución

La visualización es textual en terminal y funciona con ambas máquinas y con
otras definiciones compatibles. Primero dibuja el paso 0. Cada llamada a
`simulacion.paso()` aplica una única transición y genera una vista con:

- Número de paso y regla aplicada, incluyendo lectura, escritura y movimiento.
- Estado y posición del cabezal **después** de esa transición.
- Índices de las celdas y símbolos de la cinta, con blancos de margen.
- Marcador `^` alineado con la celda del cabezal.

La configuración previa de un paso corresponde a la vista del paso anterior.
No se omiten transiciones de regreso, marcas o movimientos sobre blancos. El
intervalo dibujado incluye el origen, el contenido no blanco y el cabezal,
incluso si sus índices son negativos. La anchura de las columnas se ajusta a
los índices. El resumen siempre vuelve a dibujar la cinta final y distingue
`ACEPTADA`, `RECHAZADA` y `LIMITE_ALCANZADO`.

La interfaz usa `simulacion.ejecutar(max_pasos=...)` al finalizar el recorrido
visible; el límite cuenta desde el inicio, sin repetir las transiciones ya
mostradas. Así se respeta la aceptación exactamente en el último paso permitido
y el rechazo por regla ausente sin consumir otro paso. `--solo-resumen` ejecuta
la misma máquina y omite la impresión intermedia. No hay pausas entre pasos:
la traza completa puede revisarse en la terminal o guardarse redirigiendo stdout.

El límite predeterminado es 10000 transiciones. Alcanzarlo no prueba rechazo;
la vista lo identifica como ejecución incompleta. El motor conserva todas las
instantáneas en memoria, incluso con `--solo-resumen`. Una traza larga puede
ocupar bastante salida y memoria; se puede reducir `--max-pasos`.

## Verificación y ejecución

`pruebas/test_integracion.py` cubre errores de sintaxis, estructura, tipos,
duplicados, estados y símbolos externos, movimientos inválidos y terminales con
salidas. También verifica ausencia de archivo, UTF-8 inválido y etiquetas no
seguras; la alteradora se compara con un oráculo aritmético independiente.
Las pruebas de CLI verifican selección de YAML, menús, trazas completas, resumen,
rechazo, límite y aceptación justo en el límite, así como la alineación del
cabezal con índices negativos y positivos fuera del contenido.

Las instrucciones de instalación para macOS, Linux y Windows, los comandos para
validar, simular y ejecutar las pruebas están en [README](../README.md).
