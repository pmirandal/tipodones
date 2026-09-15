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
@st.cache_resource
def obtener_spreadsheet():
    return conectar_google()

spreadsheet = obtener_spreadsheet()

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
# TITULO
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


@st.cache_data(ttl=300)
def obtener_registros(material):

    hoja = obtener_hoja(material)

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
# MATERIAL
# =====================================================

material = st.selectbox(
    "Material",
    list(MATERIALES.keys())
)

datos = obtener_registros(
    material
)

# =====================================================
# TIPO
# =====================================================

tipo = None

tipo = None

tipos = sorted(
    set(
        fila.get("Tipo", "")
        for fila in datos
        if fila.get("Tipo", "")
    )
)

if len(tipos) > 0:

    tipo = st.selectbox(
        "Tipo",
        tipos
    )

# =====================================================
# DETALLE
# =====================================================

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

# =====================================================
# FILTRAR DATOS
# =====================================================

filtrados = datos.copy()

if tipo:

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

    c1.metric("Total", total)
    c2.metric("SMP", smp)
    c3.metric("La Molina", molina)
    c4.metric("Buenos", buenos)
    c5.metric("Deteriorados", deteriorados)
    c6.metric("Sin existencia", sin_existencia)

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

    # ------------------------------------
    # UNIDAD
    # ------------------------------------

    if modo == "Unidad":

        codigo = st.selectbox(
            "Código",
            codigos_disponibles
        )

        codigos = [codigo]

        registro_actual = next(
            (
                r
                for r in filtrados
                if r["Código"] == codigo
            ),
            None
        )

        if registro_actual:

            st.info(
                f"""
    Código: {registro_actual['Código']}

    Tipo: {registro_actual.get('Tipo', 'N/A')}

    Estado actual: {registro_actual['Estado']}

    Ubicación actual: {registro_actual['Ubicación']}
    """
            )

            if registro_actual["Estado"] == "Sin existencia":

                st.error(
                    "⚠️ Este material está marcado como "
                    "'Sin existencia'."
                )
    # ------------------------------------
    # RANGO
    # ------------------------------------

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
            f"Se seleccionarán {len(codigos)} registros"
        )

        sin_existencia = []

        for codigo_sel in codigos:

            registro = next(
                (
                    r
                    for r in filtrados
                    if r["Código"] == codigo_sel
                ),
                None
            )

            if (
                registro
                and registro["Estado"]
                == "Sin existencia"
            ):

                sin_existencia.append(
                    codigo_sel
                )

        if sin_existencia:

            st.warning(
                f"""
        Seleccionados: {len(codigos)}

        Sin existencia: {len(sin_existencia)}

        Códigos:
        {", ".join(sin_existencia)}
        """
            )

    # ------------------------------------
    # MULTIPLE
    # ------------------------------------

    else:

        codigos = st.multiselect(
            "Selecciona códigos",
            codigos_disponibles
        )

        st.info(
            f"{len(codigos)} seleccionados"
        )

        sin_existencia = []

        for codigo_sel in codigos:

            registro = next(
                (
                    r
                    for r in filtrados
                    if r["Código"] == codigo_sel
                ),
                None
            )

            if (
                registro
                and registro["Estado"]
                == "Sin existencia"
            ):

                sin_existencia.append(
                    codigo_sel
                )

        if sin_existencia:

            st.warning(
                f"""
        Seleccionados: {len(codigos)}

        Sin existencia: {len(sin_existencia)}

        Códigos:
        {", ".join(sin_existencia)}
        """
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

    # =====================================
    # GUARDAR
    # =====================================

    if st.button(
        "Guardar",
        use_container_width=True
    ):

        if not codigos:

            st.warning(
                "Selecciona al menos un código."
            )

            st.stop()

        hoja = obtener_hoja(
            material
        )

        fecha = ahora()

        actualizados = 0

        # =====================================
        # LEER HOJA UNA SOLA VEZ
        # =====================================

        todos_los_valores = hoja.get_all_values()

        encabezados = todos_los_valores[0]

        registros = [
            dict(zip(encabezados, fila))
            for fila in todos_los_valores[1:]
        ]

        indice_codigos = {}

        for fila_num, registro in enumerate(
            registros,
            start=2
        ):

            indice_codigos[
                registro["Código"]
            ] = (
                fila_num,
                registro
            )
        # =====================================
        # VALIDAR EXISTENCIA PARA SALIDAS
        # =====================================

        if opcion == "📤 Registrar salida":

            no_existentes = []

            for codigo in codigos:

                if codigo not in indice_codigos:
                    continue

                _, registro = indice_codigos[codigo]

                if registro["Estado"] == "Sin existencia":

                    no_existentes.append(
                        codigo
                    )

            if no_existentes:

                lista = ", ".join(
                    no_existentes
                )

                st.error(
                    "❌ No se puede registrar la salida.\n\n"
                    "Los siguientes códigos tienen estado "
                    f"'Sin existencia':\n\n{lista}"
                )

                st.stop()

        # =====================================
        # VALIDAR EXISTENCIA PARA
        # INGRESOS Y SALIDAS
        # =====================================

        if opcion in [
            "📤 Registrar salida",
            "📥 Registrar ingreso"
        ]:

            no_existentes = []

            for codigo in codigos:

                if codigo not in indice_codigos:
                    continue

                _, registro = indice_codigos[codigo]

                if registro["Estado"] == "Sin existencia":

                    no_existentes.append(
                        codigo
                    )

            if no_existentes:

                lista = ", ".join(
                    no_existentes
                )

                accion = (
                    "salida"
                    if opcion == "📤 Registrar salida"
                    else "ingreso"
                )

                st.error(
                    f"❌ No se puede registrar la {accion}.\n\n"
                    f"Los siguientes materiales "
                    f"tienen estado "
                    f"'Sin existencia':\n\n"
                    f"{lista}"
                )

                st.stop()
        
        # =====================================
        # CALCULAR COLUMNAS
        # =====================================

        col_estado = (
            encabezados.index("Estado")
            + 1
        )

        col_ubicacion = (
            encabezados.index("Ubicación")
            + 1
        )

        letra_estado = chr(
            64 + col_estado
        )

        letra_ubicacion = chr(
            64 + col_ubicacion
        )

        # =====================================
        # ACUMULADORES
        # =====================================

        actualizaciones = []

        filas_in = []

        filas_out = []

        filas_log = []

        # =====================================
        # PROCESAR
        # =====================================

        for codigo in codigos:

            if codigo not in indice_codigos:
                continue

            fila, registro = indice_codigos[
                codigo
            ]

            estado_anterior = registro[
                "Estado"
            ]

            actualizaciones.append(
                {
                    "range": f"{letra_estado}{fila}",
                    "values": [[estado]]
                }
            )

            actualizaciones.append(
                {
                    "range": f"{letra_ubicacion}{fila}",
                    "values": [[ubicacion]]
                }
            )

            tipo_registro = registro.get(
                "Tipo",
                material
            )

            if opcion == "📤 Registrar salida":

                filas_out.append(
                    [
                        fecha,
                        material,
                        codigo,
                        tipo_registro,
                        estado,
                        ubicacion,
                        observacion
                    ]
                )

            elif opcion == "📥 Registrar ingreso":

                filas_in.append(
                    [
                        fecha,
                        material,
                        codigo,
                        tipo_registro,
                        estado,
                        ubicacion,
                        observacion
                    ]
                )

            else:

                filas_log.append(
                    [
                        fecha,
                        material,
                        codigo,
                        estado_anterior,
                        estado,
                        observacion
                    ]
                )

            actualizados += 1

        # =====================================
        # BATCH UPDATE
        # =====================================

        if actualizaciones:

            hoja.batch_update(
                actualizaciones
            )

        # =====================================
        # HISTORIAL
        # =====================================

        if filas_out:

            out_sheet.append_rows(
                filas_out,
                value_input_option="USER_ENTERED"
            )

        if filas_in:

            in_sheet.append_rows(
                filas_in,
                value_input_option="USER_ENTERED"
            )

        if filas_log:

            log_sheet.append_rows(
                filas_log,
                value_input_option="USER_ENTERED"
            )

        obtener_registros.clear()

        st.success(
            f"✅ {actualizados} registros actualizados."
        )

        st.rerun()