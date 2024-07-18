dev:
	poetry run python manage.py runserver
create-migrations:
	poetry run python manage.py makemigrations
migrate:
	poetry run python manage.py migrate
check-lib:
	poetry run python3 check_dependencies.py
install: check-lib
	poetry install --no-root