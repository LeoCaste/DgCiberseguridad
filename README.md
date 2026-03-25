# Diagnóstico de Ciberseguridad - Extractor de Funciones en GitHub

Este repositorio contiene mi solución para la prueba de diagnóstico. El sistema identifica en tiempo real las palabras más usadas en los nombres de funciones de repositorios populares (Python y Java) alojados en GitHub.

## Decisiones de Diseño y Arquitectura

Para cumplir con el requisito de mantener un flujo continuo de datos y separar responsabilidades, implementé el patrón **Productor-Consumidor** usando Docker. El sistema se divide en tres contenedores independientes:

1. **Miner (El Productor):** Escrito en Python. Se conecta a la API de GitHub, filtra por lenguaje (python o java) y popularidad, y analiza el código fuente. 
   - Para Python, usa la librería nativa `ast` para leer el árbol de sintaxis y encontrar las funciones con precisión. 
   - Para Java, utiliza expresiones regulares. 
   - Limpia los nombres (rompiendo formatos como `camelCase` o `snake_case`) y, en lugar de guardarlos localmente, los empuja inmediatamente a la base de datos.

2. **Redis (El Intermediario):** Elegí Redis por su velocidad trabajando en memoria. Actúa como el puente entre el miner y el visualizer. Utiliza una estructura de datos nativa llamada *Sorted Set* que suma los contadores de palabras y mantiene el ranking ordenado automáticamente. Esto evita cuellos de botella.

3. **Visualizer (El Consumidor):** Una interfaz web ligera construida con Streamlit (Python). Opera en tiempo real haciendo *polling* a Redis para leer el ranking. Al estar totalmente desacoplado del Miner, el usuario puede cambiar los parámetros (como el Top-N o el filtro por lenguaje) sin interrumpir la extracción de datos.

## Requisitos de la herramienta

- Docker y Docker Compose instalados.

## Cómo ejecutar el proyecto

Para ser de facil montaje, todo el sistema está orquestado. Solo se necesita clonar el repositorio y correr un comando:

```bash
# 1. Clonar el repositorio
git clone <https://github.com/LeoCaste/DgCiberseguridad>
cd DgCiberseguridad

# 2. Levantar la infraestructura
docker compose up --build