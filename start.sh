export FAST_APP=src.app:create_app
uvicorn --host 0.0.0.0 --port 8000 src.app:create_app
