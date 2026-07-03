from flask import Flask, render_template, request, redirect, url_for
import plotly.graph_objects as go
import json

app = Flask(__name__)

# =========================================================================
# BASE DE DATOS DEL ECOSISTEMA COMPLETO (20 Empresas del Aula en Red)
# =========================================================================
ECOSISTEMA_SIMULACIONES = [
    {"empresa": "LONGCHA TEA", "origen": "China", "destino": "Ecuador", "estrategia": "Franquicias",
     "compatibilidad": 85, "tipo_estrategia": "Sin Participación Accionaria (Contratos)"},
    {"empresa": "INCAFOODS", "origen": "Ecuador", "destino": "Estados Unidos", "estrategia": "Exportación Directa",
     "compatibilidad": 95, "tipo_estrategia": "Sin Participación Accionaria (Contratos)"},
    {"empresa": "EUROTECH", "origen": "Alemania", "destino": "México",
     "estrategia": "Empresas Conjuntas (Joint Ventures)", "compatibilidad": 60,
     "tipo_estrategia": "Con Participación Accionaria (Propiedad)"},
    {"empresa": "ANDINA LOGISTICS", "origen": "Ecuador", "destino": "España",
     "estrategia": "Alanzas con Participación (Subsidiaria Propia)", "compatibilidad": 40,
     "tipo_estrategia": "Con Participación Accionaria (Propiedad)"},
    {"empresa": "AZTEC EXPORTS", "origen": "México", "destino": "Alemania", "estrategia": "Licencias",
     "compatibilidad": 78, "tipo_estrategia": "Sin Participación Accionaria (Contratos)"},
    {"empresa": "SAMURAI CORP", "origen": "Japón", "destino": "Estados Unidos",
     "estrategia": "Alanzas con Participación (Subsidiaria Propia)", "compatibilidad": 92,
     "tipo_estrategia": "Con Participación Accionaria (Propiedad)"},
    {"empresa": "PACIFIC COFFEE", "origen": "Ecuador", "destino": "China",
     "estrategia": "Empresas Conjuntas (Joint Ventures)", "compatibilidad": 50,
     "tipo_estrategia": "Con Participación Accionaria (Propiedad)"}
]

