FROM postgres:16

ENV POSGRES_CONFIG="log_replication_commands = on"
ENV POSTGRES_HOST_AUTH_METHOD="scram-sha-256" 
ENV POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256"

COPY ./init.sql /docker-entrypoint-initdb.d/init.sql

CMD ["postgres"]
