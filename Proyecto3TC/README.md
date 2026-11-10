# Simulador de máquinas de Turing

Simulador determinista de **una cinta** con lectura y validación de YAML,
visualización de cada transición y de la cinta final. Incluye dos máquinas:

- **Reconocedora de paquetes** `cantidad#datos`: acepta cuando la cantidad de
  unos antes de `#` coincide con el número de bits después de `#`.
- **Alteradora de incremento binario**: suma uno a una cadena binaria no vacía.
  Por ejemplo, `10111 → 11000` y `11111 → 100000`.

## Instalación

Requiere **Python 3.10 o superior** y PyYAML. Abre una terminal dentro de
`Proyecto3TC` (la carpeta que contiene `simulador.py`).

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python simulador.py
```

### Windows / PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe simulador.py
```

No es necesario activar el entorno. En Windows, sustituye `.venv/bin/python`
por `.\.venv\Scripts\python.exe` en los ejemplos siguientes.

## Ejecución

El comando sin entrada abre el menú: **1** evalúa una cadena y **0** sale.
También se puede escribir `salir` o presionar `Ctrl+C`. Para abrir el menú de
la alteradora:

```bash
.venv/bin/python simulador.py --maquina alteradora
```

Para ejecutar directamente y ver todos los pasos:

```bash
.venv/bin/python simulador.py "111#010"
.venv/bin/python simulador.py --maquina alteradora "11111"
```

La salida muestra la configuración inicial (**paso 0**), cada regla
`δ(estado, leído) = (siguiente, escrito, movimiento)` y la cinta después de
aplicarla. `L` significa izquierda, `R` derecha y `S` permanecer. Los índices
identifican las celdas, `_` es el blanco y `^` señala el cabezal. La vista incluye
los índices negativos y el cabezal incluso fuera del contenido escrito.

Al terminar se muestran aceptación, rechazo o límite, el motivo, el número de
transiciones, el estado, el contenido final y la posición del cabezal. La cinta
final omite únicamente los blancos exteriores. En la reconocedora, `X` e `Y`
son marcas de símbolos emparejados; en la alteradora, la cinta es el binario
resultante. Si se alcanza el límite, la ejecución está incompleta y la cinta
es parcial.

Opciones adicionales:

```bash
# Cargar otro archivo (ruta relativa a la terminal o ruta absoluta).
.venv/bin/python simulador.py --yaml maquinas/alteradora_incremento.yaml "10111"

# Validar sin ejecutar ni abrir el menú.
.venv/bin/python simulador.py --maquina alteradora --validar
.venv/bin/python simulador.py --yaml maquinas/reconocedora_paquetes.yaml --validar

# Mostrar únicamente el resumen y la cinta final.
.venv/bin/python simulador.py --maquina alteradora "10100" --solo-resumen

# Limitar el número total de transiciones (predeterminado: 10000).
.venv/bin/python simulador.py --maquina alteradora "11111" --max-pasos 11
```

`--maquina` y `--yaml` son excluyentes. Sin selección se usa la reconocedora.
Las definiciones incluidas se encuentran a partir de la ubicación del programa,
por lo que también se puede ejecutar `simulador.py` desde otra carpeta.
`--max-pasos` acepta enteros no negativos; con cero se muestra la configuración
inicial y no se aplica ninguna transición. Los errores de definición se informan
sin traceback y terminan con código 2. Un resultado aceptado, rechazado o
incompleto es una simulación válida y termina con código 0.

## Cuatro cadenas de la alteradora

Todas tienen al menos cinco caracteres. Los casos ejecutables están en
[ejemplos/alteradora.json](ejemplos/alteradora.json).

| Entrada | Longitud | Cinta final | Pasos | Caso |
| --- | --- | --- | --- | --- |
| `10100` | 5 | `10101` | 7 | Sin acarreo. |
| `10111` | 5 | `11000` | 10 | Acarreo sobre tres unos. |
| `00000` | 5 | `00001` | 7 | Conserva ceros iniciales. |
| `11111` | 5 | `100000` | 12 | Acarreo final; escribe en la celda -1. |

```bash
.venv/bin/python simulador.py --maquina alteradora "10100"
.venv/bin/python simulador.py --maquina alteradora "10111"
.venv/bin/python simulador.py --maquina alteradora "00000"
.venv/bin/python simulador.py --maquina alteradora "11111"
```

## Documentación y pruebas

- [Lectura, validación y visualización](docs/lectura_visualizacion.md): alcance
  implementado, formato YAML, diagnósticos y conexión con el motor.
- [Diseño de la MT alteradora](docs/alteradora.md): definición formal,
  transiciones, corrección y traza completa de ejemplo.
- [Motor y MT reconocedora](docs/reconocedora.md): lenguaje, algoritmo,
  contrato del motor y sus cuatro ejemplos originales.

```bash
.venv/bin/python -m unittest discover -s pruebas -v
```

Las pruebas incluyen archivos YAML inválidos, los cuatro casos de cada máquina,
3280 entradas de la reconocedora (longitud 0 a 7), 510 binarios de la alteradora
(longitud 1 a 8) comparados con una suma aritmética, límites, cinta con índices
negativos y ejecución de la interfaz desde otra carpeta.