# Diccionario Geográfico de Coordenadas para trazar los vectores comerciales en el mapa mundial
COORDENADAS_PAISES = {
    "Ecuador": {"lat": -1.8312, "lon": -78.1834},
    "Estados Unidos": {"lat": 37.0902, "lon": -95.7129},
    "China": {"lat": 35.8617, "lon": 104.1954},
    "Alemania": {"lat": 51.1657, "lon": 10.4515},
    "México": {"lat": 23.6345, "lon": -102.5528},
    "España": {"lat": 40.4637, "lon": -3.7492},
    "Japón": {"lat": 36.2048, "lon": 138.2529}
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

    # Dibujar líneas de conexión y nodos por cada simulación
    for sim in simulaciones_filtradas:
        orig = sim['origen']
        dest = sim['destino']

        if orig in COORDENADAS_PAISES and dest in COORDENADAS_PAISES:
            coord_o = COORDENADAS_PAISES[orig]
            coord_d = COORDENADAS_PAISES[dest]

            # Asignación de colores según la compatibilidad teórica de la red
            if sim['compatibilidad'] >= 80:
                color_linea = '#28a745'  # Verde: Ajuste Alto
            elif sim['compatibilidad'] >= 55:
                color_linea = '#ffc107'  # Amarillo: Ajuste Moderado
            else:
                color_linea = '#dc3545'  # Rojo: Riesgo Crítico

            # 1. Trazar el vector de red de negociación comercial (Origen -> Destino)
            fig.add_trace(go.Scattergeo(
                lon=[coord_o['lon'], coord_d['lon']],
                lat=[coord_o['lat'], coord_d['lat']],
                mode='lines+markers',
                line=dict(width=3, color=color_linea),
                marker=dict(size=6, color='#003366'),
                hoverinfo='text',
                text=f"<b>Empresa:</b> {sim['empresa']}<br><b>Ruta:</b> {orig} ➔ {dest}<br><b>Estrategia:</b> {sim['estrategia']}<br><b>Ajuste:</b> {sim['compatibilidad']}%"
            ))

            # 2. Agregar etiqueta de texto flotante en los nodos de los países
            fig.add_trace(go.Scattergeo(
                lon=[coord_d['lon']], lat=[coord_d['lat']],
                mode='markers',
                marker=dict(size=8, color='#2575fc'),
                hoverinfo='text',
                text=f"Mercado Destino: {dest}"
            ))

    # Configuración estética global del mapa mundial interactivo
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

    # Retorna el componente en formato HTML incrustable
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

    # Lógica de cálculo simplificada para la simulación activa
    puntaje = 90
    if filosofia_cultural == "transaccional" and pais_destino == "China": puntaje -= 30
    if prioridad_legal == "secretos_industriales" and pais_destino == "Ecuador": puntaje -= 20

    res_texto = "Ajuste viable bajo el marco analítico." if puntaje >= 70 else "Fricción crítica detectada en el canal internacional."

    # Guardamos en nuestra red centralizada
    ECOSISTEMA_SIMULACIONES.append({
        "empresa": nombre_empresa, "origen": pais_origen, "destino": pais_destino,
        "estrategia": detalles['nombre'], "compatibilidad": puntaje, "tipo_estrategia": detalles['tipo']
    })

    return render_template('resultado.html', empresa=nombre_empresa, resultado=res_texto, consejos=[],
                           origen=pais_origen, destino=pais_destino, estrategia=detalles['nombre'],
                           compatibilidad=puntaje)


# 📊 VISTA 1: Dashboard del Estudiante (Optimizado con Matriz de Decisiones Propia)
@app.route('/dashboard_estudiante')
def dashboard_estudiante():
    if not ECOSISTEMA_SIMULACIONES:
        return redirect(url_for('index'))

    empresa_seleccionada = request.args.get('empresa', '').upper()

    if not empresa_seleccionada:
        empresa_seleccionada = ECOSISTEMA_SIMULACIONES[-1]['empresa']

    perfil_empresa = next((item for item in ECOSISTEMA_SIMULACIONES if item['empresa'] == empresa_seleccionada), None)

    # Extraemos ÚNICAMENTE los registros y negociaciones que le pertenecen a este alumno
    mis_negociaciones = [item for item in ECOSISTEMA_SIMULACIONES if item['empresa'] == empresa_seleccionada]

    # Generamos el mapa con sus vectores comerciales
    mapa_html = generar_mapa_red(mis_negociaciones)

    return render_template('dashboard_estudiante.html',
                           empresa=empresa_seleccionada,
                           perfil=perfil_empresa,
                           mis_negociaciones=mis_negociaciones,  # <-- Enviamos su bitácora de datos a la vista
                           mapa_html=mapa_html)

# 🎓 VISTA 2: Dashboard del Docente (Control Global y Desglose por Empresa)
@app.route('/dashboard_docente')
def dashboard_docente():
    total = len(ECOSISTEMA_SIMULACIONES)
    promedio = sum(item['compatibilidad'] for item in ECOSISTEMA_SIMULACIONES) // total if total > 0 else 0

    # Captura si el docente quiere ver a todo el salón o auditar a una empresa en específico
    filtro_empresa = request.args.get('empresa_auditar', 'GLOBAL')

    if filtro_empresa == 'GLOBAL':
        # Muestra la red interactiva de todos los estudiantes superpuestos
        simulaciones_mapeadas = ECOSISTEMA_SIMULACIONES
        mapa_titulo = "Topología de Red Comercial Completa (Toda la Clase)"
    else:
        # Aísla la red del estudiante seleccionado para la auditoría del docente
        simulaciones_mapeadas = [item for item in ECOSISTEMA_SIMULACIONES if item['empresa'] == filtro_empresa]
        mapa_titulo = f"Auditoría de Red Individual: Empresa {filtro_empresa}"

    mapa_html = generar_mapa_red(simulaciones_mapeadas)
    lista_empresas_dropdown = [item['empresa'] for item in ECOSISTEMA_SIMULACIONES]

    return render_template('dashboard_docente.html',
                           simulaciones=ECOSISTEMA_SIMULACIONES,
                           total=total,
                           promedio=promedio,
                           mapa_html=mapa_html,
                           mapa_titulo=mapa_titulo,
                           lista_empresas=lista_empresas_dropdown,
                           empresa_actual=filtro_empresa)


if __name__ == '__main__':
    app.run(debug=True)