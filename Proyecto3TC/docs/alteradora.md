# MT alteradora: incremento binario

## Propósito y contrato

La máquina transforma una cadena binaria no vacía en su sucesor numérico:

```text
f(w) = representación binaria de (valor_binario(w) + 1), con ancho mínimo |w|.
Dominio: {0,1}+.
```

Por ejemplo, `00000` produce `00001`: se conservan los ceros iniciales que no
cambian por la suma. Si todos los bits son unos, la salida crece una celda:
`11111` produce `100000`. No se impone un ancho máximo.
La entrada vacía se rechaza y los símbolos fuera de `{0,1}` se rechazan antes
de efectuar transiciones. Un límite de pasos puede interrumpir la ejecución.

Es una MT alteradora porque **su resultado es el contenido modificado de la
cinta**, además de alcanzar un estado de aceptación. Usa el mismo motor de una
cinta que la reconocedora, sin realizar la suma mediante código Python.
El YAML está en [alteradora.yaml](../maquinas/alteradora.yaml).

## Definición formal

Se utiliza la variante `M = (Q, Σ, Γ, δ, q₀, B, Fₐ, Fᵣ)` con:

- `Q = {q_inicio, q_derecha, q_sumar, q_aceptar, q_rechazar}`.
- `Σ = {0,1}` y `Γ = {0,1,B}`.
- `q₀ = q_inicio` y el símbolo blanco es `B`.
- `Fₐ = {q_aceptar}` y `Fᵣ = {q_rechazar}`.
- `δ: (Q − (Fₐ ∪ Fᵣ)) × Γ → Q × Γ × {L,R,S}`, definida por las reglas siguientes.

El cabezal empieza en la posición 0 y la entrada ocupa las posiciones `0..n−1`.
La cinta se extiende en ambas direcciones. Primero se escribe el símbolo,
después se mueve y se cambia de estado.

| Origen | Lee | Siguiente | Escribe | Mueve |
| --- | --- | --- | --- | --- |
| `q_inicio` | `0` | `q_derecha` | `0` | R |
| `q_inicio` | `1` | `q_derecha` | `1` | R |
| `q_inicio` | `B` | `q_rechazar` | `B` | S |
| `q_derecha` | `0` | `q_derecha` | `0` | R |
| `q_derecha` | `1` | `q_derecha` | `1` | R |
| `q_derecha` | `B` | `q_sumar` | `B` | L |
| `q_sumar` | `1` | `q_sumar` | `0` | L |
| `q_sumar` | `0` | `q_aceptar` | `1` | S |
| `q_sumar` | `B` | `q_aceptar` | `1` | S |

Los estados terminales no tienen salidas. Las reglas ausentes significan rechazo.

## Algoritmo, corrección y terminación

1. `q_inicio` exige al menos un bit y avanza a la derecha.
2. `q_derecha` recorre los bits sin cambiarlos. Al encontrar el primer blanco,
   retrocede al bit menos significativo y pasa a `q_sumar`.
3. `q_sumar` transporta un acarreo igual a uno. Cada `1` se vuelve `0` y el
   cabezal retrocede. El primer `0` se vuelve `1` y se acepta. Si se llega al
   blanco izquierdo, se escribe `1` y se acepta.

Durante el recorrido derecho la entrada se conserva. Durante la suma, los bits
ya visitados son exactamente un sufijo de unos originales convertido a ceros,
y el acarreo sigue pendiente a su izquierda. Cambiar el primer cero por uno
resuelve el acarreo y deja intacto el prefijo restante. Si no existe ese cero,
el uno escrito a la izquierda representa el nuevo bit más significativo. Estas
son las reglas de la suma binaria de uno, así que la cinta final representa
`valor(w) + 1` y conserva al menos el ancho original.

