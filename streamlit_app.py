import streamlit as st

from utils.google_sheets import conectar_google

from utils.materiales import (
    MATERIALES,
    UBICACIONES
)

from utils.estados import (
    obtener_estados
)

from utils.movimientos import (
    ahora
)

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Control de Materiales FAEST",
    page_icon="📦",
    layout="wide"
)

# =====================================================
# GOOGLE SHEETS
# =====================================================

spreadsheet = conectar_google()

in_sheet = spreadsheet.worksheet(
    "IN"
)

out_sheet = spreadsheet.worksheet(
    "OUT"
)

log_sheet = spreadsheet.worksheet(
    "LOG_ESTADOS"
)

# =====================================================
# TÍTULO
# =====================================================

st.title(
    "📦 Control de Materiales FAEST"
)

st.caption(
    "Control de ubicación, estado y movimientos"
)

# =====================================================
# FUNCIONES
# =====================================================

def obtener_hoja(material):

    return spreadsheet.worksheet(
        MATERIALES[material]
    )


@st.cache_data(ttl=10)
def obtener_registros(material):

    hoja = obtener_hoja(
        material
    )

    return hoja.get_all_records()


def buscar_fila_codigo(
    hoja,
    codigo
):

    registros = hoja.get_all_records()

    for fila, registro in enumerate(
        registros,
        start=2
    ):

        if registro["Código"] == codigo:

            return fila, registro

    return None, None


def actualizar_registro(
    hoja,
    codigo,
    estado,
    ubicacion
):

    fila, registro = buscar_fila_codigo(
        hoja,
        codigo
    )

    if fila is None:

        return None

    encabezados = hoja.row_values(1)

    col_estado = (
        encabezados.index("Estado")
        + 1
    )

    col_ubicacion = (
        encabezados.index("Ubicación")
        + 1
    )

    estado_anterior = registro[
        "Estado"
    ]

    hoja.update_cell(
        fila,
        col_estado,
        estado
    )

    hoja.update_cell(
        fila,
        col_ubicacion,
        ubicacion
    )

    return estado_anterior

# =====================================================
# MENU
# =====================================================

opcion = st.radio(
    "Selecciona una opción",
    [
        "🔍 Consultar",
        "📤 Registrar salida",
        "📥 Registrar ingreso",
        "🛠 Actualizar estado"
    ],
    horizontal=True
)

# =====================================================
# SELECCIÓN DE MATERIAL
# =====================================================

material = st.selectbox(
    "Material",
    list(
        MATERIALES.keys()
    )
)

datos = obtener_registros(
    material
)

tipo = None

if material != "Máscaras":

    tipos = sorted(
        set(
            fila.get("Tipo", "")
            for fila in datos
            if fila.get("Tipo", "")
        )
    )

    tipo = st.selectbox(
        "Tipo",
        tipos
    )

detalle = None

if material == "Encías":

    detalles = sorted(
        set(
            fila["Detalle"]
            for fila in datos
            if fila["Tipo"] == tipo
        )
    )

    detalle = st.selectbox(
        "Detalle",
        detalles
    )

filtrados = datos.copy()

if material != "Máscaras":

    filtrados = [
        x
        for x in filtrados
        if x.get("Tipo") == tipo
    ]

if material == "Encías":

    filtrados = [
        x
        for x in filtrados
        if x.get("Detalle") == detalle
    ]

# =====================================================
# CONSULTAR
# =====================================================

