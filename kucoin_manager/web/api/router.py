from fastapi.routing import APIRouter

from kucoin_manager.web.api import kucoin, monitoring

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(kucoin.router, prefix="/kucoin")
