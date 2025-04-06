# BlueprintHub  
**Scaffold projects fast. Reuse any GitHub repo as a template.**  

BlueprintHub is a CLI tool that spins up project boilerplate in minutes—choose from built-in starters or import custom GitHub repos. Perfect for devs who hate setup grunt work.

## Features  
- Pre-built templates: CLI, FastAPI, Flask, Data Science.  
- Import any public GitHub repo as a reusable template.  
- Customize with interactive prompts: name, deps, Docker, CI/CD.  

## Installation  
```bash
git clone 
```
```
https://github.com/srinivassarkar/BlueprintHub.git 
```
```
cd BlueprintHub
```
```
poetry install
```

## Commands  

### 1. List Templates  
See available templates.  
```bash
poetry run python -m blueprinthub.cli list
```  
Output: Lists starters (e.g., fastapi_app) and imported templates.  
Next: Pick one to create a project.  

### 2. Create a Project  
Scaffold a project from a template.  
```bash
poetry run python -m blueprinthub.cli create <template_name> [project_dir]
```  
Example:  
```bash
poetry run python -m blueprinthub.cli create fastapi_app my-api
```  
Prompts: Project name?, Author?, Package manager?, Database?, Docker?, etc.  
Output: my-api/ with main.py, pyproject.toml, etc.  
Options:  
--dry-run: Preview without creating files.  

### 3. Import a GitHub Repo  
Turn a GitHub repo into a template.  
```bash
poetry run python -m blueprinthub.cli import <github_url>
```  
Example:  
```bash
poetry run python -m blueprinthub.cli import https://github.com/srinivassarkar/TO_DO_APP_REACT_JS.git 
```  
Prompts:  
Select files (e.g., index.html, package.json).  
Strings to templatize (e.g., to-do-app-react → name).  
Template name (e.g., git_custome_to_do_app).  
Output: New template in templates/git_custome_to_do_app/.  
Use: Run create git_custome_to_do_app my-todo to scaffold it.
  

## Demo Walkthrough  

### List Templates:  
```bash
poetry run python -m blueprinthub.cli list
```  
See fastapi_app, python_cli, etc.  

### Create a FastAPI Project:  
```bash
poetry run python -m blueprinthub.cli create fastapi_app my-api
```  
Input: my-api, seenu, poetry, PostgreSQL, y, SQLAlchemy, y, n, httpx, y.  
Check: my-api/main.py, Dockerfile.  

### Import a React App:  
```bash
poetry run python -m blueprinthub.cli import https://github.com/srinivassarkar/TO_DO_APP_REACT_JS.git 
```  
Input: Select files, to-do-app-react, seenu, 0.0.0 → name, author, version, git_custome_to_do_app, seenu, just testing.  
Check: templates/git_custome_to_do_app/.  

### Create from Imported Template:  
```bash
poetry run python -m blueprinthub.cli create git_custome_to_do_app my-todo
```  
Input: my-todo, seenu sarkar, poetry, y, y, httpx, y.  
Check: my-todo/package.json with "name": "my-todo-app-react".  

## Requirements  
- Python 3.10+  
- Poetry  
- Git  

## Next Steps  
- Test it: Run the demo commands.  
- Share templates: Zip templates/<template_name>/ for now (V2: cloud registry).  
- Feedback: Tell us what rocks or sucks!
---