FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Train the model at build time so risk_model.pkl is ready when the
# container starts. If attendance_history.csv changes later, rebuild
# the image (or call POST /refresh after replacing the CSV at runtime).
RUN python train_model.py

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
