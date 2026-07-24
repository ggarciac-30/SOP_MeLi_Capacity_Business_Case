/* ================================================================
   SCRIPT PRINCIPAL — Caso S&OP Mercado Envios
   ================================================================
   Este archivo hace 3 cosas:
   1. Carga los datos desde data/resultados.json
   2. Inyecta esos datos en el HTML (Análisis, Conclusiones, Recomendaciones)
   3. Controla el menu lateral (resaltar seccion activa + boton movil)
   4. Muestra el aviso de "rota tu dispositivo" en movil

   Si quieres AGREGAR una pregunta nueva al Análisis, NO necesitas
   tocar este archivo -- edita data/resultados.json. Este script solo
   lee ese archivo y arma las tarjetas automaticamente.
   ================================================================ */


/* ----------------------------------------------------------------
   1. CARGA DE DATOS
   ---------------------------------------------------------------- */

// fetch() lee el archivo JSON. Si cambias el nombre o la ubicacion
// de data/resultados.json, actualiza esta ruta tambien.
fetch('data/resultados.json')
  .then(function (respuesta) {
    return respuesta.json();
  })
  .then(function (datos) {
    // Una vez que los datos llegan, llenamos cada seccion.
    // Si agregas una nueva seccion que necesite datos, agrega aqui
    // tu propia funcion "renderX(datos)" siguiendo el mismo patron.
    renderAnalisis(datos.analisis);
    renderListaSimple('conclusionesContainer', datos.conclusiones);
    renderListaSimple('recomendacionesContainer', datos.recomendaciones);
  })
  .catch(function (error) {
    console.error('No se pudo cargar data/resultados.json:', error);
  });


/* ----------------------------------------------------------------
   2. FUNCIONES QUE INYECTAN DATOS EN EL HTML
   ---------------------------------------------------------------- */

/* Dibuja las 8 (o las que sean) tarjetas de pregunta/respuesta dentro
   de <div id="analisisContainer">.

   Cada pregunta puede tener estos campos (ver data/resultados.json):
     - numero      (obligatorio) el numero de la pregunta
     - pregunta    (obligatorio) el texto de la pregunta
     - respuesta   (obligatorio) el texto de la respuesta
     - kpis        (opcional) array de numeros destacados: [{valor, etiqueta, tipo}]
     - imagen      (opcional) ruta a una imagen (grafica exportada de Python)
     - tabla       (opcional) {titulo, encabezados: [...], filas: [[...]]}
     - nota        (opcional) un texto destacado al final (supuesto o recomendacion)

   No necesitas usar todos los campos en cada pregunta -- la funcion
   solo dibuja lo que exista. Por eso puedes duplicar cualquier
   pregunta de resultados.json como plantilla y borrar lo que no uses. */
function renderAnalisis(preguntas) {
  var contenedor = document.getElementById('analisisContainer');
  if (!contenedor || !preguntas) return;

  preguntas.forEach(function (item) {
    var tarjeta = document.createElement('div');
    tarjeta.className = 'analisis-card';

    // --- Encabezado: numero + pregunta ---
    var html = '<div class="analisis-header">' +
      '<span class="analisis-numero">' + item.numero + '</span>' +
      '<h3>' + item.pregunta + '</h3>' +
      '</div>';

    // --- KPIs (opcional): fila de numeros destacados ---
    if (item.kpis && item.kpis.length > 0) {
      html += '<div class="kpi-grid kpi-grid-compacta">';
      item.kpis.forEach(function (kpi) {
        var esAlerta = kpi.tipo === 'alerta';
        html += '<div class="kpi-card' + (esAlerta ? ' alerta' : '') + '">' +
          '<span class="kpi-valor">' + kpi.valor + '</span>' +
          '<span class="kpi-etiqueta">' + kpi.etiqueta + '</span>' +
          '</div>';
      });
      html += '</div>';
    }

    // --- Imagen (opcional): grafica exportada de Python ---
    if (item.imagen) {
      html += '<img class="analisis-imagen" src="' + item.imagen + '" alt="' + item.pregunta + '" />';
    }

    // --- Texto de la respuesta ---
    html += '<p class="analisis-respuesta">' + item.respuesta + '</p>';

    // --- Tabla (opcional) ---
    if (item.tabla) {
      html += '<h4 class="analisis-tabla-titulo">' + item.tabla.titulo + '</h4>';
      html += '<table class="data-table">';
      html += '<thead><tr>' +
        item.tabla.encabezados.map(function (h) { return '<th>' + h + '</th>'; }).join('') +
        '</tr></thead>';
      html += '<tbody>' +
        item.tabla.filas.map(function (fila) {
          return '<tr>' + fila.map(function (celda) { return '<td>' + celda + '</td>'; }).join('') + '</tr>';
        }).join('') +
        '</tbody>';
      html += '</table>';
    }

    // --- Nota destacada (opcional): supuesto o recomendacion ---
    if (item.nota) {
      html += '<div class="analisis-nota">' + item.nota + '</div>';
    }

    tarjeta.innerHTML = html;
    contenedor.appendChild(tarjeta);
  });
}

