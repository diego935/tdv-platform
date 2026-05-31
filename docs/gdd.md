# Documento de Diseño de Juego (GDD): Pill of Silence

---

## 1. Visión General y Core Loop
* **Nombre del Juego:** Pill of Silence
* **Género / Subtipo:** Shooter / Aventura 2D Lateral
* **Estética Visual:** Gráficos pixelados con una paleta de colores fría y apagada. El objetivo es transmitir un mundo oscuro, desolado y bajo una atmósfera de constante tensión y misterio.
* **Core Loop (Bucle de Juego):** Explorar entornos oscuros ➔ Rastrear huellas/Detectar amenazas ➔ Combatir (Disparar/Melee) ➔ Gestionar recursos e interactuar ➔ Avanzar de zona para la limpiar la ciudad.

---

## 2. Narrativa y Personajes

### 📜 Sinopsis de la Historia
Eres un soldado aparentemente como cualquier otro, uno más entre las filas. Se ha desatado el caos en la ciudad más cercana y las autoridades han tenido que evacuar a toda la población civil a gran velocidad. Sin previo aviso ni detalles sobre la raíz del problema, se te asigna una misión clandestina en solitario: *“Limpia la ciudad y vuelve entero”*. 

Los superiores insisten de manera sospechosa en una sola directriz: *“No te cuestiones nada, incluso demasiado”*. A medida que avanzas por los escenarios neutralizando todo lo que aún se mueve, la intriga te supera. Decides romper el silencio y descubrir la verdad de lo que realmente ocurrió por tu propia cuenta.

### 👥 Perfiles de Personajes (Planificación)
* **El Soldado (Jugador):** El protagonista. Un militar disciplinado que comienza acatando órdenes a ciegas pero cuya curiosidad lo lleva a investigar el trasfondo del desastre.
* **Los Altos Mandos:** Voces u órdenes en la sombra que guían al jugador de forma estricta, ocultando información crucial sobre el origen de la catástrofe.
* **NPCs:** Ciudadanos infectados que dan lugar a la constraposición del videojuego.

---

## 3. Mecánicas de Juego Propuestas (Gameplay)

### 3.1. Movimiento del Jugador
* **Caminar:** Movimiento lateral básico fluido en dos dimensiones.
* **Correr (`Shift`):** Mecánica para aumentar la velocidad temporalmente. Se planea para favorecer los momentos de huida o el posicionamiento táctico rápido cuando el jugador se vea acorralado.

### 3.2. Sistema de Combate y Armamento
* **Apuntado y Disparo:** El jugador usará el ratón para dirigir el punto de mira libremente en los 360 grados alrededor del personaje, disparando con el clic izquierdo.
* **Mecánica de Recarga:** Las armas de fuego tienen munición infinita, pero el jugador será obligado a buscar momentos seguros para recargar.
* **Ataque Melee (Cuerpo a Cuerpo):** Un ataque rápido de corto alcance.
* **Zoom de la Cámara:** Uso de la rueda del ratón para ampliar o reducir el campo de visión, permitiendo al jugador otear pasillos estrechos o anticipar peligros en espacios abiertos.

### 3.3. Sistema de Inventario e Interacción
* **Gestión de Objetos (`Tab`):** Pantalla donde el jugador podrá organizar visualmente sus recursos. Debe permitir almacenar diferentes armas (mapeadas del 1 al 4), munición y botiquines de curación.
* **Interacción (`E`) y Diálogos:** Un botón contextual para abrir puertas, recoger suministros del suelo y activar los cuadros de texto al hablar con los supervivientes (NPCs).

---

## 4. Comportamiento de los Enemigos (Implementación de IA)

Para evitar rutas fijas y aburridas, los enemigos mutantes reaccionarán de forma dinámica mediante estados básicos:
1. **Fase de Patrulla (Seguir Huellas):** Los enemigos deambulan por el mapa con libre albedrío.
2. **Fase de Alerta (Persecución):** Si el jugador entra en su rango de visión o cercanía, el enemigo abandonará su ruta fija para empezar a perseguir al soldado directamente.
3. **Fase de Ataque:** Al alcanzar la posición del jugador, el enemigo detendrá su carrera para ejecutar animaciones de daño cuerpo a cuerpo.

---

## 5. Diseño y Flujo de Escenarios (Planificación de Niveles)

El juego progresará de forma lineal a través de diferentes entornos que alterarán el ritmo y la dificultad del combate:

1. **Fase 1: Spawn (Claros Desiertos):** Espacios abiertos en las afueras. El mapa guiará al jugador invitándole a seguir las huellas en la tierra. Diseñado para familiarizarse con los controles básicos.
2. **Fase 2: La Carretera y Pasillos Estrechos:** Infraestructuras bloqueadas por la evacuación masiva. Alternará zonas anchas con laberintos de vehículos abandonados y pasillos muy estrechos para generar situaciones de encierro y agobio.
3. **Fase 3: El Trial (Ciudades Destruidas):** Entornos urbanos en ruinas y escombros. El jugador deberá superar un desafío o prueba de supervivencia para demostrar sus habilidades con el inventario y el combate.
4. **Fase 4: Puerta Final & Jefe (El Núcleo del Caos):**  Tras interactuar con la puerta final, el jugador se enfrentará a un jefe para terminar la limpieza y decidir el destino de su misión.

---

## 6. Herramientas de Testeo (Consola de Comandos)

Se proyecta la inclusión de una consola de desarrollo accesible mediante la tecla `F1` para facilitar las pruebas del equipo durante las fases de integración de código. Permitirá escribir comandos de texto básicos para realizar acciones como spawnear enemigos en un punto concreto.
