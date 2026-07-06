from flask import Flask, render_template, request, redirect, url_for
import plotly.graph_objects as go
import sqlite3
import os

app = Flask(__name__)

DB_PATH = 'simulador.db'


# =========================================================================
# INITIALIZACIÓN DE BASE DE DATOS (Persistencia Real para Render)
# =========================================================================
def init_db():
    """Crea la base de datos y la tabla si no existen al arrancar el servidor"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa TEXT NOT NULL,
                origen TEXT NOT NULL,
                destino TEXT NOT NULL,
                estrategia TEXT NOT NULL,
                compatibilidad INTEGER NOT NULL,
                tipo_estrategia TEXT NOT NULL
            )
        ''')
        # Insertar registros semilla de demostración solo si la tabla está completamente vacía
        cursor.execute("SELECT COUNT(*) FROM simulaciones")
        if cursor.fetchone()[0] == 0:
            semillas = [
                ("LONGCHA TEA", "China", "Ecuador", "Franquicias", 85, "Sin Participación Accionaria (Contratos)"),
                ("INCAFOODS", "Ecuador", "Estados Unidos", "Exportación Directa", 95,
                 "Sin Participación Accionaria (Contratos)"),
                ("EUROTECH", "Alemania", "México", "Empresas Conjuntas (Joint Ventures)", 60,
                 "Con Participación Accionaria (Propiedad)"),
                ("ANDINA LOGISTICS", "Ecuador", "España", "Alanzas con Participación (Subsidiaria Propia)", 45,
                 "Con Participación Accionaria (Propiedad)")
            ]
            cursor.executemany('''
                INSERT INTO simulaciones (empresa, origen, destino, estrategia, compatibilidad, tipo_estrategia)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', semillas)
        conn.commit()


# Ejecutar la inicialización
init_db()

# =========================================================================
# DICCIONARIO GEOGRÁFICO Y MACROECONÓMICO DE RESPALDO (20 Países del Aula)
# =========================================================================
COORDENADAS_PAISES = {
    "Ecuador": {"lat": -1.8312, "lon": -78.1834, "perfil_cultural": "relacional", "nivel_ip": "bajo"},
    "Luxemburgo": {"lat": 49.8153, "lon": 6.1296, "perfil_cultural": "transaccional", "nivel_ip": "alto"},
    "Marruecos": {"lat": 31.7917, "lon": -7.0926, "perfil_cultural": "relacional", "nivel_ip": "bajo"},
    "México": {"lat": 23.6345, "lon": -102.5528, "perfil_cultural": "relacional", "nivel_ip": "medio"},
    "Estados Unidos": {"lat": 37.0902, "lon": -95.7129, "perfil_cultural": "transaccional", "nivel_ip": "alto"},
    "Hungría": {"lat": 47.1625, "lon": 19.5033, "perfil_cultural": "transaccional", "nivel_ip": "medio"},
    "Japón": {"lat": 36.2048, "lon": 138.2529, "perfil_cultural": "relacional", "nivel_ip": "alto"},
    "Mónaco": {"lat": 43.7384, "lon": 7.4246, "perfil_cultural": "transaccional", "nivel_ip": "alto"},
    "Emiratos Árabes Unidos": {"lat": 23.4241, "lon": 53.8478, "perfil_cultural": "relacional", "nivel_ip": "medio"},
    "China": {"lat": 35.8617, "lon": 104.1954, "perfil_cultural": "relacional", "nivel_ip": "medio"},
    "Rusia": {"lat": 61.5240, "lon": 105.3188, "perfil_cultural": "relacional", "nivel_ip": "bajo"},
    "Nueva Zelanda": {"lat": -40.9006, "lon": 174.8860, "perfil_cultural": "transaccional", "nivel_ip": "alto"},
    "Suiza": {"lat": 46.8182, "lon": 8.2275, "perfil_cultural": "transaccional", "nivel_ip": "alto"},
    "Australia": {"lat": -25.2744, "lon": 133.7751, "perfil_cultural": "transaccional", "nivel_ip": "alto"},
    "Colombia": {"lat": 4.5709, "lon": -74.2973, "perfil_cultural": "relacional", "nivel_ip": "medio"},
    "Países Basos": {"lat": 52.1326, "lon": 5.2913, "perfil_cultural": "transaccional", "nivel_ip": "alto"},
    # REEMPLAZADO PERÚ
    "Argentina": {"lat": -38.4161, "lon": -63.6167, "perfil_cultural": "relacional", "nivel_ip": "bajo"},
    "Venezuela": {"lat": 6.4238, "lon": -66.5897, "perfil_cultural": "relacional", "nivel_ip": "bajo"},
    "Uruguay": {"lat": -32.5228, "lon": -55.7658, "perfil_cultural": "relacional", "nivel_ip": "medio"},
    "Brasil": {"lat": -14.2350, "lon": -51.9253, "perfil_cultural": "relacional", "nivel_ip": "medio"},
    "Alemania": {"lat": 51.1657, "lon": 10.4515, "perfil_cultural": "transaccional", "nivel_ip": "alto"},
    "España": {"lat": 40.4637, "lon": -3.7492, "perfil_cultural": "relacional", "nivel_ip": "alto"}
}

PAISES_MUNDIALES = sorted(list(COORDENADAS_PAISES.keys()))

ESTRATEGIAS_ECOTEC = {
    "exportacion_directa": {"nombre": "Exportación Directa", "tipo": "Sin Participación Accionaria (Contratos)"},
    "licencias": {"nombre": "Licencias", "tipo": "Sin Participación Accionaria (Contratos)"},
    "franquicias": {"nombre": "Franquicias", "tipo": "Sin Participación Accionaria (Contratos)"},
    "contratos_administracion": {"nombre": "Contratos de Administración",
                                 "tipo": "Sin Participación Accionaria (Contratos)"},
    "operaciones_llave_mano": {"nombre": "Operaciones Llave en Mano",
                               "tipo": "Sin Participación Accionaria (Contratos)"},
    "empresas_conjuntas": {"nombre": "Empresas Conjuntas (Joint Ventures)",
                           "tipo": "Con Participación Accionaria (Propiedad)"},
    "alianzas_participacion": {"nombre": "Alanzas con Participación (Subsidiaria Propia)",
                               "tipo": "Con Participación Accionaria (Propiedad)"}
}


# =========================================================================
# MOTOR GRÁFICO DE REDES DE NEGOCIACIÓN (PLOTLY MAP CREATOR)
# =========================================================================
def generar_mapa_red(simulaciones_filtradas):
    fig = go.Figure()

    for sim in simulaciones_filtradas:
        orig = sim['origen']
        dest = sim['destino']

        if orig in COORDENADAS_PAISES and dest in COORDENADAS_PAISES:
            coord_o = COORDENADAS_PAISES[orig]
            coord_d = COORDENADAS_PAISES[dest]

            if sim['compatibilidad'] >= 80:
                color_linea = '#28a745'  # Verde: Ajuste Alto
            elif sim['compatibilidad'] >= 60:
                color_linea = '#ffc107'  # Amarillo: Ajuste Moderado
            else:
                color_linea = '#dc3545'  # Rojo: Riesgo Crítico

            fig.add_trace(go.Scattergeo(
                lon=[coord_o['lon'], coord_d['lon']],
                lat=[coord_o['lat'], coord_d['lat']],
                mode='lines+markers',
                line=dict(width=3, color=color_linea),
                marker=dict(size=6, color='#003366'),
                hoverinfo='text',
                text=f"<b>Empresa:</b> {sim['empresa']}<br><b>Ruta:</b> {orig} ➔ {dest}<br><b>Estrategia:</b> {sim['estrategia']}<br><b>Ajuste:</b> {sim['compatibilidad']}%"
            ))

            fig.add_trace(go.Scattergeo(
                lon=[coord_d['lon']], lat=[coord_d['lat']],
                mode='markers',
                marker=dict(size=8, color='#2575fc'),
                hoverinfo='text',
                text=f"Mercado Destino: {dest}"
            ))

    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(
            scope='world',
            projection_type='equirectangular',
            showland=True, landcolor='#f8f9fa',
            showocean=True, oceancolor='#e3f2fd',
            showcountries=True, countrycolor='#ced4da',
            countrywidth=1
        ),
        height=450
    )
    return fig.to_html(full_html=False, include_plotlyjs='cdn')


# =========================================================================
# RUTAS DE ACCESO Y CONTROL DEL SISTEMA
# =========================================================================

@app.route('/')
def index():
    return render_template('formulario.html', paises=PAISES_MUNDIALES)


@app.route('/ir_a_filosofia', methods=['POST'])
def ir_a_filosofia():
    empresa = request.form.get('nombre_empresa', '').upper()
    origen = request.form.get('pais_origen')
    destino = request.form.get('pais_destino')
    estrategia = request.form.get('estrategia')
    return render_template('formulario2.html', empresa=empresa, origen=origen, destino=destino, estrategia=estrategia)


@app.route('/simular', methods=['POST'])
def simular():
    nombre_empresa = request.form.get('nombre_empresa').upper()
    pais_origen = request.form.get('pais_origen')
    pais_destino = request.form.get('pais_destino')
    estrategia_clave = request.form.get('estrategia')
    filosofia_cultural = request.form.get('filosofia_cultural')
    prioridad_legal = request.form.get('prioridad_legal')

    detalles = ESTRATEGIAS_ECOTEC.get(estrategia_clave, {"nombre": "Desconocida", "tipo": "Contratos"})
    cfg_destino = COORDENADAS_PAISES.get(pais_destino, {"perfil_cultural": "transaccional", "nivel_ip": "alto"})

    # ---------------------------------------------------------------------
    # NUEVO ALGORITMO ACADÉMICO DE PARAMETRIZACIÓN COMPLETA
    # Base inicial dinámica: Estrategias de propiedad requieren mayor análisis estructural
    # ---------------------------------------------------------------------
    puntaje = 100

    # 1. Ajuste de Cultura Corporativa vs Cultura del País de Destino
    if filosofia_cultural == "transaccional" and cfg_destino["perfil_cultural"] == "relacional":
        # Países de alta relación (Asia, Latam, Medio Oriente) sufren fricción severa con tácticas transaccionales
        puntaje -= 25
    elif filosofia_cultural == "relacional" and cfg_destino["perfil_cultural"] == "transaccional":
        # Países muy estructurados/normativos castigan la pérdida de tiempo o informalidad relacional
        puntaje -= 10

    # 2. Ajuste de Riesgo de Propiedad Intelectual (Legal)
    if prioridad_legal == "secretos_industriales":
        if cfg_destino["nivel_ip"] == "bajo":
            puntaje -= 30  # Riesgo extremo de copia/piratería (Ej. Venezuela, Rusia)
        elif cfg_destino["nivel_ip"] == "medio":
            puntaje -= 15  # Riesgo moderado institucional (Ej. China, Brasil)

    elif prioridad_legal == "contratos_estrictos" and cfg_destino["nivel_ip"] == "bajo":
        # Las cortes locales no ejecutan contratos eficientemente en entornos débiles
        puntaje -= 20

    # 3. Consistencia de la Estrategia de Entrada
    # Si hay alta fricción institucional (IP baja) y eligen Joint Ventures o Licencias sin control accionario duro
    if cfg_destino["nivel_ip"] == "bajo" and estrategia_clave in ["licencias", "empresas_conjuntas"]:
        puntaje -= 15

    # Acotar el puntaje en límites matemáticos reales (mínimo 40, máximo 100)
    puntaje = max(40, min(puntaje, 100))
    res_texto = "Ajuste altamente viable bajo el marco analítico." if puntaje >= 75 else (
        "Estrategia moderada con contingencias." if puntaje >= 60 else "Fricción estructural crítica detectada en el canal.")

    # GUARDAR EN BASE DE DATOS SQLITE (Persistencia)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO simulaciones (empresa, origen, destino, estrategia, compatibilidad, tipo_estrategia)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nombre_empresa, pais_origen, pais_destino, detalles['nombre'], puntaje, detalles['tipo']))
        conn.commit()

    return render_template('resultado.html', empresa=nombre_empresa, resultado=res_texto, consejos=[],
                           origen=pais_origen, destino=pais_destino, estrategia=detalles['nombre'],
                           compatibilidad=puntaje)


# 📊 VISTA 1: Dashboard del Estudiante (Lectura desde SQLite)
@app.route('/dashboard_estudiante')
def dashboard_estudiante():
    empresa_seleccionada = request.args.get('empresa', '').upper()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Si no seleccionó empresa, toma la última ingresada históricamente
        if not empresa_seleccionada:
            cursor.execute("SELECT empresa FROM simulaciones ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            empresa_seleccionada = row['empresa'] if row else ""

        # Leer registros de esta empresa
        cursor.execute("SELECT * FROM simulaciones WHERE empresa = ?", (empresa_seleccionada,))
        rows = cursor.fetchall()
        mis_negociaciones = [dict(r) for r in rows]

    if not mis_negociaciones:
        return redirect(url_for('index'))

    perfil_empresa = mis_negociaciones[-1]
    mapa_html = generar_mapa_red(mis_negociaciones)

    return render_template('dashboard_estudiante.html',
                           empresa=empresa_seleccionada,
                           perfil=perfil_empresa,
                           mis_negociaciones=mis_negociaciones,
                           mapa_html=mapa_html)


# 🎓 VISTA 2: Dashboard del Docente (Lectura Global desde SQLite)
@app.route('/dashboard_docente')
def dashboard_docente():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM simulaciones ORDER BY id DESC")
        rows = cursor.fetchall()
        todas_simulaciones = [dict(r) for r in rows]

    total = len(todas_simulaciones)
    promedio = sum(item['compatibilidad'] for item in todas_simulaciones) // total if total > 0 else 0

    filtro_empresa = request.args.get('empresa_auditar', 'GLOBAL')

    if filtro_empresa == 'GLOBAL':
        simulaciones_mapeadas = todas_simulaciones
        mapa_titulo = "Topología de Red Comercial Completa (Toda la Clase)"
    else:
        simulaciones_mapeadas = [item for item in todas_simulaciones if item['empresa'] == filtro_empresa]
        mapa_titulo = f"Auditoría de Red Individual: Empresa {filtro_empresa}"

    mapa_html = generar_mapa_red(simulaciones_mapeadas)
    lista_empresas_dropdown = sorted(list(set(item['empresa'] for item in todas_simulaciones)))

    return render_template('dashboard_docente.html',
                           simulaciones=todas_simulaciones,
                           total=total,
                           promedio=promedio,
                           mapa_html=mapa_html,
                           mapa_titulo=mapa_titulo,
                           lista_empresas=lista_empresas_dropdown,
                           empresa_actual=filtro_empresa)


if __name__ == '__main__':
    app.run(debug=True)