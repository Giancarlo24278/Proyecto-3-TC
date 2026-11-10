# Proyecto 3: simulador de máquinas de Turing

Simulador determinista de **una sola cinta**, con definición en YAML, ejecución
de todas las entradas configuradas, descripción de cada paso y cinta final.
Incluye una reconocedora de paquetes y una alteradora de incremento binario.

## Abrir en Visual Studio Code

1. Abre Visual Studio Code y selecciona **Archivo > Abrir carpeta**.
2. Selecciona **Proyecto-3-TC**, la raíz que contiene este README y `ejecutar.py`.
3. Abre **Terminal > Nueva terminal** y usa los comandos siguientes.

El proyecto no necesita copiarse dentro de otro archivo ni usa Live Server.
Se ejecuta con Python desde la terminal integrada. Requiere **Python 3.10 o
superior**; `python3 --version` (macOS/Linux) o `python --version` (Windows)
muestra la versión instalada.

## Instalar y ejecutar: macOS / Linux

Desde la raíz del repositorio:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r Proyecto3TC/requirements-dev.txt
.venv/bin/python ejecutar.py
```

En la computadora usada para este proyecto, si la terminal está en otra carpeta:

```bash
cd "/Users/luisestrada/Desktop/Proyecto-3-TC"
```

## Instalar y ejecutar: Windows / PowerShell

Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r Proyecto3TC/requirements-dev.txt
.\.venv\Scripts\python.exe ejecutar.py
```

No hace falta activar el entorno. En los ejemplos siguientes, cambia
`.venv/bin/python` por `.\.venv\Scripts\python.exe` si usas Windows.
La instalación necesita conexión a Internet. Solo se instala PyYAML; el motor,
el lanzador y las pruebas usan la biblioteca estándar de Python.

## Comandos para la demostración

```bash
# Ocho cadenas: cuatro de la reconocedora y cuatro de la alteradora.
.venv/bin/python ejecutar.py

# Ejecutar solo una máquina, leyendo sus cuatro inputs desde el YAML.
.venv/bin/python ejecutar.py reconocedora
.venv/bin/python ejecutar.py alteradora

# Vista corta para comprobar resultados; para el video usa la vista completa.
.venv/bin/python ejecutar.py --solo-resumen

# Validar el archivo sin simular.
.venv/bin/python Proyecto3TC/simulador.py --yaml Proyecto3TC/maquinas/reconocedora.yaml --validar
.venv/bin/python Proyecto3TC/simulador.py --yaml Proyecto3TC/maquinas/alteradora.yaml --validar

# Ejecutar un archivo YAML propio y todas sus entradas.
.venv/bin/python Proyecto3TC/simulador.py --yaml Proyecto3TC/maquinas/alteradora.yaml

# Ejecutar una cadena específica en lugar del lote.
.venv/bin/python Proyecto3TC/simulador.py --maquina alteradora "11111"

# Abrir el menú para introducir cadenas manualmente.
.venv/bin/python Proyecto3TC/simulador.py --maquina alteradora --interactivo

# Límite de pasos por cadena (predeterminado: 10000).
.venv/bin/python ejecutar.py alteradora --max-pasos 100

# Ejecutar todas las pruebas desde la raíz.
.venv/bin/python -m unittest discover -s Proyecto3TC/pruebas -t Proyecto3TC -v
```

Después de instalar el entorno en la raíz, también puedes ejecutar la tarea
**Demostración: ocho cadenas** desde **Terminal > Ejecutar tarea** en VS Code.
La configuración está en `.vscode/tasks.json` y usa el mismo entorno `.venv`.

## Qué se muestra

Por cada `input` aparece el paso 0 y cada transición posterior, con el estado,
los índices de cinta y `^` sobre el cabezal. `B` es el blanco en los YAML del
proyecto. `L` mueve a la izquierda, `R` a la derecha y `S` permanece en la celda.
La cinta admite posiciones negativas y se usa una única cinta por simulación.

