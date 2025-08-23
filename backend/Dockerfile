FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# Install uv package manager
RUN pip install uv

# Install dependencies using uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

COPY . .

# Expose the port the app runs on
EXPOSE 8000