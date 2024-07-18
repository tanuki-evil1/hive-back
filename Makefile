dev:
	poetry run python3 manage.py runserver
create-migrations:
	poetry run python3 manage.py makemigrations
migrate:
	poetry run python3 manage.py migrate
check-lib:
	poetry run python3 check_dependencies.py
install: check-lib
	poetry install --no-root