from utils.materiales import (
    ESTADOS_GENERALES,
    ESTADOS_CIAIII
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

    return ESTADOS_GENERALES