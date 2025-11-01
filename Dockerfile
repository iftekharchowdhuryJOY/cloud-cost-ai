# ---- Base image ----
FROM python:3.12-slim

WORKDIR /app

# ---- System deps ----
RUN apt-get update && apt-get install -y build-essential python3-dev && rm -rf /var/lib/apt/lists/*

# ---- Install ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy app ----
COPY . .

# ---- Expose ports ----
EXPOSE 8080

# ---- Run both API + dashboard ----
CMD ["bash", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8080 & streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0"]
