FROM python:3.11.2
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV FLASK_APP=py.py
ENV FLASK_RUN_HOST=0.0.0.0

ARG FTP_USER
ARG FTP_PASSWORD
ARG sender_email
ARG sender_password
ARG redis

CMD ["flask", "run", "--host=0.0.0.0"]