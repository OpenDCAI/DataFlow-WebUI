# DataFlow WebUI Backend

# Installation
For Linux, please install the requirements needed.
```
pip install -r requirements.txt
```

## Quick Start 

Start backend serving:
```bash
# If you have installed make on your machine
make dev

# Otherwise, use this command directly. 
uvicorn app.main:app --reload --port 8000  --reload-dir app --host=0.0.0.0
```
