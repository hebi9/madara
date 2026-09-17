Madara – Documento de requerimientos del proyecto
Objetivo

Desarrollar un software nativo para Windows, completamente offline, que permita diseñar, editar y reproducir contenido multimedia sobre múltiples pantallas físicas o LED walls mediante un sistema de espacios virtuales independientes del hardware disponible.

El proyecto debe permitir preparar un evento desde cualquier computadora (incluso con un solo monitor) y posteriormente asignar los espacios virtuales a las pantallas físicas disponibles durante el montaje del evento.

Requerimientos funcionales
1. Espacios virtuales

Los espacios virtuales representan superficies lógicas de trabajo.

Cada espacio debe tener:

Nombre.

Resolución lógica (ancho y alto).

Posición dentro del workspace.

Monitor físico asignado (opcional).

Ejemplo:

Espacio

	

Resolución




Escenario Izquierdo

	

1920×1080




Escenario Derecho

	

1920×1080




Fondo LED

	

8000×2000

Los espacios virtuales deben poder:

crearse;

renombrarse;

cambiar resolución;

reordenarse;

moverse libremente durante la configuración;

asignarse posteriormente a monitores físicos.

La posición del espacio nunca debe depender del monitor físico.

2. Detección de monitores físicos

El programa debe detectar automáticamente los monitores conectados mediante Qt.

Debe mostrar:

nombre del monitor;

resolución;

cuál es el principal;

posición real según Windows.

Debe permitir:

elegir qué monitores utilizar;

reacomodarlos visualmente;

guardar esa configuración global.

Esta configuración es independiente de cualquier proyecto.

3. Relación Espacio Virtual ↔ Monitor

Durante el montaje del evento:

un espacio virtual puede asignarse a un monitor disponible;

la asignación puede cambiar sin modificar el proyecto.

Cuando cambie la asignación:

todo el contenido debe escalar proporcionalmente;

deben conservarse las posiciones relativas;

deben respetarse las relaciones entre múltiples espacios.

Ejemplo:

Proyecto:

Espacio de 1920×1080.

Evento:

Monitor LED 7680×4320.

Una imagen ubicada al 10% del ancho deberá seguir apareciendo al 10% del ancho.

4. Escenas

Las escenas representan estados completos del contenido.

Cada escena contiene múltiples fuentes.

Las escenas deben ser independientes de los espacios virtuales.

Una misma escena puede abarcar varios espacios simultáneamente.

Debe existir:

escena activa por cada espacio virtual durante reproducción;

última escena utilizada por cada espacio;

cambio instantáneo de escena.

5. Fuentes

Cada escena puede contener múltiples fuentes.

Tipos iniciales:

Imagen

Texto

Tipos futuros:

Video

GIF

Cámara

Captura de pantalla

Navegador

PDF

Audio

Color sólido

Temporizador

Reloj

Cada fuente debe almacenar:

nombre;

tipo;

posición absoluta;

tamaño;

rotación (futuro);

capa (Z-index);

visibilidad;

bloqueo;

opacidad (futuro).

6. Editor visual

El editor debe funcionar sobre un único workspace lógico.

Características:

mover fuentes libremente;

seleccionar múltiples;

redimensionar mediante handles;

editar texto en tiempo real;

cambiar tamaño de fuente;

cambiar color;

cambiar imagen desde propiedades;

mantener selección tras modificar.

Inspiración:

OBS Studio

Photoshop

Resolume Arena

7. Clipping entre espacios virtuales

Una fuente puede cruzar varios espacios virtuales.

Debe existir una única instancia de la fuente.

El sistema debe mostrar únicamente la parte correspondiente dentro de cada espacio.

Ejemplo:

El espacio entre ambos no debe afectar el contenido.

8. Reproducción

Al presionar Play:

abrir una ventana sin bordes por monitor asignado;

ocupar toda la pantalla;

permanecer siempre encima;

mostrar el contenido correspondiente;

sincronizar todas las ventanas.

Al detener:

cerrar todas las ventanas.

9. Edición durante reproducción

La reproducción nunca debe editar directamente la escena visible.

