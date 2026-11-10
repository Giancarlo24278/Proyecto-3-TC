# Lectura del YAML y visualización

## Arquitectura

| Archivo | Responsabilidad |
| --- | --- |
| `lector_yaml.py` | Leer UTF-8, validar los dos formatos y crear la MT junto a sus entradas. |
| `motor.py` | Simular una cinta, estado, cabezal y reglas; guardar configuraciones inmutables. |
| `visualizacion.py` | Dibujar índices, símbolos, cabezal y estado; imprimir cada regla y resultado. |
| `simulador.py` | Seleccionar archivo, validar y ejecutar una cadena, un lote o el menú. |
| `../../ejecutar.py` | Lanzar desde la raíz las cuatro entradas de cada máquina. |

El motor no interpreta YAML ni suma binarios mediante código especial: ambas
máquinas se definen exclusivamente con reglas. Cada entrada inicia una nueva
simulación con cinta y cabezal independientes.

## Esquema del documento del proyecto

La raíz contiene únicamente `mt`. Dentro de ese mapa son obligatorios:

| Campo | Tipo y significado |
| --- | --- |
| `states` | Lista no vacía de nombres de estados, sin duplicados. |
| `input_alphabet` | Lista de símbolos de entrada de un carácter, sin duplicados. |
| `tape_alphabet` | Lista de símbolos de un carácter; contiene entrada y blanco. |
| `initial_state` | Estado inicial declarado. |
| `accept_states` | Lista de estados de aceptación declarados. |
| `transitions` | Lista de mapas con `state`, `read`, `write`, `move` y `next`. |
| `inputs` | Lista de cadenas que se simulan en orden. |

Se aceptan como extensiones opcionales `name`, `blank_symbol` y `reject_states`.
El blanco predeterminado es `B`. El alfabeto de entrada no contiene el blanco.
Los estados de rechazo predeterminados forman una lista vacía; la falta de regla
sigue significando rechazo. Estados de aceptación y rechazo son disjuntos y no
tienen transiciones de salida. `L`, `R` y `S` son los movimientos permitidos.
No se admiten campos desconocidos ni nombres vacíos o compuestos solo de espacios.

`inputs` admite una lista vacía, que termina sin abrir el menú, y admite la cadena
vacía como caso a simular. Los elementos deben ser cadenas: escribe los binarios
entre comillas para que YAML no elimine ceros iniciales ni los convierta en
números. Una entrada con símbolos ajenos al alfabeto produce rechazo de esa
cadena, y no impide ejecutar las demás.

### Interpretación de read y write

El ejemplo del documento utiliza listas pese a exigir una sola cinta y no
precisa su semántica. Se adopta y documenta esta interpretación: las listas son
alternativas emparejadas para una única celda por transición.

```yaml
- state: q0
  read: [a, B]
  write: [X, Y]
  move: R
  next: q1
```

Esto equivale a dos reglas: al leer `a` escribe `X`; al leer `B` escribe `Y`.
En ambos casos avanza una celda y entra en `q1`. No se crean dos cintas ni se
leen dos posiciones a la vez. Ambas listas deben tener igual longitud y ser no
vacías. También se admiten símbolos escalares, como `read: a` y `write: X`.
Si uno de esos campos es lista, el otro también debe serlo.

El ejemplo original repite la misma regla del blanco al expandir dos listas.
El normalizador unifica reglas exactamente equivalentes. Una repetición con
diferente escritura, movimiento o siguiente estado se rechaza porque introduciría
no determinismo. Las claves YAML repetidas siempre son un error.

## Compatibilidad y API

Se conservan los YAML anteriores `reconocedora_paquetes.yaml` y
`alteradora_incremento.yaml`. Su estructura usa `estados`, `alfabeto_entrada`,
`alfabeto_cinta`, `blanco`, `estado_inicial`, `estados_aceptacion`,
`estados_rechazo` y `transiciones`. Cada regla usa `origen`, `leer`, `siguiente`,
`escribir` y `mover`. En ese formato no se admite `inputs` y los duplicados de
transición se rechazan incluso si son equivalentes, preservando el contrato
anterior. Esos archivos usan `_` como blanco.

`cargar_proyecto(ruta)` devuelve un `ProyectoMT` con `maquina` y `entradas`.
`entradas` es una tupla para el formato nuevo; `None` identifica un archivo
anterior sin lote. `validar_proyecto(datos)` ofrece lo mismo desde datos ya
leídos. `cargar_maquina(ruta)` y `validar_definicion(datos)` conservan la API
que devuelve solo `MaquinaTuring` y admiten ambos formatos.

```python
from lector_yaml import cargar_proyecto

proyecto = cargar_proyecto('maquinas/alteradora.yaml')
for entrada in proyecto.entradas:
    resultado = proyecto.maquina.ejecutar(entrada)
    print(entrada, resultado.estado.value, resultado.final.contenido())
```

## Validación y diagnósticos

El cargador deriva de `yaml.SafeLoader`: no ejecuta etiquetas de objetos Python,
comprueba las claves repetidas y no admite claves no textuales ni varios
documentos en el mismo archivo. Después se comprueban tipos y campos, se
normalizan las reglas y se verifican los invariantes semánticos del motor.

Los problemas se exponen como `ErrorDefinicion`, derivada de `ValueError`. Los
errores de sintaxis incluyen archivo, línea y columna cuando PyYAML los aporta.
Los errores de estructura identifican el campo o la regla, con índices desde 1.
Se controlan archivos inexistentes y UTF-8 inválido. La interfaz informa el error
en stderr y termina con código 2, sin traceback.

## Visualización y ejecución por lotes

Por cada cadena, la interfaz muestra su número en el lote, la configuración
inicial (paso 0), y cada transición con lectura, escritura y movimiento. La vista
incluye estado, índices, contenido de cinta y un `^` alineado con el cabezal.
Cada vista posterior corresponde a una única transición. No se omiten regresos,
marcas ni movimientos sobre blancos. La ventana incluye el origen, todos los
símbolos no blancos y el cabezal, incluso en posiciones negativas.

El resumen siempre vuelve a dibujar la cinta final e informa aceptación,
rechazo o límite. Se omiten únicamente los blancos exteriores del contenido
final. El límite predeterminado es 10000 transiciones **por cadena**. Alcanzarlo
no prueba rechazo y la cinta se identifica como parcial. La aceptación justo
en el último paso permitido se respeta. `--solo-resumen` omite la impresión de
pasos, conservando el mismo resultado. No hay pausas entre pasos; la traza se
puede revisar con el scroll o guardar redirigiendo stdout.

Sin cadena explícita se recorren todos los `inputs` del YAML. Una cadena pasada
como argumento sustituye al lote. `--interactivo` abre el menú manual. Los
archivos anteriores sin entradas abren el menú si no se pasa una cadena.
`--validar` verifica el archivo y cuenta sus entradas sin simular.

El motor conserva las instantáneas del historial en memoria aun en modo resumen.
El costo del historial es O(P·C), para P pasos y un máximo de C celdas no blancas;
la cinta sigue siendo única. Consulta el [README principal](../../README.md)
para instalar, ejecutar, usar VS Code y correr las pruebas.
