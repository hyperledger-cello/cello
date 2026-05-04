import uuid
from urllib.parse import urlparse, urlunparse


def make_uuid():
    return str(uuid.uuid4())


def separate_upper_class(class_name):
    x = ""
    i = 0
    for c in class_name:
        if c.isupper() and not class_name[i - 1].isupper():
            x += " %s" % c.lower()
        else:
            x += c
        i += 1
    return "_".join(x.strip().split(" "))


def normalize_agent_url(url: str) -> str:
    """Ensure the URL path ends with a trailing slash.

    Uses urllib.parse to safely modify only the path component,
    preserving any query strings or fragments unchanged.
    """
    parsed = urlparse(url)
    if not parsed.path.endswith("/"):
        parsed = parsed._replace(path=parsed.path + "/")
    return urlunparse(parsed)
