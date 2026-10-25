"""Real Sphinx builds of a tiny project in a temporary folder."""

import re
import textwrap
from pathlib import Path

import pytest
from sphinx.cmd.build import build_main

from sphinx_privatus_analytics import _core

TRACKER = re.compile(r"<script[^>]*/js/pa\.js[^>]*></script>")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("PRIVATUS_SITE_ID", raising=False)
    monkeypatch.delenv("PRIVATUS_SCRIPT_HOST", raising=False)


def build(tmp_path: Path, conf: str, builder: str = "html") -> Path:
    src = tmp_path / "src"
    src.mkdir(parents=True)
    base = 'project = "Test docs"\ncopyright = "2026"\nversion = "1.0"\n'
    (src / "conf.py").write_text(base + 'extensions = ["sphinx_privatus_analytics"]\n' + textwrap.dedent(conf))
    (src / "index.rst").write_text("Home\n====\n\n.. toctree::\n\n   guide\n")
    (src / "guide.rst").write_text("Guide\n=====\n\nText.\n")
    out = tmp_path / "out"
    # -W turns warnings into errors, so a config type warning fails the test.
    assert build_main(["-b", builder, "-W", "-q", "-E", "-d", str(tmp_path / "doctrees"), str(src), str(out)]) == 0
    return out


def head(path: Path) -> str:
    return path.read_text().split("</head>")[0]


def tracker(html: str) -> str:
    found = TRACKER.findall(html)
    assert len(found) == 1, found
    return found[0]


def test_html_build_adds_the_tag_to_every_page(tmp_path):
    out = build(tmp_path, 'privatus_site_id = "pa_TEST123456"\n')
    for page in ("index.html", "guide.html", "search.html", "genindex.html"):
        tag = tracker(head(out / page))
        assert 'src="https://privatusstats.com/js/pa.js"' in tag
        assert 'data-site="pa_TEST123456"' in tag
        assert 'defer="defer"' in tag
        assert "data-props" not in tag


def test_dirhtml_and_singlehtml_get_it(tmp_path):
    for builder in ("dirhtml", "singlehtml"):
        out = build(tmp_path / builder, 'privatus_site_id = "pa_TEST123456"\n', builder)
        assert 'data-site="pa_TEST123456"' in tracker(head(out / "index.html"))


def test_epub_and_text_do_not(tmp_path):
    out = build(tmp_path / "epub", 'privatus_site_id = "pa_TEST123456"\nprivatus_enabled = True\n', "epub")
    assert not any("/js/pa.js" in p.read_text() for p in out.rglob("*.xhtml"))
    out = build(tmp_path / "epub2", 'privatus_site_id = "pa_TEST123456"\n', "epub")
    assert not any("/js/pa.js" in p.read_text() for p in out.rglob("*.xhtml"))
    out = build(tmp_path / "text", 'privatus_site_id = "pa_TEST123456"\n', "text")
    assert "/js/pa.js" not in (out / "index.txt").read_text()


def test_site_id_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATUS_SITE_ID", "pa_ENV")
    out = build(tmp_path, "")
    assert 'data-site="pa_ENV"' in tracker(head(out / "index.html"))


def test_no_site_id_or_disabled_adds_nothing(tmp_path):
    out = build(tmp_path / "a", "")
    assert "/js/pa.js" not in (out / "index.html").read_text()
    out = build(tmp_path / "b", 'privatus_site_id = "pa_TEST123456"\nprivatus_enabled = False\n')
    assert "/js/pa.js" not in (out / "index.html").read_text()


def test_options_reach_the_tag_and_are_escaped(tmp_path):
    conf = """\
        privatus_site_id = "pa_TEST123456"
        privatus_script_host = "https://stats.example.com/"
        privatus_modules = ["engage", "auto"]
        privatus_excluded_paths = ['/a"b/*']
        privatus_domains = "docs.example.com"
        privatus_spa = "hash"
        privatus_manual = True
        privatus_extra_attributes = {"data-mask": "/x/*->/x/:id"}
        privatus_nonce = "n0nce"
        """
    tag = tracker(head(build(tmp_path, conf) / "index.html"))
    assert 'src="https://stats.example.com/js/pa.js"' in tag
    assert 'data-modules="engage,auto"' in tag
    assert 'data-exclude="/a&quot;b/*"' in tag
    assert 'data-domains="docs.example.com"' in tag
    assert 'data-spa="hash"' in tag
    assert 'data-manual="true"' in tag
    assert 'data-mask="/x/*-&gt;/x/:id"' in tag
    assert 'nonce="n0nce"' in tag


