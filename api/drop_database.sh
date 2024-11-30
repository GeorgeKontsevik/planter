#!/bin/bash

DB_NAME="trud"

# Terminate connections
psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}';"

# Drop the database
dropdb -U postgres ${DB_NAME}

echo "Database ${DB_NAME} dropped successfully."
