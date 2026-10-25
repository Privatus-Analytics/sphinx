import json

import pytest

from sphinx_privatus_analytics import _core
from sphinx_privatus_analytics._core import Settings, inject, page_props_json, render_tag

BASIC = '<script defer src="https://privatusstats.com/js/pa.js" data-site="pa_TEST123456"></script>'


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("PRIVATUS_SITE_ID", raising=False)
    monkeypatch.delenv("PRIVATUS_SCRIPT_HOST", raising=False)


def test_basic_tag():
    assert render_tag(Settings(site_id="pa_TEST123456")) == BASIC


def test_nothing_without_a_site_id():
    assert render_tag(Settings()) == ""


def test_site_id_and_host_from_the_environment(monkeypatch):
    monkeypatch.setenv("PRIVATUS_SITE_ID", "pa_ENV")
    monkeypatch.setenv("PRIVATUS_SCRIPT_HOST", "https://stats.example.com/")
    assert render_tag(Settings()) == (
        '<script defer src="https://stats.example.com/js/pa.js" data-site="pa_ENV"></script>'
    )


def test_list_options_spa_manual():
    tag = render_tag(
        Settings(
            site_id="pa_X",
            modules=["engage", "auto"],
            excluded_paths=["/admin/*", "/preview/*"],
            domains="example.com, www.example.com",
            spa="hash",
            manual=True,
        )
    )
    assert 'data-modules="engage,auto"' in tag
    assert 'data-exclude="/admin/*,/preview/*"' in tag
    assert 'data-domains="example.com,www.example.com"' in tag
    assert 'data-spa="hash"' in tag
    assert 'data-manual="true"' in tag


def test_empty_modules_loads_none_and_empty_lists_print_nothing():
    tag = render_tag(Settings(site_id="pa_X", modules=[], excluded_paths=[], domains=[]))
    assert 'data-modules=""' in tag
    assert "data-exclude" not in tag
    assert "data-domains" not in tag


def test_auto_and_unknown_spa_modes_print_nothing():
    assert "data-spa" not in render_tag(Settings(site_id="pa_X", spa="auto"))
    assert "data-spa" not in render_tag(Settings(site_id="pa_X", spa="bogus"))


def test_escapes_values_and_adds_extras_and_nonce():
    tag = render_tag(
        Settings(
            site_id="pa_X",
            excluded_paths=['/a"b'],
            extra_attributes={"data-mask": "/orders/*->/orders/:id", "data-gone": None},
            nonce="abc123",
        )
    )
    assert 'data-exclude="/a&quot;b"' in tag
    assert 'data-mask="/orders/*-&gt;/orders/:id"' in tag
    assert "data-gone" not in tag
    assert 'nonce="abc123"' in tag


def test_page_props_script_before_the_tag():
    html = render_tag(Settings(site_id="pa_TEST123456"), {"plan": "pro", "role": "admin"})
    assert html == (
        '<script>window.privatusPageProps=function(){return {"plan":"pro","role":"admin"}}</script>\n'
        '<script defer src="https://privatusstats.com/js/pa.js" data-site="pa_TEST123456" '
        'data-props="privatusPageProps"></script>'
    )


def test_queue_stub_then_props_then_tag_with_nonce():
    parts = render_tag(Settings(site_id="pa_X", queue_stub=True, nonce="n1"), {"plan": "pro"}).split("\n")
    assert parts[0] == f'<script nonce="n1">{_core.QUEUE_STUB}</script>'
    assert parts[1].startswith('<script nonce="n1">window.privatusPageProps=')
    assert "/js/pa.js" in parts[2]


def test_queue_stub_is_the_official_one():
    assert _core.QUEUE_STUB == (
        "window.privatus=window.privatus||{q:[]};['track','pageview','props','optOut','optIn','ready']"
        ".forEach(function(m){window.privatus[m]=window.privatus[m]||function(){window.privatus.q.push("
        "[m,Array.prototype.slice.call(arguments)])}})"
    )


def test_props_json_types_and_rules():
    assert page_props_json({}) is None
    assert page_props_json({"gone": None}) is None
    assert (
        page_props_json({"seats": 5, "ratio": 1.5, "beta": True, "old": False, "flags": ["a", None, "b", 3]})
        == '{"seats":5,"ratio":1.5,"beta":true,"old":false,"flags":["a","b",3]}'
    )
    assert page_props_json({"App Version": "2.1"}) == '{"app_version":"2.1"}'
    assert page_props_json({"bad": float("nan")}) is None


def test_props_limits():
    assert len(json.loads(page_props_json({f"p{i}": i for i in range(40)}))) == 30
    assert len(json.loads(page_props_json({"list": [str(i) for i in range(50)]}))["list"]) == 30
    assert len(json.loads(page_props_json({"long": "x" * 900}))["long"]) == 500


def test_props_json_is_safe_inside_a_script():
    text = page_props_json({"note": "</script><b>&\u2028\u2029"})
    assert text == '{"note":"\\u003c/script\\u003e\\u003cb\\u003e\\u0026\\u2028\\u2029"}'
    for char in "<>&\u2028\u2029":
        assert char not in text


def test_merge_props_none_removes():
    assert _core.merge_props({"plan": "pro", "Role": "admin"}, {"role": None, "tier": "gold"}) == {
        "plan": "pro",
        "role": None,
        "tier": "gold",
    }
    assert page_props_json(_core.merge_props({"plan": "pro", "role": "a"}, {"role": None})) == '{"plan":"pro"}'


def test_event_and_click_attributes():
    assert _core.event_attributes("  Export CSV ", {"format": "csv", "Report Type": "a", "on": True}) == {
        "data-privatus-event": "Export CSV",
        "data-privatus-prop-format": "csv",
        "data-privatus-prop-report_type": "a",
        "data-privatus-prop-on": "true",
    }
    assert _core.event_attributes("  ") == {}
    assert _core.click_attributes("pricing.cta") == {"data-privatus-click": "pricing.cta"}
    assert _core.click_attributes("has space") == {}


def test_inject_before_head_once():
    page = "<html><head><title>x</title></head><body></body></html>"
    out = inject(page, BASIC)
    assert out == f"<html><head><title>x</title>{BASIC}\n</head><body></body></html>"
    assert inject(out, BASIC) == out
    assert inject("<p>no head</p>", BASIC) == "<p>no head</p>"
    assert inject(page, "") == page


def test_inject_still_adds_when_the_snippet_is_only_shown_in_the_body():
    page = "<html><head></head><body><code>/js/pa.js</code></body></html>"
    assert BASIC in inject(page, BASIC)
