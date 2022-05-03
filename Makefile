
env-create: env-destroy
	@printf "Criando ambiente virtual... "
	@virtualenv -q venv -p python3.8
	@echo "OK"

env-destroy:
	@printf "Destruindo ambiente virtual... "
	@rm -rfd venv
	@echo "OK"

packages:
	@printf "Instalando bibliotecas..."
	@venv/bin/pip install -q --no-cache-dir -r requirements.txt
	@echo "OK"

folders:
	@printf "Criando pastas..."
	@mkdir models
	@echo "OK"


install: env-create packages folders

run:
	@python ./game.py