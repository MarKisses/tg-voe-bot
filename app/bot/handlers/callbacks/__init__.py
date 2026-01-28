from .go import router as go_router
from .back import router as back_router
from .address import router as address_router
from .subscriptions import router as subscriptions_router
from .settings import router as settings_router

__all__ = [
    "go_router",
    "back_router",
    "address_router",
    "subscriptions_router",
    "settings_router"
]
