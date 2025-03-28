FROM postgis/postgis:15-3.3

ENV POSTGRES_DB=trud
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

COPY trud.dump /docker-entrypoint-initdb.d/trud.dump
COPY restore.sh /docker-entrypoint-initdb.d/zzz-restore.sh
RUN chmod +x /docker-entrypoint-initdb.d/zzz-restore.sh