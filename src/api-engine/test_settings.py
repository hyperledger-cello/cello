import tempfile

from api_engine.settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

MEDIA_ROOT = tempfile.mkdtemp(prefix="cello_test_media_")