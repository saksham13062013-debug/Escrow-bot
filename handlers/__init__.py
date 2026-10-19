from .user import router as user_router
from .admin import router as admin_router
from .group import router as group_router
from .verify import router as verify_router

__all__ = ["user_router", "admin_router", "group_router", "verify_router"]
