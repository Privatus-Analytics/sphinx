#!/bin/sh
# Builds the docs three times and puts the pages in one folder ($1).
#   main       /, /event and /nasty: the extension as most projects use it
#   off        /off: the tag forced off, queue stub on
#   off-plain  /off-plain: the tag forced off, queue stub off
# Sphinx has no auto inject step (the extension adds the tag to every page itself),
# so there is no /auto page and nginx answers 404 for it.
set -e
out="$1"
cd "$(dirname "$0")"
EXAMPLE_BUILD=main sphinx-build -q -b dirhtml -d /tmp/doctrees-main docs "$out"
rm -rf "$out/off" "$out/off-plain"
for name in off off-plain; do
  EXAMPLE_BUILD=$name sphinx-build -q -b dirhtml -d "/tmp/doctrees-$name" docs "/tmp/$name"
  mkdir -p "$out/$name"
  cp "/tmp/$name/off/index.html" "$out/$name/index.html"
done
