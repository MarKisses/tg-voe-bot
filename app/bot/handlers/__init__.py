from aiogram import Dispatcher

from .main_menu import router as start_router
from .commands.admin import router as admin_router
from .callbacks import go_router, back_router, address_router, subscriptions_router, settings_router
from .address_flow import address_router as address_flow_router
from .deleter import router as deleter_router


def register_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(go_router)
    dp.include_router(back_router)
    dp.include_router(address_router)
    dp.include_router(address_flow_router)
    dp.include_router(subscriptions_router)
    dp.include_router(settings_router)
    dp.include_router(deleter_router)


__all__ = ["register_handlers"]