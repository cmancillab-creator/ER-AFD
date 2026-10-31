# ER-AFD — Convertidor de expresiones regulares a AFD

Proyecto académico de Teoría de Autómatas. Python 3.9+ / Linux 64-bit / sin dependencias externas.

## Uso

```sh
make config
make build
make test
./er-afd '(a|b)*abb' 'aabb'
./er-afd '[a-z]\N' 'g7'
make run ER='(a|b)*abb' CADENA='aabb'
make clean
```

**Importante:** `./er-afd` devuelve 1 cuando acepta, 0 cuando rechaza y 2 si la sintaxis/los argumentos son incorrectos, tal y como pide la guía. `make run` transforma la aceptación en salida exitosa para `make`.

## Estructura

- `src/automata.py`: tokenizador, parser, Thompson, subconjuntos, simulación.
- `src/main.py`: interfaz de consola.
- `er-afd`: lanzador ejecutable.
- `tests/test_automata.py`: pruebas unitarias.
- `doc/Reporte técnico.pdf`: explicación algorítmica.
- `doc/Manual de usuario.pdf`: instalación y uso.
- `doc/Casos de prueba.pdf`: capturas reales de ejecución.

En `doc/` también están las versiones editables `.docx` de los tres documentos.

En Windows (PowerShell), para probar sin Makefile:

```powershell
py -m unittest discover -s tests -v
py src/main.py "(a|b)*abb" "aabb"
py src/main.py "(a|b)*abb" "aaba"
```

## Alcance

Operadores `|`, `*`, concatenación implícita, paréntesis, `.`, `ε`, conjuntos `[]`, rangos, negación `[^]`, escapes normales y `\N`, `\hHH`, `\A`, `\a`, `\z`. Universo ASCII 0–127. Un AFD con transiciones ausentes rechaza de inmediato; no se imprime estado sumidero explícito.

## Defensa sugerida (10 minutos)

0–2: correr un caso aceptado y otro rechazado. 2–5: explicar en la tabla el AFND, la clausura ε y los subconjuntos del AFD. 5–7: `make test` y cobertura de casos. 7–10: contestar preguntas sobre precedencia, epsilon y transiciones solapadas.

## Repositorio

Publicar el contenido de esta carpeta en un repositorio de GitHub o GitLab y entregar el enlace. El ZIP no crea ni publica el repositorio automáticamente.
