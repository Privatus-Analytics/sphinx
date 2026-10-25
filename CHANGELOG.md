# Changelog

## 1.0.0 - 2026-10-25

- Initial release.
- Sphinx extension `sphinx_privatus_analytics` that adds the tag to the `html`, `dirhtml` and
  `singlehtml` builders with `app.add_js_file`.
- `privatus_*` settings in conf.py for site id, script host, modules, excluded paths, domains,
  single-page app mode, manual mode, extra attributes, nonce, builders and the queue stub.
- Page props from `privatus_props`: a dict, or a function that gets the page name.
