# Simulador de máquinas de Turing

El [README de la raíz](../README.md) contiene la instalación completa, las
instrucciones para Visual Studio Code y todos los comandos de ejecución.
Abre la carpeta raíz `Proyecto-3-TC`, crea allí `.venv` y ejecuta desde allí:

```bash
.venv/bin/python ejecutar.py
```

En Windows / PowerShell:

```powershell
.\.venv\Scripts\python.exe ejecutar.py
```

Se ejecutan las ocho cadenas definidas en `mt.inputs`: cuatro de la
[reconocedora](maquinas/reconocedora.yaml) y cuatro de la
[alteradora](maquinas/alteradora.yaml). El programa muestra cada transición,
la cinta y el cabezal, además del resultado y la cinta final de cada cadena.
Los comandos aceptan `--solo-resumen` y `--max-pasos`.

Para ejecutar únicamente una máquina desde la raíz:

```bash
.venv/bin/python ejecutar.py reconocedora
.venv/bin/python ejecutar.py alteradora
```

Para introducir una cadena manualmente se puede pasar como argumento o abrir
el menú con `--interactivo`. Sin entrada ni esa opción, los YAML nuevos se
ejecutan por lotes. Los YAML originales con campos españoles se conservan para
compatibilidad, con `_` como blanco; los nuevos usan el formato `mt:` y `B`.

## Diseño y demostración

- [Lectura y visualización](docs/lectura_visualizacion.md).
- [Motor y reconocedora](docs/reconocedora.md).
- [MT alteradora](docs/alteradora.md).
- [Casos esperados de la reconocedora](ejemplos/reconocedora.json).
- [Casos esperados de la alteradora](ejemplos/alteradora.json).
- [Trazas guardadas](ejemplos/trazas/).

La reconocedora acepta `111#010` y `1111#1010`, y rechaza `111#01` y `11#010`.
La alteradora produce `10100 → 10101`, `10111 → 11000`, `00000 → 00001` y
`11111 → 100000`. Todas las entradas tienen longitud mínima de cinco.

Desde la raíz se ejecutan las pruebas con:

```bash
.venv/bin/python -m unittest discover -s Proyecto3TC/pruebas -t Proyecto3TC -v
```
