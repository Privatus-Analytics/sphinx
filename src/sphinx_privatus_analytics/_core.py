"""Builds the Privatus Analytics script tag and page props script.

Plain Python with no dependencies. This module only builds HTML text. It never
sends anything over the network, sets no cookies and reads nothing about visitors.
"""

from __future__ import annotations

import html
import json
import math
import os
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

DEFAULT_HOST = "https://privatusstats.com"
SPA_MODES = ("auto", "history", "hash", "off")
MARKER = "/js/pa.js"
PROPS_FUNCTION = "privatusPageProps"
QUEUE_STUB = (
    "window.privatus=window.privatus||{q:[]};['track','pageview','props','optOut','optIn','ready']"
    ".forEach(function(m){window.privatus[m]=window.privatus[m]||function(){window.privatus.q.push("
    "[m,Array.prototype.slice.call(arguments)])}})"
)

MAX_NAME = 120
MAX_KEY = 64
MAX_PROPS = 30
MAX_VALUE = 500
MAX_ITEMS = 30
CLICK_NAME = re.compile(r"[A-Za-z0-9_.:-]{1,100}")
_KEY_UNSAFE = re.compile(r"[^a-z0-9_]")
_JSON_UNSAFE = re.compile("[<>&\u2028\u2029]")
_LIST_OPTIONS = (("modules", "data-modules"), ("excluded_paths", "data-exclude"), ("domains", "data-domains"))


@dataclass
class Settings:
    """Tag settings. Every one is optional except the site id."""

    site_id: str | None = None
    script_host: str | None = None
    modules: Any = None
    excluded_paths: Any = None
    domains: Any = None
    spa: str | None = None
    manual: bool = False
    extra_attributes: Mapping[str, Any] = field(default_factory=dict)
    queue_stub: bool = False
    nonce: str | None = None

    def resolved_site_id(self) -> str | None:
        """The site id, or PRIVATUS_SITE_ID from the environment, or None."""
        value = str(self.site_id or "").strip() or os.environ.get("PRIVATUS_SITE_ID", "").strip()
        return value or None

    def resolved_script_host(self) -> str:
        """The script host, or PRIVATUS_SCRIPT_HOST, or the default, without a trailing slash."""
        value = str(self.script_host or "").strip() or os.environ.get("PRIVATUS_SCRIPT_HOST", "").strip()
        return (value or DEFAULT_HOST).rstrip("/")


def normalize_key(key: Any) -> str:
    """Lowercases a prop key, swaps anything outside a-z 0-9 _ for _ and cuts it to 64 characters."""
    return _KEY_UNSAFE.sub("_", str(key).lower())[:MAX_KEY]


def normalize(props: Mapping[str, Any] | None) -> dict[str, Any]:
    """Cleans the keys, drops None values and keeps the first 30 props."""
    clean: dict[str, Any] = {}
    for key, value in dict(props or {}).items():
        key = normalize_key(key)
        if key and value is not None:
            clean[key] = value
    return dict(list(clean.items())[:MAX_PROPS])


def _text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def string_value(value: Any) -> str:
    """An event prop value as text: lists joined with commas, cut to 500 characters."""
    if isinstance(value, (list, tuple)):
        text = ",".join(_text(item) for item in value if item is not None)
    else:
        text = _text(value)
    return text[:MAX_VALUE]


def event_attributes(name: Any, props: Mapping[str, Any] | None = None) -> dict[str, str]:
    """{"data-privatus-event": name, "data-privatus-prop-<key>": value, ...}, or {} for an empty name."""
    name = str(name if name is not None else "").strip()[:MAX_NAME].strip()
    if not name:
        return {}
    attrs = {"data-privatus-event": name}
    for key, value in normalize(props).items():
        attrs[f"data-privatus-prop-{key}"] = string_value(value)
    return attrs


def valid_click(name: Any) -> bool:
    """Whether a click map name uses only letters, digits and _ . : - with at most 100 characters."""
    return name is not None and CLICK_NAME.fullmatch(str(name)) is not None


def click_attributes(name: Any) -> dict[str, str]:
    """{"data-privatus-click": name}, or {} when the name is not valid."""
    return {"data-privatus-click": str(name)} if valid_click(name) else {}


