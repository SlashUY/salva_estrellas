```
 ____  ____  _      __   ____  _   _         _   _  _  _
/ ___\/ ___\| |    / _| / ___\| |_| |       | | | || || |
\___ \\___ \| |   | |_  \___ \| __| |  ___  | | | || || |
 ___) )___) | |___|  _|  ___) | |_| | |___| | |_| || || |
\____/\____/ \____/|_|  \____/ \__|_|        \___/ |_||_|
```

# Salva Estrellas

Recreación del icónico salvapantallas de Windows 3.1 — el viaje estelar que hipnotizó a toda una generación.  
Desarrollado en Python con tkinter, con algunos toques propios: cursor alien personalizado, firma interactiva y panel de configuración en tiempo real.

---

## ¿Qué hace?

Simula un vuelo a través del espacio usando proyección 3D clásica: 300 estrellas nacen en el centro de la pantalla y se acercan hacia el espectador, acelerando y creciendo a medida que se aproximan.

Características:
- **Proyección 3D** fiel al salvapantallas original de Windows 3.1
- **Cursor alien** personalizado en verde neón (extraído de imagen pixel art)
- **Firma interactiva** `SSLASH_UY` en la esquina inferior izquierda — late entre amarillo y verde neón al pasar el cursor, y abre el perfil de GitHub al hacer clic
- **Panel de configuración** en tiempo real (tecla `T`): cantidad de estrellas, velocidad y FPS
- **Pantalla completa** automática al iniciar

---

## Requisitos

- Python 3.8 o superior
- Pillow (`pip install pillow`)

---

## Cómo usar

**Opción 1 — Lanzador silencioso (recomendado en Windows):**
```
Doble clic en iniciar.vbs
```
Ejecuta el programa sin abrir ninguna ventana de consola.

**Opción 2 — Directo:**
```bash
python salva_estrellas.py
```

---

## Controles

| Tecla / Acción | Función |
|---|---|
| `T` | Abrir panel de configuración |
| `ESC` o `SPACE` | Salir |
| Clic en pantalla | Salir |
| Clic en `SSLASH_UY` | Abrir GitHub |

### Panel de configuración

| Parámetro | Rango | Por defecto |
|---|---|---|
| Estrellas | 1 – 1000 | 300 |
| Velocidad | 1 – 20 | 4 |
| FPS | 10 – 120 | 60 |

---

## Archivos

| Archivo | Descripción |
|---|---|
| `salva_estrellas.py` | Programa principal |
| `iniciar.vbs` | Lanzador silencioso para Windows |
| `puntero.JPG` | Imagen base del cursor alien |

---

## Autor

**SSLASH_UY** — [github.com/SlashUY](https://github.com/SlashUY)
