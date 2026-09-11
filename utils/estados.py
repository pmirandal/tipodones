from utils.materiales import (
    ESTADOS_GENERALES,
    ESTADOS_CIAIII,
    ESTADOS_MASCARAS
)


def obtener_estados(
    material,
    tipo
):

    if (
        material == "Encías"
        and tipo == "CIA III PPR"
    ):
        return ESTADOS_CIAIII

    if material == "Máscaras":
        return ESTADOS_MASCARAS

    return ESTADOS_GENERALES