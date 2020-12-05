#!/bin/bash

## Postgres configuration

# Verify if Postgres is installed
if ! type "psql" > /dev/null; then
    echo "Postgres not installed."
    printf "To install: sudo apt-get install postgresql\n"
    echo "Then run this script again"
fi

# Drop old database and user
sudo -u postgres dropdb macAmigo_db >> /dev/null
sudo -u postgres dropuser superAmigo >> /dev/null

# Create database and user
sudo -u postgres psql << EOF
create database macAmigo_db;
create user superAmigo with password 'superAmigo';
alter role superAmigo set client_encoding to 'utf-8';
alter role superAmigo set default_transaction_isolation TO 'read committed';
alter role superAmigo set timezone to 'UTC';
alter role superAmigo createdb;
grant all privileges on database macAmigo_db to superAmigo;
\q
EOF

# Remove old migrations
#rm -r ToDoListMiniApp/migrations >> /dev/null