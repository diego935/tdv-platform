#  Memoria del Proyecto: Pill of Silence

## 1. Introducción

**Pill of Silence** es un videojuego de acción en 2D desarrollado como proyecto académico. En él, el jugador asume el papel de un soldado que es enviado a una ciudad plagada de mutantes. Su misión consiste en avanzar por diferentes zonas, enfrentarse a los enemigos que encuentra en su camino y descubrir qué ha sucedido en la ciudad.

El juego utiliza una **perspectiva lateral en dos dimensiones (2D)**, centrando la experiencia en la exploración, el combate y la interacción con los personajes que forman parte del entorno.

---

## 2. Jugabilidad

###  Objetivo del Juego
El jugador controla a un soldado enviado a una ciudad infestada de mutantes. Su objetivo es explorar los diferentes escenarios, sobrevivir a los ataques enemigos, interactuar con personajes y avanzar a través de los distintos niveles hasta completar la misión.

### Tabla de Controles

| Categoría | Acción | Tecla / Input |
| :--- | :--- | :--- |
| **Movimiento** | Moverse | `W` `A` `S` `D` / `Flechas de dirección` |
| | Correr | `Shift` |
| **Combate** | Apuntado | `Movimiento del Ratón` |
| | Disparar | `Clic Izquierdo` |
| | Zoom de Cámara | `Rueda del Ratón` (Scroll) |
| | Cambiar de Arma/Objeto rápido | Teclas `1` a `4` |
| **Inventario** | Abrir / Cerrar Inventario | `Tab` |
| | Mover objetos en inventario | `Clic Izquierdo` |
| | Usar objetos del inventario | `Doble Clic` |
| | Soltar objeto | `Q` |
| **Interacción**| Interactuar (Puertas, objetos y NPCs) | `E` |
| **Sistema** | Pausar juego | `Esc` |
| **Consola** | Abrir / Cerrar consola | `F1` |
| | Escribir comandos | `Teclado` |
| | Borrar texto en consola | `Backspace` |
| | Ejecutar comando en consola | `Enter` |

---

## Mecánicas Principales

* **Movimiento:** El personaje puede desplazarse libremente por el escenario utilizando el teclado. Además, dispone de una función de carrera que permite aumentar temporalmente la velocidad de movimiento para esquivar o avanzar rápido.
* **Sistema de Combate:** El jugador puede equipar diferentes armas y utilizarlas para eliminar a los mutantes. El apuntado se realiza de forma fluida mediante el ratón y el disparo con el clic izquierdo.
* **Inventario:** El juego incluye un sistema de gestión accesible mediante la tecla `Tab`. Desde este panel se pueden almacenar, mover y utilizar distintos objetos, tales como armas, munición o elementos de curación.
* **Curación:** El jugador puede recuperar puntos de vida mediante botiquines u otros objetos curativos disponibles estratégicamente durante la partida.
* **Interacción:** La tecla `E` permite interactuar de forma contextual con elementos del entorno, abriendo puertas, recogiendo objetos del suelo o entablando diálogos con personajes no jugables (NPCs).
* **Consola de Comandos:** El juego incorpora una consola accesible mediante `F1` orientada a la depuración, que permite introducir diferentes comandos en tiempo de ejecución.
* **Progresión:** La aventura se desarrolla a través de varios niveles conectados entre sí de forma lineal. El jugador debe avanzar por ellos completando objetivos específicos y limpiando las zonas de amenazas.

---

## 3. Desarrollo del Proyecto

Durante el desarrollo del proyecto se diseñaron e implementaron los diferentes escenarios, enemigos y personajes necesarios para crear la experiencia de juego. 

A nivel técnico, se desarrollaron e integraron con éxito los siguientes sistemas centrales:
1. Control de físicas y movimiento del jugador.
2. Sistema de combate y cajas de colisión (*hitboxes*).
3. Lógica de Inteligencia Artificial para el comportamiento de los mutantes.
4. Interfaz de usuario (UI) para el inventario, el menú y la consola de comandos.
5. Sistema de transición y progresión entre niveles.

Esta estructura modular permitió que todos los elementos artísticos y lógicos funcionaran de forma integrada y optimizada.

---

## 4. Conclusión

**Pill of Silence** es un videojuego de acción en 2D que combina exploración, combate e interacción con personajes para ofrecer una experiencia dinámica al jugador. 

Este proyecto ha permitido aplicar de forma práctica conocimientos avanzados relacionados con:
* La programación de videojuegos y arquitectura de software.
* El diseño de mecánicas de juego (*Game Design*).
* La organización y diseño de niveles (*Level Design*).

Como resultado, se ha logrado un producto de software de entretenimiento **funcional, completo y entretenido**, cumpliendo satisfactoriamente con los objetivos académicos planteados.
