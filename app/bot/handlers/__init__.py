from aiogram import Dispatcher

from .commands.start import router as start_router
from .callbacks import go_router, back_router, address_router
from .address_flow import address_router as address_flow_router


def register_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(go_router)
    dp.include_router(back_router)
    dp.include_router(address_router)
    dp.include_router(address_flow_router)


__all__ = ["register_handlers"]