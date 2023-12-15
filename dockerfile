FROM python:3.11.2

COPY requirements.txt /app/requirements.txt

WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ARG FTP_USER
ARG FTP_PASSWORD
ARG sender_email
ARG sender_password
ARG redis
ENV FTP_USER=$FTP_USER
ENV FTP_PASSWORD=$FTP_PASSWORD
ENV sender_email=$sender_email
ENV sender_password=$sender_password
ENV redis=$redis

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run", "--host=0.0.0.0"]
