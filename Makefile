install:
	@pip install -e .

clean:
	@rm -f */version.txt
	@rm -f .coverage
	@rm -rf */.ipynb_checkpoints
	@rm -Rf build
	@rm -Rf */__pycache__
	@rm -Rf */*.pyc
	@echo "🧽 Cleaned up successfully!"

all: install clean

test:
	@pytest -v tests

# Specify package name
lint:
	@black xeroconvert/

app:
	@streamlit run xeroconvert/app.py

app2:
	@streamlit run xeroconvert/app2.py

git_merge:
	$(MAKE) clean
	@python xeroconvert/auto_git/git_merge.py

git_push:
	$(MAKE) clean
	@python xeroconvert/auto_git/git_push.py