def to_html(attrs: Mapping[str, Any]) -> str:
    """An attribute dict as HTML, every value escaped. True prints the bare name."""
    parts = []
    for name, value in attrs.items():
        if value is True:
            parts.append(name)
        else:
            parts.append(f'{name}="{html.escape(str(value), quote=True)}"')
    return " ".join(parts)


def _scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return str(value)[:MAX_VALUE]


def _json_value(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        items = [item for item in value if item is not None][:MAX_ITEMS]
        return [s for s in (_scalar(item) for item in items) if s is not None]
    return _scalar(value)


def page_props_json(props: Mapping[str, Any] | None) -> str | None:
    """Page props as a JSON object that is safe inside <script>, or None when there are none."""
    clean = {}
    for key, value in normalize(props).items():
        value = _json_value(value)
        if value is not None:
            clean[key] = value
    if not clean:
        return None
    text = json.dumps(clean, separators=(",", ":"), ensure_ascii=False)
    return _JSON_UNSAFE.sub(lambda match: f"\\u{ord(match.group()):04x}", text)


def merge_props(*layers: Mapping[str, Any] | None) -> dict[str, Any]:
    """Merges props layers left to right by cleaned key. A None value removes a key."""
    merged: dict[str, Any] = {}
    for layer in layers:
        for key, value in dict(layer or {}).items():
            merged[normalize_key(key)] = value
    return merged


def as_list(value: Any) -> list[str] | None:
    """None stays None. A string or a list becomes a clean list, split on commas."""
    if value is None:
        return None
    items: Iterable[Any] = [value] if isinstance(value, str) else value
    out = []
    for item in items:
        out.extend(part.strip() for part in str(item).split(","))
    return [part for part in out if part]


def props_script(props_json: str) -> str:
    """The JavaScript that defines the page props function."""
    return f"window.{PROPS_FUNCTION}=function(){{return {props_json}}}"


def tracker_attributes(settings: Settings, with_props: bool = False) -> dict[str, Any]:
    """The tracker tag's attributes in print order. True means a bare attribute."""
    attrs: dict[str, Any] = {
        "defer": True,
        "src": f"{settings.resolved_script_host()}{MARKER}",
        "data-site": settings.resolved_site_id(),
    }
    for name, attribute in _LIST_OPTIONS:
        values = as_list(getattr(settings, name))
        # None keeps the tracker default. An empty modules list loads none.
        if values is not None and (name == "modules" or values):
            attrs[attribute] = ",".join(values)
    spa = str(settings.spa or "")
    if spa in SPA_MODES and spa != "auto":
        attrs["data-spa"] = spa
    if settings.manual is True:
        attrs["data-manual"] = "true"
    for name, value in dict(settings.extra_attributes or {}).items():
        if value is not None:
            attrs[str(name)] = value
    if settings.nonce:
        attrs["nonce"] = settings.nonce
    if with_props:
        attrs["data-props"] = PROPS_FUNCTION
    return attrs


def _inline(code: str, nonce: str | None) -> str:
    opening = f'<script nonce="{html.escape(str(nonce), quote=True)}">' if nonce else "<script>"
    return f"{opening}{code}</script>"


def render_tag(settings: Settings, props: Mapping[str, Any] | None = None) -> str:
    """The full HTML: queue stub (optional), page props script (when there are props), tracker tag.

    Returns "" without a site id. Whether the tag is on at all is the caller's job.
    """
    if settings.resolved_site_id() is None:
        return ""
    props_json = page_props_json(props)
    parts = []
    if settings.queue_stub is True:
        parts.append(_inline(QUEUE_STUB, settings.nonce))
    if props_json:
        parts.append(_inline(props_script(props_json), settings.nonce))
    parts.append(f"<script {to_html(tracker_attributes(settings, bool(props_json)))}></script>")
    return "\n".join(parts)


_HEAD_CLOSE = re.compile(r"</head>", re.IGNORECASE)


def inject(page_html: str, tag_html: str) -> str:
    """Puts the tag just before the first </head>. Leaves pages without a head, or with the tag, alone."""
    match = _HEAD_CLOSE.search(page_html)
    # Only the head is checked for the tag, so a page that shows the snippet as text still gets it.
    if not tag_html or match is None or MARKER in page_html[: match.start()]:
        return page_html
    return f"{page_html[: match.start()]}{tag_html}\n{page_html[match.start() :]}"
