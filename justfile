go:
	uv run uvicorn dependency_agent.web:app --reload

test:
	uv run pytest

analyse:
	uv run dependency-agent analyse maven/demo-app/pom_that_do_not_work.xml

mvn1:
	cd maven/demo-app && mvn clean install

mvnbroken1:
	cd maven/demo-app && mvn -f pom_that_do_not_work.xml clean install
