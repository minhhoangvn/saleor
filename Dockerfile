### Build and install packages
FROM python:3.8 as build-python

RUN apt-get -y update \
  && apt-get install -y gettext \
  # Cleanup apt cache
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_dev.txt /app/
WORKDIR /app
RUN pip install -r requirements_dev.txt

### Final image
FROM python:3.8-slim

ARG STATIC_URL
ENV STATIC_URL ${STATIC_URL:-/static/}

RUN groupadd -r saleor && useradd -r -g saleor saleor

RUN apt-get update \
  && apt-get install -y \
  libxml2 \
  libssl1.1 \
  libcairo2 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgdk-pixbuf2.0-0 \
  shared-mime-info \
  mime-support \
  netcat \
  postgresql-client \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY . /app
COPY --from=build-python /usr/local/lib/python3.8/site-packages/ /usr/local/lib/python3.8/site-packages/
COPY --from=build-python /usr/local/bin/ /usr/local/bin/
WORKDIR /app

RUN SECRET_KEY=dummy STATIC_URL=${STATIC_URL} python3 manage.py collectstatic --no-input

RUN mkdir -p /app/media /app/static \
  && chown -R saleor:saleor /app/

EXPOSE 8000
EXPOSE 9191
ENV PORT 8000
ENV PYTHONUNBUFFERED 1
ENV PROCESSES 8
ENV UWSGI_FILE 'uwsgi-production.ini'
CMD ["sh","-c","uwsgi --ini /app/saleor/wsgi/$UWSGI_FILE"]
