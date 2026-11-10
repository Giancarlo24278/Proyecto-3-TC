# Motor y MT reconocedora de paquetes

## Alcance

Se implementó un motor genérico para máquinas de Turing deterministas de **una
sola cinta**, una MT reconocedora de paquetes y cuatro entradas de ejemplo.
`simulador.py` permite probar paquetes desde la terminal y muestra cada
transición y la cinta final; el README explica cómo ejecutarla. El lector general
`lector_yaml.py` valida las definiciones de ambas máquinas y `visualizacion.py`
dibuja las configuraciones. La integración se documenta en
[lectura_visualizacion.md](lectura_visualizacion.md).
El motor también puede ejecutar una MT alteradora: las
transiciones no contienen lógica específica de reconocimiento de paquetes.

## Modelo del motor

La cinta es un diccionario que relaciona posiciones enteras con símbolos. Las
posiciones no almacenadas contienen el blanco `_`. El cabezal empieza en la
posición 0, sobre el primer símbolo de la entrada; para la entrada vacía lee un
blanco. Puede moverse hacia índices negativos. Esto representa una sola cinta
ilimitada en ambas direcciones, sin reservar una cantidad fija de celdas.

Una transición se consulta mediante `(estado_actual, simbolo_leido)` y determina
el estado siguiente, el símbolo que se escribe y un movimiento: `L` (izquierda),
`R` (derecha) o `S` (permanecer). Primero se escribe, después se mueve el cabezal y
se actualiza el estado. Solo se aplica una regla por paso.

La ejecución se detiene al entrar en aceptación o rechazo. Una regla ausente
tiene significado de rechazo. Los símbolos de entrada ajenos al alfabeto se
rechazan antes de ejecutar transiciones. Un límite configurable de pasos evita
ejecuciones infinitas: `limite_alcanzado` es un resultado independiente y **no
demuestra rechazo**. El límite predeterminado es 10 000 transiciones.

Cada `Paso` conserva el número, la configuración anterior, el símbolo leído,
la transición aplicada y la configuración posterior. Las configuraciones son
instantáneas inmutables; las escrituras futuras no alteran el historial. El
resultado incluye la configuración inicial, la final, todos los pasos, el estado
de ejecución y el motivo de detención. Las ejecuciones de una misma definición
usan cintas independientes.

## Lenguaje reconocido

Se reconoce:

```text
L = { 1^n # w | n >= 1, w pertenece a {0,1}*, |w| = n }
```

La cantidad es una secuencia no vacía de unos. Se exige exactamente un `#`,
seguido por la misma cantidad de bits. Se adopta `n >= 1`: la cadena `#` se
rechaza porque no tiene cantidad escrita. No se permiten espacios, ceros en la
cantidad ni separadores adicionales.

El alfabeto de entrada es `{0,1,#}`. El de cinta es `{0,1,#,X,Y,_}`. `X` marca un
uno de la cantidad ya utilizado y `Y` un bit de datos ya emparejado. Las marcas
son internas: no se admiten en la entrada.

## Algoritmo de la reconocedora

1. Comprueba que la entrada comience con `1`, lo cambia por `X` y busca el `#`.
2. Después del separador, salta las marcas `Y` y marca el siguiente bit con `Y`.
   Si encuentra blanco en lugar de ese bit, rechaza: faltan datos.
3. Regresa al blanco situado a la izquierda de la entrada y avanza de nuevo.
4. Salta las `X`. Si encuentra otro `1` de la cantidad, lo marca y repite el
   emparejamiento. Si encuentra `#`, ya terminó la cantidad.
5. Recorre los datos: si solo quedan `Y` hasta el blanco, acepta. Si todavía hay
   un `0` o `1`, rechaza: sobran datos. Todo formato sin regla también rechaza.

| Estado | Función |
| --- | --- |
| `q_inicio` | Exigir al menos un uno y marcarlo. |
| `q_buscar_uno` | Encontrar el siguiente uno de la cantidad. |
| `q_buscar_separador` | Recorrer los unos restantes hasta `#`. |
| `q_buscar_bit` | Emparejar el uno marcado con un bit. |
| `q_regresar` | Regresar al extremo izquierdo. |
| `q_comprobar` | Verificar que no sobren bits. |
| `q_aceptar` | Terminar con aceptación. |
| `q_rechazar` | Terminar con rechazo. |

Después de cada regreso al inicio se han marcado exactamente tantos unos con
`X` como bits con `Y`. Por eso, al agotar la cantidad, la comprobación final
acepta si y solo si no quedan bits sin marcar. Cada vuelta consume un uno y un
bit; las búsquedas avanzan en una dirección hasta una marca, separador o blanco,
de modo que la reconocedora termina en entradas finitas, si el límite de pasos
permite completar el recorrido.

