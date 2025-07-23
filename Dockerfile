From python:3.13 
Workdir /app
copy . .
Run pip install uv
Run uv pip install --system -r requirements.txt

Cmd ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