El recorrido derecho avanza hasta el blanco en una entrada finita. El acarreo
solo retrocede y termina ante un cero o el blanco izquierdo. La máquina termina
para toda entrada válida, si el límite permite completar sus pasos.
Para longitud `n >= 1`, el peor caso son **2n + 2 transiciones**: `n` para recorrer
los bits, una para regresar desde el blanco, `n` para propagar el acarreo y una
para escribir el nuevo uno. Tiempo `O(n)` y espacio de cinta `O(n)`, con a lo sumo
`n+1` celdas no blancas. Las copias de configuraciones del simulador requieren
memoria adicional `O(n²)` en esta máquina.

## Cuatro cadenas de prueba

| Entrada | Longitud | Valor inicial | Salida | Valor final | Pasos | Cabezal final |
| --- | --- | --- | --- | --- | --- | --- |
| `10100` | 5 | 20 | `10101` | 21 | 7 | 4 |
| `10111` | 5 | 23 | `11000` | 24 | 10 | 1 |
| `00000` | 5 | 0 | `00001` | 1 | 7 | 4 |
| `11111` | 5 | 31 | `100000` | 32 | 12 | -1 |

Las cuatro se aceptan. Se eligieron para cubrir ausencia de acarreo, varios
acarreos, ceros iniciales y expansión por acarreo final. Están registradas en
[ejemplos/alteradora.json](../ejemplos/alteradora.json) y las pruebas verifican su
longitud, salida y número de pasos. Además se comparan los 510 binarios de
longitud 1 a 8 con `format(int(entrada, 2) + 1, 'b').zfill(len(entrada))`, usado
solo como oráculo de prueba independiente de las transiciones.

## Traza completa de `11111`

Esta tabla muestra cada transición, sin agrupar movimientos. El contenido
omite blancos exteriores; la posición del cabezal puede estar fuera de él.

| Paso | Estado después del paso | Cabezal | Lee / escribe / mueve | Contenido |
| --- | --- | --- | --- | --- |
| 0 | `q_inicio` | 0 | Configuración inicial | `11111` |
| 1 | `q_derecha` | 1 | `1 / 1 / R` | `11111` |
| 2 | `q_derecha` | 2 | `1 / 1 / R` | `11111` |
| 3 | `q_derecha` | 3 | `1 / 1 / R` | `11111` |
| 4 | `q_derecha` | 4 | `1 / 1 / R` | `11111` |
| 5 | `q_derecha` | 5 | `1 / 1 / R` | `11111` |
| 6 | `q_sumar` | 4 | `B / B / L` | `11111` |
| 7 | `q_sumar` | 3 | `1 / 0 / L` | `11110` |
| 8 | `q_sumar` | 2 | `1 / 0 / L` | `11100` |
| 9 | `q_sumar` | 1 | `1 / 0 / L` | `11000` |
| 10 | `q_sumar` | 0 | `1 / 0 / L` | `10000` |
| 11 | `q_sumar` | -1 | `1 / 0 / L` | `00000` |
| 12 | `q_aceptar` | -1 | `B / 1 / S` | `100000` |

La salida ocupa las posiciones `-1..4`. El cabezal termina sobre el bit donde
se resolvió el acarreo; no se reposiciona automáticamente al comienzo.

## Cómo ejecutar esta parte

Las cuatro cadenas están dentro de `mt.inputs`. El archivo anterior
`alteradora_incremento.yaml` se conserva con el formato español y `_` como
blanco; la definición principal utiliza `B`, igual que el documento.

Sigue la instalación del [README de la raíz](../../README.md). Desde esa raíz:

```bash
.venv/bin/python Proyecto3TC/simulador.py --maquina alteradora --validar
.venv/bin/python ejecutar.py alteradora
.venv/bin/python Proyecto3TC/simulador.py --maquina alteradora "11111"
.venv/bin/python -m unittest discover -s Proyecto3TC/pruebas -t Proyecto3TC -v
```

En Windows / PowerShell sustituye `.venv/bin/python` por
`.\.venv\Scripts\python.exe`. Sin cadena, se ejecutan las cuatro entradas YAML.
Para abrir el menú usa `--interactivo`; para ocultar pasos, `--solo-resumen`;
para configurar el límite por cadena, `--max-pasos`.
