# Privatus Analytics for Sphinx

**Simple, private website analytics for your Sphinx docs. No cookies, honest numbers,
and a dashboard you understand in seconds.**

## Why Privatus Analytics

**Google Analytics is slow, confusing and hungry for data.** It sends what your
visitors do to Google. In many countries it means showing a cookie pop-up (the box
that asks visitors to accept cookies), and many people click "reject", so you never
see them. Bots pad the numbers that are left.

**Privatus Analytics fixes that.** It counts visits to your Sphinx docs without cookies and
never stores IP addresses. Bots are filtered out before they are counted. Your
data is never sold or shared.

What you get:

- **A dashboard you understand in seconds.** Visitors, top pages and where people
  came from, all on one screen.
- **No cookie pop-up needed for our analytics.** We set no cookies and store no
  personal data. Laws differ by country, so check your own legal advice.
- **Honest numbers.** Known bots and fake traffic are left out on every plan.
- **A fast docs site.** The tracking script is about 3 KB, tiny next to most tracking tags.
- **Data you own.** We never sell it or show you ads, and you can pull it out
  any time through the API.

**Start free.** The Free plan has 10,000 events a month and 3 sites, with no card.
Every new account also gets 14 days of Pro free, with no card.
[Create your account](https://privatusanalytics.com).

## What this package does

- A [Sphinx](https://www.sphinx-doc.org) extension that adds the tracking script
  to every page of your HTML docs.
- Works with any HTML theme and on [Read the Docs](https://about.readthedocs.com).
- The extension only adds the browser script to your HTML pages. It never sends
  events from your computer or build server and sets no cookies.

You need a Privatus Analytics account to see your reports, and there is a
free plan. [Sign up at privatusanalytics.com](https://privatusanalytics.com).

## Requirements

* Python 3.10 or later.
* Sphinx 7.2 or later.
* A Privatus Analytics site id (it starts with `pa_`). You find it under
  Site settings, Tracking.

## Install

```sh
pip install sphinx-privatus-analytics
```

For the full setup guide and every tracker option, see the [Privatus Analytics
docs](https://privatusanalytics.com/docs).

## Add the tag

Add the extension and your site id to `conf.py`:

```python
extensions = [
    "sphinx_privatus_analytics",
]

privatus_site_id = "pa_YOURSITEID"
```

Instead of writing the site id in `conf.py`, you can set the
`PRIVATUS_SITE_ID` environment variable on your build machine.

The `html`, `dirhtml` and `singlehtml` builders then add this to the `<head>` of
every page (Sphinx writes `defer="defer"`, which means the same as `defer`):

```html
<script data-site="pa_YOURSITEID" defer="defer" src="https://privatusstats.com/js/pa.js"></script>
```

No tag is added when there is no site id, and nothing for other builders such
as `epub`, `latexpdf` or the offline help formats. (With
`privatus_queue_stub = True`, web pages still get the small queue stub, see
below.)

## Read the Docs

1. List the package with your other docs requirements, for example in
   `docs/requirements.txt`:

   ```text
   sphinx-privatus-analytics
   ```

   and make sure `.readthedocs.yaml` installs it:

   ```yaml
   python:
     install:
       - requirements: docs/requirements.txt
   ```

2. Add the extension to `conf.py` as above. You can keep the site id out of
   the file: in your Read the Docs project, open Settings, Environment
   variables, and add `PRIVATUS_SITE_ID`.

3. Read the Docs also builds a preview for each pull request. To leave those
   out of your reports, turn the tag off for them. Read the Docs sets
   `READTHEDOCS_VERSION_TYPE` to `external` for pull request builds:

   ```python
   import os

   privatus_enabled = os.environ.get("READTHEDOCS_VERSION_TYPE") != "external"
   ```

   To count only your real address, set the hostnames too:

   ```python
   privatus_domains = ["docs.example.com"]
   ```

Read the Docs adds its own scripts to your pages (its "addons"). They do not
get in the way of the tracker.

## Configuration

Every setting is optional except the site id. All go in `conf.py`.

```python
privatus_site_id = "pa_YOURSITEID"  # or the PRIVATUS_SITE_ID environment variable
privatus_script_host = "https://privatusstats.com"  # or PRIVATUS_SCRIPT_HOST
privatus_modules = ["engage", "auto", "vitals", "clicks", "ask"]
privatus_excluded_paths = ["/drafts/*"]
privatus_domains = ["docs.example.com"]
privatus_spa = "auto"  # auto, history, hash or off
privatus_manual = False  # True turns off the automatic pageview
privatus_enabled = None  # True or False forces the tag on or off
privatus_builders = ["html", "dirhtml", "singlehtml"]
privatus_extra_attributes = {"data-mask": "/orders/*->/orders/:id"}
privatus_props = {"docs_version": "2.4"}
privatus_queue_stub = False
privatus_nonce = ""
```

| Setting | Default | What it does |
|---|---|---|
| `privatus_site_id` | `PRIVATUS_SITE_ID` | The `data-site` attribute. Nothing is added without it |
| `privatus_script_host` | `https://privatusstats.com` | Where `/js/pa.js` is served. Change it only if you host your own copy |
| `privatus_modules` | tracker default (`engage`) | The `data-modules` attribute. Setting it replaces the default, so keep `engage` for time on page and scroll depth. `[]` loads none |
| `privatus_excluded_paths` | none | The `data-exclude` attribute. Path patterns the tracker never counts |
| `privatus_domains` | all hosts | The `data-domains` attribute. Count only these hostnames |
| `privatus_spa` | `auto` | The `data-spa` attribute |
| `privatus_manual` | `False` | The `data-manual` attribute |
| `privatus_enabled` | `None` | `False` turns the tag off. `True` turns it on for every HTML builder. `None` uses `privatus_builders` |
| `privatus_builders` | `html`, `dirhtml`, `singlehtml` | The builders that get the tag |
| `privatus_extra_attributes` | `{}` | Any other `data-*` attribute |
| `privatus_props` | `{}` | Page props sent with every pageview and event. A dict, or a function that gets the page name. See below |
| `privatus_queue_stub` | `False` | Adds a small script first, so `privatus.track` calls made before the tracker loads are kept and sent later |
| `privatus_nonce` | none | A Content Security Policy nonce for the tags. Static sites rarely have one |

Each tracker attribute is explained in the [script attributes
reference](https://privatusanalytics.com/docs/tracker/attributes), and the
modules in [Modules](https://privatusanalytics.com/docs/tracker/modules).

### Development and test

Sphinx has no separate "development" build, so the tag is added to every
`html` build that has a site id. Your own visits are still not counted when you
open the pages from your disk or from `localhost` (for example with
`sphinx-autobuild`), because the tracker ignores them. To see the tracker work
there, pass `data-allow-local` or `data-debug` (see [Debug
mode](https://privatusanalytics.com/docs/tracker/debug)):

```python
privatus_extra_attributes = {"data-debug": "true"}
```

To keep the tag out of local builds altogether, set the site id only on your
build server with `PRIVATUS_SITE_ID`, or use
`privatus_enabled = os.environ.get("CI") == "true"`.

### Leaving people out

Use `privatus_excluded_paths` for pages you do not want counted, like drafts.
`privatus_domains` makes sure only your real site is counted, not previews or
copies on other hosts.

## Product analytics: see which features people use

Privatus Analytics can show which links and buttons people use in your docs, and which
parts of your docs lead people to sign up. You add a few attributes to your
HTML. The tracker reads them in the browser and sends the events. Your build
still sends nothing.

### Name events well

Use a short "Noun verb" name, like `Example copied` or `Download started`. Put
the details in props, not in the name. So write `Download started` with
`format: pdf`, not `Download started as PDF`. Then all downloads add up in one
place, and you can split them by format.

### Events on buttons, links and forms

reStructuredText has no way to add data attributes to a link, so use a `raw`
block for the parts you want to track:

```rst
.. raw:: html

   <a href="_static/guide.pdf" data-privatus-event="Download started" data-privatus-prop-format="pdf">Download the guide</a>
```

With MyST Markdown, write the HTML straight into the page. On a form, the
event is sent when the form is submitted. Use a short event name (at most 120
characters). Prop keys are lowercase letters, digits and `_`, and there can be
up to 30 of them.

### Click maps

A click map shows where people click on a page. Give the important parts a
name so they stay easy to find, even when the page changes:

```rst
.. raw:: html

   <a href="https://example.com/pricing" data-privatus-click="docs.pricing-link">See plans</a>
```

A name may use letters, digits and `_ . : -`, up to 100 characters.

### Page props: version, section and other groups

Page props are sent with every pageview and event on the page. Use them to
split your reports by docs version, section or product.

A dict sets them for every page:

```python
privatus_props = {"docs_version": release, "product": "api"}
```

A function gets the page name (like `index` or `guides/install`) and returns
the props for that page:

```python
def privatus_props(pagename):
    return {"docs_version": release, "section": pagename.split("/")[0]}
```

The extension then adds a small script before the tracker and points the
tracker at it:

```html
<script>window.privatusPageProps=function(){return {"docs_version":"2.4","section":"guides"}}</script>
<script data-props="privatusPageProps" data-site="pa_YOURSITEID" defer="defer" src="https://privatusstats.com/js/pa.js"></script>
```

Keys are made lowercase, and anything that is not a letter, a digit or `_`
becomes `_`. Numbers and true or false stay as they are, and lists stay lists
(up to 30 items). Text is cut to 500 characters. The props are escaped so they
are safe inside a script.

Sphinx only rewrites pages that changed. When you change only
`privatus_props`, build with `-E` (or `make clean html`) so every page gets the
new props.

**Never put names, emails, user ids or anything that points to one person in
props.** Privatus Analytics counts visitors without any id. Put groups (like the docs
version or the section), not people. The server also removes emails and long
ids it finds.

### Track from your own JavaScript

For things that are not a click or a submit, call the tracker from your
JavaScript (add your file with `html_js_files`), as the [JavaScript API
docs](https://privatusanalytics.com/docs/tracker/javascript-api) explain:

```js
privatus.track("Feature used", { feature: "search" })
```

If your code may run before the tracker has loaded, set
`privatus_queue_stub = True`. It adds a tiny script before the tracker that
keeps your calls in a list and sends them once the tracker is ready. The stub
is added to every web page even when the tag is off (with
`privatus_enabled = False` or with no site id), so your `privatus.track`
calls never fail while you write: they wait in the list and are never sent.
Then the extension adds the stub alone, once per page, with no tracker and no
page props, and it does not call a `privatus_props` function. With
`privatus_queue_stub = False` nothing is added when the tag is off.

### See the results

* [Funnels](https://privatusanalytics.com/docs/features/funnels): how many
  people go from one step to the next.
* [Click maps](https://privatusanalytics.com/docs/features/click-maps): where
  people click.
* [Goals](https://privatusanalytics.com/docs/features/goals): turn an event
  into a goal to count conversions.
* [Events](https://privatusanalytics.com/docs/events): every custom event and
  its props.

## Privacy

The script sets no cookies and stores nothing in the browser. The extension
only adds HTML to your pages. Keep people out of your props and event props:
no names, emails or user ids. See the [privacy
documentation](https://privatusanalytics.com/docs/privacy) for what is
collected.

If you have a privacy policy, it should say which tools handle your visitors' data. You can paste this:

> This website uses [Privatus Analytics](https://privatusanalytics.com/privacy-analytics) to count visits. It
> does not use cookies and does not follow you from one website to another. Your IP address is used for a moment
> to count visits and is never stored.

Change it to fit your site. The [privacy policy generator](https://privatusanalytics.com/tools/privacy-policy-generator)
makes a longer version with your site's name in it.

## Development

The tests run in Docker so your local Python does not matter:

```sh
./run-docker.sh
```

It runs pytest (with real Sphinx builds of a tiny project with the `html`,
`dirhtml`, `singlehtml`, `epub` and `text` builders), Ruff, and the package
build.

The `example/` folder holds a tiny site for the [conformance
tests](https://github.com/Privatus-Analytics/conformance), which open it in a
real browser with the real tracker. Run them from a copy of that repo with
`./run.sh ../sphinx`.

## Contributing

Bug reports and pull requests are welcome at
https://github.com/Privatus-Analytics/sphinx.

## License

MIT. See [LICENSE](LICENSE). Privatus Analytics is a product of Two Phase LLC,
Wyoming, USA.