// Dibuja una lista simple (usada en Conclusiones y Recomendaciones).
// Para usarla en otra lista, llama: renderListaSimple('idDelUL', datos.tu_array)
function renderListaSimple(idContenedor, items) {
  var contenedor = document.getElementById(idContenedor);
  if (!contenedor || !items) return;

  items.forEach(function (texto) {
    var li = document.createElement('li');
    li.textContent = texto;
    contenedor.appendChild(li);
  });
}


/* ----------------------------------------------------------------
   3. NAVEGACION DEL MENU LATERAL
   ---------------------------------------------------------------- */

// Boton hamburguesa: abre/cierra el sidebar en movil
var botonMenu = document.getElementById('menuToggle');
var sidebar = document.getElementById('sidebar');

if (botonMenu && sidebar) {
  botonMenu.addEventListener('click', function () {
    sidebar.classList.toggle('sidebar-abierto');
  });
}

// Resaltar el link del menu correspondiente a la seccion que se esta viendo.
// Usa IntersectionObserver: es la forma moderna y eficiente de detectar
// "que seccion esta visible en pantalla ahora mismo" sin escuchar el
// evento scroll manualmente.
var secciones = document.querySelectorAll('.page-section');
var linksDelMenu = document.querySelectorAll('.nav-link');

var observador = new IntersectionObserver(
  function (entradas) {
    entradas.forEach(function (entrada) {
      if (entrada.isIntersecting) {
        var idVisible = entrada.target.getAttribute('id');

        // Quita "active" de todos los links...
        linksDelMenu.forEach(function (link) {
          link.classList.remove('active');
        });
        // ...y se lo pone solo al link que corresponde a la seccion visible
        var linkActivo = document.querySelector('.nav-link[data-section="' + idVisible + '"]');
        if (linkActivo) {
          linkActivo.classList.add('active');
        }
      }
    });
  },
  { rootMargin: '-40% 0px -55% 0px' } // considera "visible" cuando la seccion esta cerca del centro de la pantalla
);

secciones.forEach(function (seccion) {
  observador.observe(seccion);
});

// En movil, cerrar el menu automaticamente despues de tocar un link
// (para que no se quede tapando el contenido)
linksDelMenu.forEach(function (link) {
  link.addEventListener('click', function () {
    if (sidebar) {
      sidebar.classList.remove('sidebar-abierto');
    }
  });
});


/* ----------------------------------------------------------------
   4. AVISO DE "ROTA TU DISPOSITIVO" EN MOVIL
   ----------------------------------------------------------------
   Esta funcion revisa el tamaño y la orientacion de la pantalla y
   muestra/oculta el overlay #rotate-message (definido en index.html
   y con su estilo en css/styles.css).

   Se ejecuta 3 veces:
   - Al cargar la pagina (checkOrientation() al final de este bloque)
   - Cada vez que cambia el tamaño de la ventana (evento "resize")
   - Cada vez que el celular gira fisicamente (evento "orientationchange")

   Para cambiar A PARTIR DE QUE ANCHO se considera "movil", edita
   el numero 900 de aqui abajo (esta en pixeles). */
function checkOrientation() {
  var esMovil = window.innerWidth <= 900;
  var esVertical = window.innerHeight > window.innerWidth;
  var overlay = document.getElementById('rotate-message');

  if (!overlay) return; // si el overlay no existe en el HTML, no hace nada

  if (esMovil && esVertical) {
    overlay.style.display = 'flex'; // muestra el aviso
  } else {
    overlay.style.display = 'none'; // lo oculta
  }
}

// Vuelve a revisar cada vez que cambia el tamaño de la ventana o la orientacion
window.addEventListener('resize', checkOrientation);
window.addEventListener('orientationchange', checkOrientation);

// Revisa una vez apenas carga la pagina, por si ya esta en movil+vertical
checkOrientation();
