#!/bin/bash
echo "🧙 Restoring trud.dump..."
pg_restore -U $POSTGRES_USER -d $POSTGRES_DB /docker-entrypoint-initdb.d/trud.dump