if opcion == "🔍 Consultar":

    total = len(filtrados)

    smp = sum(
        1
        for x in filtrados
        if x["Ubicación"] == "SMP"
    )

    molina = sum(
        1
        for x in filtrados
        if x["Ubicación"] == "La Molina"
    )

    buenos = sum(
        1
        for x in filtrados
        if x["Estado"] == "Bueno"
    )

    deteriorados = sum(
        1
        for x in filtrados
        if x["Estado"] == "Deteriorado"
    )

    sin_existencia = sum(
        1
        for x in filtrados
        if x["Estado"] == "Sin existencia"
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric(
        "Total",
        total
    )

    c2.metric(
        "SMP",
        smp
    )

    c3.metric(
        "La Molina",
        molina
    )

    c4.metric(
        "Buenos",
        buenos
    )

    c5.metric(
        "Deteriorados",
        deteriorados
    )

    c6.metric(
        "Sin existencia",
        sin_existencia
    )

    st.markdown("---")

    st.dataframe(
        filtrados,
        use_container_width=True,
        hide_index=True
    )

# =====================================================
# MOVIMIENTOS Y ESTADOS
# =====================================================

elif opcion in [
    "📤 Registrar salida",
    "📥 Registrar ingreso",
    "🛠 Actualizar estado"
]:

    codigos_disponibles = sorted(
        [
            x["Código"]
            for x in filtrados
        ]
    )

    modo = st.radio(
        "Modo de selección",
        [
            "Unidad",
            "Rango",
            "Selección múltiple"
        ],
        horizontal=True
    )

    codigos = []

    # -----------------------------------
    # UNIDAD
    # -----------------------------------

    if modo == "Unidad":

        codigo = st.selectbox(
            "Código",
            codigos_disponibles
        )

        codigos = [codigo]

    # -----------------------------------
    # RANGO
    # -----------------------------------

    elif modo == "Rango":

        numeros = sorted(
            [
                codigo.split("-")[-1]
                for codigo in codigos_disponibles
            ]
        )

        desde = st.selectbox(
            "Desde",
            numeros
        )

        hasta = st.selectbox(
            "Hasta",
            numeros,
            index=len(numeros) - 1
        )

        inicio = int(desde)
        fin = int(hasta)

        codigos = [
            codigo
            for codigo in codigos_disponibles
            if inicio <= int(
                codigo.split("-")[-1]
            ) <= fin
        ]

        st.info(
            f"Se seleccionarán "
            f"{len(codigos)} registros"
        )

    # -----------------------------------
    # MULTIPLE
    # -----------------------------------

    else:

        codigos = st.multiselect(
            "Selecciona códigos",
            codigos_disponibles
        )

        st.info(
            f"{len(codigos)} seleccionados"
        )

    estado = st.selectbox(
        "Estado",
        obtener_estados(
            material,
            tipo if tipo else ""
        )
    )

    ubicacion = st.selectbox(
        "Ubicación",
        UBICACIONES
    )

    observacion = st.text_area(
        "Observación"
    )

    # -----------------------------------
    # BOTON
    # -----------------------------------

    if st.button(
        "Guardar",
        use_container_width=True
    ):

        if len(codigos) == 0:

            st.warning(
                "Selecciona al menos un código."
            )

            st.stop()

        hoja = obtener_hoja(
            material
        )

        fecha = ahora()

        actualizados = 0

        for codigo in codigos:

            fila, registro = buscar_fila_codigo(
                hoja,
                codigo
            )

            if fila is None:
                continue

            estado_anterior = actualizar_registro(
                hoja,
                codigo,
                estado,
                ubicacion
            )

            if estado_anterior is None:
                continue

            tipo_registro = registro.get(
                "Tipo",
                material
            )

            # -----------------------------
            # SALIDA
            # -----------------------------

            if opcion == "📤 Registrar salida":

                out_sheet.append_row(
                    [
                        fecha,
                        material,
                        codigo,
                        tipo_registro,
                        estado,
                        ubicacion,
                        observacion
                    ],
                    value_input_option="USER_ENTERED"
                )

            # -----------------------------
            # INGRESO
            # -----------------------------

            elif opcion == "📥 Registrar ingreso":

                in_sheet.append_row(
                    [
                        fecha,
                        material,
                        codigo,
                        tipo_registro,
                        estado,
                        ubicacion,
                        observacion
                    ],
                    value_input_option="USER_ENTERED"
                )

            # -----------------------------
            # CAMBIO ESTADO
            # -----------------------------

            else:

                log_sheet.append_row(
                    [
                        fecha,
                        material,
                        codigo,
                        estado_anterior,
                        estado,
                        observacion
                    ],
                    value_input_option="USER_ENTERED"
                )

            actualizados += 1

        obtener_registros.clear()

        st.success(
            f"✅ {actualizados} registros actualizados."
        )

        st.rerun()