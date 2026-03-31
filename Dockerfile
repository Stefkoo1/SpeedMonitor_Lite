FROM python:3.11-alpine
RUN apk add --no-cache curl bash

# Wir laden die Binärdatei direkt (kein entpacken nötig!)
RUN curl -L -o /usr/local/bin/ndt7-client https://github.com/m-lab/ndt7-client-go/releases/download/v0.7.0/ndt7-client-go_0.7.0_linux_amd64 && \
    chmod +x /usr/local/bin/ndt7-client

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
COPY ./templates /code/templates
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]