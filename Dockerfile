# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV STREAMLIT_PORT=8501

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Streamlit config to avoid prompt for email
RUN mkdir -p ~/.streamlit && \
    echo "\
[server]\n\
headless = true\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
port = \$STREAMLIT_PORT\n\
\n\
[client]\n\
showErrorDetails = true\n\
\n\
" > ~/.streamlit/config.toml

# Expose Streamlit default port
EXPOSE ${STREAMLIT_PORT}

# Run Streamlit
CMD ["streamlit", "run", "your_app_file.py"]
