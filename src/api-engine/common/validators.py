from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from fqdn import FQDN

_url_validator = URLValidator()


def validate_url(value):
    try:
        _url_validator(value)
        return value
    except ValidationError:
        parsed = urlparse(value)
        scheme, host = parsed.scheme, parsed.hostname or ""
        if scheme not in ("http", "https"):
            raise ValidationError(
                "Invalid scheme. URLs must start with 'http' or 'https'"
            )
        validate_host(host)
        return value

def validate_host(value):
    fqdn = FQDN(value, min_labels=1)
    if not fqdn.is_valid:
        raise ValidationError("Invalid hostname")
