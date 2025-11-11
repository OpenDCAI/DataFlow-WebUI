.PHONY: dev test fmt lint

dev:
	uvicorn app.main:app --reload --port 8000  --reload-dir app

# 用默认浏览器打开文档页面
	
doc:
	@echo "Opening http://localhost:8000/docs ..."
	@python -c "import webbrowser; webbrowser.open('http://localhost:8000/docs')"

test:
	pytest -q

fmt:
	trufflehog || true
	trufflehog --version || true
	trufflehog --fix .
	black .
	isort .

lint:
	trufflehog check .
	flake8
	mypy .
