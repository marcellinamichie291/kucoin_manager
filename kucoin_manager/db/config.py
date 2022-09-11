from typing import List

from kucoin_manager.settings import settings

MODELS_MODULES: List[str] = [
    "kucoin_manager.db.models.dummy_model",
    "kucoin_manager.db.models.kucoin_model",
]  # noqa: WPS407

TORTOISE_CONFIG = {  # noqa: WPS407
    "connections": {
        "default": str(settings.db_url),
    },
    "apps": {
        "models": {
            "models": MODELS_MODULES + ["aerich.models"],
            "default_connection": "default",
        },
    },
}