def test_props_dict_and_queue_stub_come_before_the_tracker(tmp_path):
    conf = """\
        privatus_site_id = "pa_TEST123456"
        privatus_props = {"docs_version": "2.4", "Beta": True}
        privatus_queue_stub = True
        privatus_nonce = "n0nce"
        """
    html = head(build(tmp_path, conf) / "index.html")
    stub = f'<script nonce="n0nce">{_core.QUEUE_STUB}</script>'
    data = '{"docs_version":"2.4","beta":true}'
    props = f'<script nonce="n0nce">window.privatusPageProps=function(){{return {data}}}</script>'
    tag = tracker(html)
    assert 'data-props="privatusPageProps"' in tag
    assert html.index(stub) < html.index(props) < html.index(tag)


def test_props_callable_gets_the_page_name(tmp_path):
    conf = """\
        privatus_site_id = "pa_TEST123456"

        def privatus_props(pagename):
            return {"section": pagename.split("/")[0], "note": "</script>"}
        """
    out = build(tmp_path, conf)
    home = head(out / "index.html")
    guide = head(out / "guide.html")
    assert '{return {"section":"index","note":"\\u003c/script\\u003e"}}' in home
    assert '{return {"section":"guide","note":"\\u003c/script\\u003e"}}' in guide
    assert guide.count("privatusPageProps=") == 1


def test_custom_builders_list(tmp_path):
    out = build(tmp_path, 'privatus_site_id = "pa_TEST123456"\nprivatus_builders = ["dirhtml"]\n')
    assert "/js/pa.js" not in (out / "index.html").read_text()


STUB = "<script>" + _core.QUEUE_STUB + "</script>"


def test_off_with_the_queue_stub_adds_only_the_stub(tmp_path):
    conf = (
        'privatus_site_id = "pa_TEST123456"\nprivatus_enabled = False\nprivatus_queue_stub = True\n'
        'privatus_nonce = "n1"\nprivatus_props = {"plan": "pro"}\n'
    )
    page = head(build(tmp_path, conf) / "index.html")
    assert page.count('<script nonce="n1">' + _core.QUEUE_STUB + "</script>") == 1
    assert "/js/pa.js" not in page
    assert "privatusPageProps" not in page


def test_off_without_the_queue_stub_adds_nothing(tmp_path):
    conf = 'privatus_site_id = "pa_TEST123456"\nprivatus_enabled = False\nprivatus_props = {"plan": "pro"}\n'
    page = head(build(tmp_path, conf) / "index.html")
    assert "window.privatus" not in page
    assert "/js/pa.js" not in page


def test_no_site_id_with_the_queue_stub_adds_only_the_stub_and_skips_the_props_function(tmp_path):
    # The props function fails the build if it is called.
    conf = "privatus_queue_stub = True\ndef privatus_props(page):\n    raise RuntimeError('props called')\n"
    page = head(build(tmp_path, conf) / "index.html")
    assert page.count(STUB) == 1
    assert "/js/pa.js" not in page
    assert "privatusPageProps" not in page


def test_the_stub_is_not_added_to_epub(tmp_path):
    out = build(tmp_path, 'privatus_site_id = "pa_TEST123456"\nprivatus_queue_stub = True\n', builder="epub")
    assert "window.privatus" not in "".join(p.read_text() for p in out.glob("*.xhtml"))


PAGES = ("index.html", "guide.html", "genindex.html", "search.html")


def test_off_with_the_queue_stub_adds_one_stub_to_every_page_and_never_calls_props(tmp_path):
    conf = (
        'privatus_site_id = "pa_TEST123456"\nprivatus_enabled = False\nprivatus_queue_stub = True\n'
        "def privatus_props(page):\n    raise RuntimeError('props called')\n"
    )
    out = build(tmp_path, conf)
    for name in PAGES:
        html = (out / name).read_text()
        assert head(out / name).count(STUB) == 1, name
        assert html.count("window.privatus=window.privatus") == 1, name
        assert "/js/pa.js" not in html, name
        assert "privatusPageProps" not in html, name
        assert "data-props" not in html, name


def test_off_without_the_queue_stub_adds_nothing_to_any_page(tmp_path):
    conf = (
        'privatus_site_id = "pa_TEST123456"\nprivatus_enabled = False\n'
        "def privatus_props(page):\n    raise RuntimeError('props called')\n"
    )
    out = build(tmp_path, conf)
    for name in PAGES:
        html = (out / name).read_text()
        assert "window.privatus" not in html, name
        assert "/js/pa.js" not in html, name
