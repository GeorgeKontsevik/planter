# pull official base image
FROM python:3.10.0-slim-buster

# set work directory
WORKDIR /usr/api

# copy requirements file
COPY ./reqs_cleaned.txt /usr/api/app/reqs.txt
RUN pip install setuptools==65.5.1 pip==23.2.1 wheel==0.41.0
# RUN apt-get remove -y python3-shapely
# install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        cmake \
        python3-dev \
        libffi-dev \
        libssl-dev \
        libgdal-dev \
        libspatialindex-dev \
    && pip install --upgrade Cython \
    && pip install --no-cache-dir -r /usr/api/app/reqs.txt \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /root/.cache/pip
# copy project
COPY . /usr/api/

VOLUME /usr/api


CMD  ["uvicorn", "api.app.main:app", "--reload", "--workers", "-1", "--host", "0.0.0.0", "--port", "8000"]