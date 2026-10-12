FROM python:3.11-slim
WORKDIR /srv/app
COPY cropbima-express/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY cropbima-express ./cropbima-express
ENV PYTHONPATH=/srv/app/cropbima-express/backend PORT=8000 MOCK_MODE=false
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --app-dir /srv/app/cropbima-express/backend"]
