
FROM golang:alpine AS builder
RUN apk add --no-cache git
RUN go install github.com/m-lab/ndt7-client-go/cmd/ndt7-client@latest


FROM python:3.11-alpine
RUN apk add --no-cache curl bash


COPY --from=builder /go/bin/ndt7-client /usr/local/bin/ndt7-client
RUN chmod +x /usr/local/bin/ndt7-client

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
COPY ./templates /code/templates
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]