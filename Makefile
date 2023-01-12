
setup:
	pip install --upgrade pip
	pip install -r requirements.txt
	sqlite3 tables.db < tables.sql
db:
	sqlite3 tables.db < tables.sql
start:
	python3 app.py