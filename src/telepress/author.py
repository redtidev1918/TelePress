"""Structured Telegraph author metadata.

Encapsulates the flat ``author_name`` / ``author_url`` fields of the
Telegraph ``createPage`` / ``editPage`` API into one immutable object so
publish methods do not grow an ever-longer parameter list. Future author
attributes (avatar, description, publisher, channel link, ...) will be
added here instead of as new per-method parameters.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urlparse

from .exceptions import ValidationError


@dataclass(frozen=True)
class AuthorMetadata:
    """Author metadata attached to a published Telegraph page.

    Both fields are optional and may be supplied independently, mirroring
    the legacy ``author_name`` / ``author_url`` keyword arguments.

    Attributes:
        name: Author name displayed below the page title.
        url: ``http``/``https`` URL opened when the author name is clicked.
    """

    name: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self):
        if self.name is not None and not isinstance(self.name, str):
            raise ValidationError("author_name must be a string")

        if self.url is None:
            return
        if not isinstance(self.url, str):
            raise ValidationError("author_url must be a string")
        if any(char.isspace() for char in self.url):
            raise ValidationError("author_url must be a valid URL")

        parsed = urlparse(self.url)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise ValidationError("author_url must be a valid URL")

    def to_kwargs(self) -> Dict[str, str]:
        """Flatten to the fields Telegraph ``createPage``/``editPage`` accept.

        Fields the caller left unset are omitted so the page falls back to
        the account-level defaults, exactly like the legacy kwargs path.
        """
        kwargs: Dict[str, str] = {}
        if self.name is not None:
            kwargs['author_name'] = self.name
        if self.url is not None:
            kwargs['author_url'] = self.url
        return kwargs
