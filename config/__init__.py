# This makes config a Python package

# Install PyMySQL as MySQLdb (required for Django MySQL backend)
import pymysql
pymysql.install_as_MySQLdb()

# Import Celery (optional - only if celery is installed)
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not installed, skip
    __all__ = ()
