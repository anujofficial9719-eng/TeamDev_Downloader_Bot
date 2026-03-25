from .start import register_start_handlers
from .download import register_download_handlers
from .admin import register_admin_handlers

__all__ = [
    "register_start_handlers",
    "register_download_handlers",
    "register_admin_handlers",
]
