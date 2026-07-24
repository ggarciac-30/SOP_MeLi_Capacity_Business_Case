# Caso S&OP — Mercado Envíos — Dashboard Ejecutivo

Sitio estático (HTML/CSS/JS puro, sin frameworks) para presentar el caso de capacidad y
staffing del FC MXXX1. Pensado para editarse fácilmente aunque regreses en 6 meses.

## Estructura

```
/
├── index.html          <- estructura y contenido (texto, KPIs, tablas)
├── css/
│   └── styles.css      <- todos los estilos, variables al inicio del archivo
├── js/
│   └── script.js       <- carga de datos + navegacion + espacio para tus graficas
├── images/              <- pon aqui tus capturas de Power BI / exports de Python
├── data/
│   └── resultados.json <- TODOS los numeros y textos del sitio viven aqui
└── README.md
```

## ¿Dónde edito qué?

| Quiero cambiar... | Edito este archivo |
|---|---|
| Un KPI, hallazgo, conclusión o recomendación | `data/resultados.json` |
| El texto de "Objetivo" o "Dataset" | `index.html` (busca `<!-- ===== SECCION: ... -->`) |
| Colores, tipografía, espaciados | `css/styles.css`, bloque `:root` al inicio |
| Agregar una gráfica real (Chart.js/Plotly) | `js/script.js`, dentro de `inicializarGraficos()` |
| Agregar una sección nueva al menú | Ver instrucciones abajo |

## Cómo agregar una gráfica real

El sitio trae **contenedores vacíos** listos para dos librerías, con el código de ejemplo
comentado directamente en `js/script.js` dentro de la función `inicializarGraficos()`:

- **Chart.js** — contenedor `<canvas id="graficoCapacidad">`
- **Plotly** — contenedor `<div id="graficoProyeccion">`

Pasos:
1. Agrega el `<script>` de la librería que quieras usar en el `<head>` de `index.html`
   (las URLs exactas están comentadas en `script.js`).
2. Descomenta el bloque de ejemplo correspondiente en `inicializarGraficos()`.
3. Reemplaza los arrays de ejemplo (`labels`, `data`, `x`, `y`) con tus valores reales,
   exportados desde tu notebook de Python.

Si prefieres no usar librerías interactivas, exporta tu gráfica de Python como imagen
(`plt.savefig('images/tu_grafica.png')`) y reemplaza el `<canvas>`/`<div>` en `index.html`
por un `<img src="images/tu_grafica.png">`.

## Cómo agregar una sección nueva al menú

1. En `index.html`, dentro de `<nav class="sidebar-nav">`, copia un `<a>` existente y
   cambia el texto y el `href="#tu-id"` / `data-section="tu-id"`.
2. Copia un bloque `<section class="page-section" id="tu-id">...</section>` y cambia
   su `id` para que coincida exactamente con el que pusiste en el link.
3. No necesitas tocar `script.js` para esto — la navegación detecta automáticamente
   cualquier `.page-section` que exista en la página.

## Cómo publicar en GitHub Pages

```bash
git add .
git commit -m "Dashboard caso S&OP Mercado Envios"
git push origin main
```
Luego: `Settings → Pages → Source: main / (root)`.

## Antes de publicar

- Completa los 2 links del footer (`href="#"`) con tu repositorio real y tu LinkedIn.
- Revisa `data/resultados.json` y ajusta cualquier cifra si tu análisis cambió.
- Si agregaste gráficas, prueba abriendo `index.html` directamente en el navegador antes
  de subirlo (algunos navegadores bloquean `fetch()` en archivos locales — si el JSON no
  carga, prueba con un servidor local simple: `python -m http.server` en la carpeta del
  proyecto y abre `http://localhost:8000`).