Para una entrada válida de longitud N, el tiempo es O(N²): hay O(N) vueltas de
O(N) movimientos. La cinta utilizada ocupa O(N). El historial del simulador usa
memoria adicional: guarda una copia de las celdas no blancas antes y después de
cada transición, con costo O(P·C) para P pasos y un máximo de C celdas no blancas.
Estos registros pertenecen al simulador y no constituyen cintas adicionales de
la MT.

## Ejemplos exigidos

| Entrada | Longitud | Resultado | Justificación |
| --- | --- | --- | --- |
| `111#010` | 7 | Aceptada | Tres unos y tres bits. |
| `1111#1010` | 9 | Aceptada | Cuatro unos y cuatro bits. |
| `111#01` | 6 | Rechazada | Falta un bit. |
| `11#010` | 6 | Rechazada | Sobra un bit. |

En `111#010`, los emparejamientos completos dejan sucesivamente `X11#Y10`,
`XX1#YY0` y `XXX#YYY`. Estas son vistas entre recorridos, no transiciones
individuales. La cinta final aceptada es `XXX#YYY`; conservar los bits originales
no es necesario para reconocer el lenguaje.

## Contrato de integración del lector YAML

El YAML usa listas de cadenas para estados y alfabetos. Los símbolos se deben
mantener como cadenas: por eso `'0'`, `'1'`, `'#'` y `'_'` aparecen entre comillas.
Cada elemento de `transiciones` tiene `origen`, `leer`, `siguiente`, `escribir` y
`mover`. La lista de reglas no tiene que cubrir todas las combinaciones: las
ausentes rechazan.

El lector general verifica la estructura del YAML, los campos y sus
tipos, y rechaza reglas duplicadas para un mismo par `(origen, leer)` **antes de
crear un diccionario**, porque un diccionario sobrescribiría la regla anterior.
El motor comprueba además invariantes de su definición: símbolos y estados
declarados, movimientos válidos y separación de estados de aceptación y rechazo.
Los estados terminales no llevan reglas de salida.

La integración habitual es `cargar_maquina(ruta)` de `lector_yaml.py`, que
entrega directamente una `MaquinaTuring` validada. Internamente se convierte
la lista YAML al contrato del motor de la siguiente forma:

```python
from motor import MaquinaTuring, Transicion

reglas = {
    (t["origen"], t["leer"]): Transicion(
        siguiente=t["siguiente"], escribir=t["escribir"], mover=t["mover"]
    )
    for t in datos["transiciones"]
}
maquina = MaquinaTuring(
    estados=datos["estados"],
    alfabeto_entrada=datos["alfabeto_entrada"],
    alfabeto_cinta=datos["alfabeto_cinta"],
    blanco=datos["blanco"],
    estado_inicial=datos["estado_inicial"],
    estados_aceptacion=datos["estados_aceptacion"],
    estados_rechazo=datos["estados_rechazo"],
    transiciones=reglas,
)
resultado = maquina.ejecutar("111#010", max_pasos=10_000)
```

Para una interfaz interactiva se usa `simulacion = maquina.iniciar(entrada)` y
se llama `simulacion.paso()` por cada avance. Devuelve un `Paso`, o `None` si no
hay transición aplicada. `simulacion.estado` informa si sigue en curso y
`simulacion.resultado()` entrega los datos acumulados. La interfaz debe imponer
su límite si solo usa `paso()`; también puede continuar con
`simulacion.ejecutar(max_pasos=...)`, cuyo límite incluye los pasos ya realizados.
Alcanzar el límite cierra esa simulación; para otro límite se inicia una nueva.

Para dibujar una configuración `c`, `c.celdas` entrega los pares `(índice,
símbolo)` no blancos, `c.cabezal` indica qué celda señalar y `c.estado` el estado
actual. `c.ventana(inicio, fin)` incluye blancos y posiciones negativas. La vista
debe incluir siempre el cabezal, incluso si está fuera del contenido escrito.
`resultado.final.contenido()` devuelve el texto entre las celdas no blancas
extremas y sirve para consultar la salida de una alteradora. Si el resultado es
`limite_alcanzado`, debe mostrarse como ejecución incompleta.

## Verificación

Las pruebas verifican los cuatro ejemplos y comparan todas las 3280 cadenas
de longitud 0 a 7 sobre `{0,1,#}` con un criterio independiente de formato y
longitud. También comprueban un paquete mayor, rechazo de símbolos externos,
cinta con índices negativos, borrado de celdas, movimientos, historial,
ejecución manual, aceptación, rechazo y límites de pasos. Las instrucciones para
correr estas pruebas están en el README.
