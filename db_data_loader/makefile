.PHONY: install clean_db import_cities

# Set up your environment
install:
	pip install -r requirements.txt

# Clean the cities table
clean_db:
	psql -U postgres -d trud -c "DROP TABLE IF EXISTS cities;"

# Import cities from the CSV
import_cities: clean_db
	python cities_import.py