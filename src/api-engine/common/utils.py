import uuid
from urllib.parse import urljoin


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


def safe_urljoin(base: str, path: str) -> str:
    """Join a base URL and a path, ensuring the base URL's path is preserved.

    Unlike urllib.parse.urljoin, this function guarantees the base URL ends
    with a trailing slash before joining, so that any path segments in the
    base are not silently dropped.

    Example:
        safe_urljoin("http://host/api", "health")
        => "http://host/api/health"   (correct)

        urljoin("http://host/api", "health")
        => "http://host/health"       (wrong — drops /api)
    """
    if not base.endswith("/"):
        base = base + "/"
    return urljoin(base, path)
