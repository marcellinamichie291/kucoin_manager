from typing import List

from kucoin_manager.settings import settings

MODELS_MODULES: List[str] = [
    "kucoin_manager.db.models.kucoin"
]  # noqa: WPS407

TORTOISE_CONFIG = {  # noqa: WPS407
    "connections": {
        "default": "sqlite://db_data/db.sqlite3",
    },
    "apps": {
        "models": {
            "models": MODELS_MODULES + ["aerich.models"],
            "default_connection": "default",
        },
    },
}