Debe existir separación entre:

escena editándose;

escena reproduciéndose.

Posteriormente podrá implementarse:

Actualizar salida.

Transiciones.

10. Panel de propiedades

El panel derecho debe adaptarse según la selección.

Espacio Virtual

nombre;

resolución;

monitor asignado.

Escena

nombre;

estado activo.

Imagen

archivo;

posición;

tamaño.

Texto

contenido;

tamaño;

color;

fuente tipográfica.

11. Paneles inferiores

Tres listas independientes.

Espacios Virtuales

crear;

eliminar;

seleccionar.

Escenas

crear;

eliminar;

seleccionar.

Fuentes

crear;

eliminar;

seleccionar.

Al cambiar de espacio debe mantenerse su última escena activa.

Al cambiar de escena debe mantenerse su última fuente seleccionada.

Requerimientos de persistencia
Configuración global

Guardar:

monitores activos;

posiciones físicas;

asignaciones recientes.

Archivo:

monitor_config.json

Nunca debe sobrescribirse con proyectos.

Proyectos (futuro)

Cada proyecto debe contener:

espacios virtuales;

escenas;

fuentes;

propiedades;

recursos utilizados;

asignaciones opcionales.

Formato propuesto:

*.madara

Ejemplo:

Proyecto.madara
├── project.json
├── assets/
│   ├── logo.png
│   ├── intro.mp4
│   └── fondo.jpg
Requerimientos de interfaz
Sidebar

colapsable;

Play / Stop;

Configuración.

Barra superior

Añadir Imagen;

Añadir Texto;

Eliminar.

Área central

Workspace visual.

Panel derecho

Propiedades dinámicas.

Panel inferior

Espacios;

Escenas;

Fuentes.

Requerimientos técnicos
Lenguaje

Python.

Framework principal

PySide6.

Motor gráfico

QGraphicsView + QGraphicsScene.

Multimedia

Qt Multimedia.

Plataforma inicial

Windows.

Funcionamiento

100% offline.

Sin dependencias de Internet.

Requerimientos de rendimiento

Debe ser capaz de:

múltiples monitores;

resoluciones muy altas;

movimiento fluido;

reproducción sincronizada;

miles de fuentes por escena;

edición en tiempo real.

El render debe escalar hacia resoluciones LED sin perder proporciones.

Arquitectura prevista
Madara
│
├── Configuración Global
│     ├── Monitores físicos
│     └── Preferencias
│
├── Proyecto
│     ├── Espacios Virtuales
│     ├── Escenas
│     └── Recursos
│
├── Editor
│     ├── Workspace
│     ├── Fuentes
│     └── Propiedades
│
├── Playback
│     ├── Ventana por monitor
│     └── Sincronización
│
└── Assets
      ├── Imágenes
      ├── Videos
      ├── Audio
      └── Documentos
Roadmap de desarrollo
Fase 1 — Infraestructura (en progreso)
Detección de monitores.
Configuración de monitores.
Persistencia de configuración global.
Espacios virtuales.
Editor visual.
Reproducción básica.
Clipping perfecto entre espacios.
Handles tipo OBS.
Fase 2 — Edición profesional
Rotación.
Snap magnético.
Guías inteligentes.
Bloqueo de fuentes.
Agrupar fuentes.
Capas.
Fase 3 — Escenas avanzadas
Transiciones.
Escena previa/programa.
Editor sin afectar salida.
Temporización automática.
Fase 4 — Recursos multimedia
Video.
GIF.
Audio.
Cámara.
Navegador.
Fase 5 — Eventos masivos
Escalado lógico→físico.
Mapeo LED.
Sincronización de múltiples salidas.
Perfiles de venue.
Exportación/importación de proyectos.
Filosofía del proyecto

Madara debe comportarse como una combinación entre OBS Studio y Resolume Arena: un editor visual intuitivo para construir escenas con múltiples fuentes, combinado con un sistema de espacios virtuales independientes del hardware que permita diseñar un espectáculo completo desde cualquier computadora y desplegarlo posteriormente en configuraciones de pantallas completamente distintas sin tener que reconstruir el contenido.