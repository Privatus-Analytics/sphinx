# Changelog

## Unreleased

- With `privatus_queue_stub = True`, a tag that is off (`privatus_enabled = False` or no site id) now adds
  the queue stub and nothing else to web pages, so `privatus.track` calls never fail. Before, it added
  nothing. The props function is not called then.
- `example/`: a tiny site for the Privatus conformance tests, built with the extension and served by nginx.

## 1.0.0 - 2026-10-25

- Initial release.
- Sphinx extension `sphinx_privatus_analytics` that adds the tag to the `html`, `dirhtml` and
  `singlehtml` builders with `app.add_js_file`.
- `privatus_*` settings in conf.py for site id, script host, modules, excluded paths, domains,
  single-page app mode, manual mode, extra attributes, nonce, builders and the queue stub.
- Page props from `privatus_props`: a dict, or a function that gets the page name.
