# Sphinx settings for the conformance example. build.sh sets EXAMPLE_BUILD to main,
# off or off-plain. The site id and script host come from PRIVATUS_SITE_ID and
# PRIVATUS_SCRIPT_HOST.
import os

NASTY = "</script><script>window.__pwned=1</script>\u2028\u2029&<>\"'"
BUILD = os.environ.get("EXAMPLE_BUILD", "main")

project = "Privatus conformance"
extensions = ["sphinx_privatus_analytics"]
html_theme = "basic"
html_sidebars = {"**": []}
templates_path = ["_templates"]
exclude_patterns = ["_build"]

privatus_queue_stub = BUILD != "off-plain"
privatus_enabled = BUILD == "main"
html_context = {"off_markers": BUILD != "main"}


def privatus_props(pagename):
    """The page props. /nasty also gets the nasty value."""
    props = {"plan": "pro", "role": "admin", "beta": True, "seats": 3}
    if pagename == "nasty":
        props["nasty"] = NASTY
    return props
