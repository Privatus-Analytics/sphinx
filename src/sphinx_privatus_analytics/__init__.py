"""Cookieless Privatus Analytics tracking script for Sphinx HTML builds.

Add "sphinx_privatus_analytics" to `extensions` in conf.py and set
`privatus_site_id`. The extension only adds the browser script to your HTML
pages. It never sends events from the build machine and sets no cookies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._core import QUEUE_STUB, Settings, merge_props, page_props_json, props_script, tracker_attributes

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__version__ = "1.0.0"

# Builders that make web pages. Offline help formats such as epub, htmlhelp
# and qthelp are left out on purpose.
DEFAULT_BUILDERS = ("html", "dirhtml", "singlehtml")

# Before the theme's own scripts (500 is the default for html_js_files).
PRIORITY = 100

_FUNCTION = type(lambda: None)

_SETTINGS: dict[str, tuple[Any, frozenset[type]]] = {
    "privatus_site_id": ("", frozenset({str})),
    "privatus_script_host": ("", frozenset({str})),
    "privatus_modules": (None, frozenset({list, tuple, str})),
    "privatus_excluded_paths": (None, frozenset({list, tuple, str})),
    "privatus_domains": (None, frozenset({list, tuple, str})),
    "privatus_spa": (None, frozenset({str})),
    "privatus_manual": (False, frozenset({bool})),
    "privatus_enabled": (None, frozenset({bool})),
    "privatus_builders": (DEFAULT_BUILDERS, frozenset({list, tuple})),
    "privatus_extra_attributes": ({}, frozenset({dict})),
    "privatus_props": ({}, frozenset({dict, _FUNCTION})),
    "privatus_queue_stub": (False, frozenset({bool})),
    "privatus_nonce": ("", frozenset({str})),
}


def settings_from_config(config: Any) -> Settings:
    """The tag settings from conf.py."""
    return Settings(
        site_id=config.privatus_site_id,
        script_host=config.privatus_script_host,
        modules=config.privatus_modules,
        excluded_paths=config.privatus_excluded_paths,
        domains=config.privatus_domains,
        spa=config.privatus_spa,
        manual=config.privatus_manual,
        extra_attributes=config.privatus_extra_attributes or {},
        queue_stub=config.privatus_queue_stub,
        nonce=config.privatus_nonce or None,
    )


def is_enabled(app: Sphinx) -> bool:
    """`privatus_enabled` forces it on (any HTML builder) or off. Otherwise on for `privatus_builders`."""
    config = app.config
    if config.privatus_enabled is not None:
        return bool(config.privatus_enabled) and getattr(app.builder, "format", "") == "html"
    return app.builder.name in tuple(config.privatus_builders or ())


def page_props(app: Sphinx, pagename: str) -> dict[str, Any]:
    """`privatus_props` as a dict, or the result of calling it with the page name."""
    value = app.config.privatus_props
    if callable(value):
        value = value(pagename)
    return merge_props(value if isinstance(value, dict) else {})


def _string_attributes(attrs: dict[str, Any]) -> dict[str, str]:
    # Sphinx writes name="value" for every attribute, so a bare `defer` becomes defer="defer".
    return {name: (name if value is True else str(value)) for name, value in attrs.items()}


def is_web_page(app: Sphinx) -> bool:
    """Whether this build makes web pages: a builder in `privatus_builders`, or any HTML builder when
    `privatus_enabled` is set."""
    if app.config.privatus_enabled is not None:
        return getattr(app.builder, "format", "") == "html"
    return app.builder.name in tuple(app.config.privatus_builders or ())


def add_tag(app: Sphinx, pagename: str, templatename: str, context: dict[str, Any], doctree: Any) -> None:
    """Adds the scripts to one page. Sphinx resets page scripts after each page."""
    settings = settings_from_config(app.config)
    nonce = {"nonce": settings.nonce} if settings.nonce else {}
    if not is_enabled(app) or settings.resolved_site_id() is None:
        # The tag is off: only the queue stub (when it is on), so privatus.track calls never fail.
        # Props are not worked out, and builds that make no web pages (epub and so on) get nothing.
        if settings.queue_stub is True and is_web_page(app):
            app.add_js_file(None, priority=PRIORITY, body=QUEUE_STUB, **nonce)
        return
    props_json = page_props_json(page_props(app, pagename))
    if settings.queue_stub is True:
        app.add_js_file(None, priority=PRIORITY, body=QUEUE_STUB, **nonce)
    if props_json:
        app.add_js_file(None, priority=PRIORITY + 1, body=props_script(props_json), **nonce)
    attrs = _string_attributes(tracker_attributes(settings, bool(props_json)))
    src = attrs.pop("src")
    app.add_js_file(src, priority=PRIORITY + 2, **attrs)


def warn_without_site_id(app: Sphinx) -> None:
    if is_enabled(app) and settings_from_config(app.config).resolved_site_id() is None:
        from sphinx.util import logging

        logger = logging.getLogger(__name__)
        logger.info("privatus: no privatus_site_id (and no PRIVATUS_SITE_ID), so no tag was added.")


def setup(app: Sphinx) -> dict[str, Any]:
    for name, (default, types) in _SETTINGS.items():
        # A props function cannot be cached by Sphinx, so it must not take part in the rebuild check.
        rebuild = "" if name == "privatus_props" else "html"
        app.add_config_value(name, default, rebuild, types=types)
    app.connect("builder-inited", warn_without_site_id)
    app.connect("html-page-context", add_tag)
    return {"version": __version__, "parallel_read_safe": True, "parallel_write_safe": True}