El resumen indica `ACEPTADA`, `RECHAZADA` o `LIMITE_ALCANZADO`, junto al motivo,
los pasos, el estado y la cinta final. Un límite alcanzado significa ejecución
incompleta; su cinta es parcial. Una regla ausente significa rechazo. Las
entradas con símbolos ajenos al alfabeto también se rechazan, sin aplicar reglas.
Los errores de definición terminan con código 2; las simulaciones terminan con
código 0, sea su resultado aceptación, rechazo o límite. `Ctrl+C` interrumpe.

## Formato YAML del documento

Los archivos principales son:

- [Reconocedora](Proyecto3TC/maquinas/reconocedora.yaml).
- [Alteradora](Proyecto3TC/maquinas/alteradora.yaml).

Cada archivo contiene `mt:` y dentro `states`, `input_alphabet`, `tape_alphabet`,
`initial_state`, `accept_states`, `transitions` e `inputs`. Cada transición usa
`state`, `read`, `write`, `move` y `next`. `B` es el blanco predeterminado.
`name`, `blank_symbol` y `reject_states` son extensiones opcionales.
Los archivos originales con campos españoles se conservan por compatibilidad.

Ejemplo completo que cambia un primer `0` por `1`:

```yaml
mt:
  states: [q0, qf]
  input_alphabet: ['0', '1']
  tape_alphabet: ['0', '1', B]
  initial_state: q0
  accept_states: [qf]
  transitions:
    - state: q0
      read: ['0']
      write: ['1']
      move: R
      next: qf
  inputs:
    - '00000'
```

Se aceptan símbolos individuales o listas en `read`/`write`. **Interpretación de
las listas del ejemplo del documento:** son alternativas emparejadas sobre una
cinta. `read: [a, B]` y `write: [a, B]` definen `a → a` y `B → B`, manteniendo
el mismo movimiento y estado siguiente. No son dos cintas ni una operación
simultánea sobre dos celdas. Las dos listas deben tener igual longitud y no estar
vacías. Las reglas equivalentes repetidas del ejemplo se unifican; las que
definen resultados diferentes para el mismo estado y símbolo se rechazan.
Esta interpretación resuelve la notación ambigua del ejemplo y se documenta
explícitamente para explicarla al docente.

## Cadenas de evaluación

Todas las entradas tienen longitud mínima de cinco caracteres y están dentro
de `inputs` en sus respectivos YAML.

| Máquina | Entrada | Longitud | Resultado | Cinta final |
| --- | --- | --- | --- | --- |
| Reconocedora | `111#010` | 7 | Aceptada | `XXX#YYY` |
| Reconocedora | `1111#1010` | 9 | Aceptada | `XXXX#YYYY` |
| Reconocedora | `111#01` | 6 | Rechazada: faltan datos | Se muestra la cinta al detenerse. |
| Reconocedora | `11#010` | 6 | Rechazada: sobran datos | Se muestra la cinta al detenerse. |
| Alteradora | `10100` | 5 | Aceptada | `10101` |
| Alteradora | `10111` | 5 | Aceptada | `11000` |
| Alteradora | `00000` | 5 | Aceptada | `00001` |
| Alteradora | `11111` | 5 | Aceptada | `100000` |

La reconocedora compara una cantidad en unos con la cantidad de bits tras `#`.
La alteradora suma uno en binario, conserva el ancho mínimo y escribe una nueva
celda a la izquierda si hay acarreo final. No borra toda la cinta.

## Arquitectura y entrega del video

```text
YAML (mt + inputs)
  → lector_yaml.py: lectura segura, validación y normalización
  → motor.py: estados, reglas y una cinta con posiciones enteras
  → visualizacion.py: descripción instantánea de cada paso y cinta final
  → simulador.py: ejecución del lote o de una entrada
  → ejecutar.py: demostración de las dos máquinas desde la raíz
```

- [Lectura y visualización](Proyecto3TC/docs/lectura_visualizacion.md).
- [Diseño de la reconocedora](Proyecto3TC/docs/reconocedora.md).
- [Diseño de la alteradora](Proyecto3TC/docs/alteradora.md).

Para entregar, graba la ejecución completa de las ocho cadenas y la explicación
de la arquitectura, sube el video a YouTube como **no listado** y comparte su
enlace en la entrega. La grabación, subida y enlace deben completarse al hacer
la entrega. La dificultad
de las máquinas es parte de la evaluación del docente y no se garantiza una nota.
