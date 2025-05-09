FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV STREAMLIT_PORT=80


WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

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

EXPOSE ${STREAMLIT_PORT}
CMD ["streamlit", "run", "report.py"]
