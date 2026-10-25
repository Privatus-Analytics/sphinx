# Conformance example site (see the conformance repo's CONTRACT.md). Build with the
# package folder as the context:
#   docker build -f example/Dockerfile .
#
# A static site reads its settings when it is built, not when it is served, so the
# site id and script host are build arguments. Their defaults are the values the
# conformance suite uses.
FROM python:3.13-slim AS build
ARG PRIVATUS_SITE_ID=pa_CONFORMANCE1
ARG PRIVATUS_SCRIPT_HOST=http://mock:4000
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_ROOT_USER_ACTION=ignore PYTHONDONTWRITEBYTECODE=1 \
    PRIVATUS_SITE_ID=$PRIVATUS_SITE_ID PRIVATUS_SCRIPT_HOST=$PRIVATUS_SCRIPT_HOST
# The extension from this repo's own source, not from PyPI.
COPY pyproject.toml README.md LICENSE CHANGELOG.md /pkg/
COPY src/ /pkg/src/
RUN pip install --no-cache-dir /pkg
COPY example/ /example/
RUN sh /example/build.sh /site

FROM nginx:1.27-alpine
COPY example/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /site /usr/share/nginx/html
EXPOSE 8080
