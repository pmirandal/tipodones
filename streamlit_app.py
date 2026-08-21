import streamlit as st
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Control de Tipodones",
    page_icon="🦷",
    layout="wide"
)

# =====================================================
# TIPOS
# =====================================================

TIPOS = {
    "CIA I 2024": "T-C124",
    "CIA I 2025": "T-C125",
    "CIA III PPR 2024": "T-C3P24",
    "CIA III PPR 2025": "T-C325"
}

UBICACIONES = [
    "SMP",
    "La Molina"
]

ESTADOS = [
    "Bueno",
    "Deteriorado"
]

# =====================================================
# GOOGLE SHEETS
# =====================================================

@st.cache_resource
def conectar_google():

    credentials_info = json.loads(
        os.environ["GOOGLE_CREDENTIALS"]
    )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        credentials_info,
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open(
        "Seguimiento Materiales FAEST"
    )

    ub_sheet = spreadsheet.worksheet(
        "ub_tipodones"
    )

    in_sheet = spreadsheet.worksheet(
        "IN"
    )

    out_sheet = spreadsheet.worksheet(
        "OUT"
    )

    return ub_sheet, in_sheet, out_sheet


ub_sheet, in_sheet, out_sheet = conectar_google()

# =====================================================
# DATOS
# =====================================================

@st.cache_data(ttl=10)
def obtener_tipodones():

    return ub_sheet.get_all_records()


# =====================================================
# FUNCIONES
# =====================================================

def generar_codigos(tipo, inicio, fin):

    prefijo = TIPOS[tipo]

    return [
        f"{prefijo}-{i:02d}"
        for i in range(inicio, fin + 1)
    ]


def buscar_fila_codigo(codigo):

    registros = ub_sheet.get_all_records()

    for fila, registro in enumerate(
        registros,
        start=2
    ):

        if registro["Código"] == codigo:

            return fila, registro

    return None, None


def actualizar_tipodon(
    codigo,
    nueva_ubicacion,
    nuevo_estado
):

    fila, _ = buscar_fila_codigo(codigo)

    if fila is None:
        return False

    ub_sheet.update(
        f"D{fila}:E{fila}",
        [[
            nuevo_estado,
            nueva_ubicacion
        ]]
    )

    return True


def ahora():

    return datetime.now(
        ZoneInfo("America/Lima")
    ).strftime(
        "%d/%m/%Y %H:%M:%S"
    )


# =====================================================
# TÍTULO
# =====================================================

st.title("🦷 Control de Tipodones")

st.markdown(
    "Ubicación, estado e historial de movimientos"
)

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
# CONSULTAR
# =====================================================

if opcion == "🔍 Consultar":

    datos = obtener_tipodones()

    tipo = st.selectbox(
        "Tipo",
        list(TIPOS.keys())
    )

    filtrados = [
        x
        for x in datos
        if x["Tipo"] == tipo
    ]

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

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total", total)
    c2.metric("SMP", smp)
    c3.metric("La Molina", molina)
    c4.metric("Deteriorados", deteriorados)

    st.dataframe(
        filtrados,
        use_container_width=True
    )

# =====================================================
# REGISTRO MOVIMIENTO
# =====================================================

elif opcion in [
    "📤 Registrar salida",
    "📥 Registrar ingreso"
]:

    tipo = st.selectbox(
        "Tipo",
        list(TIPOS.keys())
    )

    modo = st.radio(
        "Modo",
        [
            "Unidad",
            "Rango"
        ],
        horizontal=True
    )

    if modo == "Unidad":

        numero = st.number_input(
            "Número",
            min_value=1,
            max_value=70,
            value=1
        )

        codigos = generar_codigos(
            tipo,
            numero,
            numero
        )

    else:

        inicio = st.number_input(
            "Desde",
            min_value=1,
            max_value=70,
            value=1
        )

        fin = st.number_input(
            "Hasta",
            min_value=1,
            max_value=70,
            value=10
        )

        codigos = generar_codigos(
            tipo,
            inicio,
            fin
        )

    st.info(
        f"Se actualizarán {len(codigos)} tipodones"
    )

    ubicacion = st.selectbox(
        "Ubicación",
        UBICACIONES
    )

    estado = st.selectbox(
        "Estado",
        ESTADOS
    )

    observacion = st.text_area(
        "Observación"
    )

    boton = st.button(
        opcion
    )

    if boton:

        fecha = ahora()

        errores = []

        for codigo in codigos:

            fila, registro = buscar_fila_codigo(
                codigo
            )

            if fila is None:

                errores.append(
                    codigo
                )

                continue

            actualizar_tipodon(
                codigo,
                ubicacion,
                estado
            )

            nueva_fila = [
                fecha,
                codigo,
                registro["Nombre"],
                registro["Tipo"],
                estado,
                ubicacion,
                observacion
            ]

            if opcion == "📤 Registrar salida":

                out_sheet.append_row(
                    nueva_fila,
                    value_input_option="USER_ENTERED"
                )

            else:

                in_sheet.append_row(
                    nueva_fila,
                    value_input_option="USER_ENTERED"
                )

        obtener_tipodones.clear()

        st.success(
            f"{len(codigos) - len(errores)} registros actualizados."
        )

        if errores:

            st.warning(
                f"No encontrados: {errores}"
            )

# =====================================================
# ACTUALIZAR ESTADO
# =====================================================

elif opcion == "🛠 Actualizar estado":

    tipo = st.selectbox(
        "Tipo",
        list(TIPOS.keys())
    )

    numero = st.number_input(
        "Número",
        min_value=1,
        max_value=70,
        value=1
    )

    codigo = generar_codigos(
        tipo,
        numero,
        numero
    )[0]

    estado = st.selectbox(
        "Nuevo estado",
        ESTADOS
    )

    if st.button(
        "Actualizar estado"
    ):

        fila, registro = buscar_fila_codigo(
            codigo
        )

        if fila is None:

            st.error(
                "Código no encontrado"
            )

        else:

            ubicacion_actual = registro[
                "Ubicación"
            ]

            actualizar_tipodon(
                codigo,
                ubicacion_actual,
                estado
            )

            obtener_tipodones.clear()

            st.success(
                f"{codigo} actualizado correctamente."
            )