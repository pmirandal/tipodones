from datetime import datetime
from zoneinfo import ZoneInfo

def ahora():
    return datetime.now(
        ZoneInfo("America/Lima")
    ).strftime(
        "%d/%m/%Y %H:%M:%S"
    )