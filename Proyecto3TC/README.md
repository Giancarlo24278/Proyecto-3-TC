# Simulador de máquinas de Turing

Motor de una sola cinta y reconocedora de paquetes `cantidad#datos`: la cantidad
se escribe con unos y debe coincidir con el número de bits después de `#`.
Por ejemplo, `111#010` se acepta y `111#01` se rechaza.

## Instalar y ejecutar

Requiere Python 3.10 o superior. Desde PowerShell, en la carpeta del proyecto:

```powershell
python -m venv .venv
$env:PYYAML_FORCE_LIBYAML = '0'
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Remove-Item Env:PYYAML_FORCE_LIBYAML
.\.venv\Scripts\python.exe simulador.py
```

Si ya tienes el entorno preparado, ejecuta solo el último comando.
Elige **1** para evaluar un paquete y **0** para salir. También puedes escribir
`salir` al ingresar un paquete o presionar `Ctrl+C` para terminar.
Se muestran el resultado, los pasos ejecutados, el estado y la cinta final.
Las marcas `X` e `Y` indican unos y bits ya emparejados.

Para evaluar una sola cadena:

```powershell
.\.venv\Scripts\python.exe simulador.py "111#010"
```

## Pruebas y documentación

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s pruebas -v
```

El diseño del motor y el contrato de integración están en
[docs/reconocedora.md](docs/reconocedora.md). La definición de la MT está en
[maquinas/reconocedora_paquetes.yaml](maquinas/reconocedora_paquetes.yaml) y los
cuatro ejemplos en [ejemplos/reconocedora.json](ejemplos/reconocedora.json).
