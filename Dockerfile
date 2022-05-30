FROM python:3.8

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY ./helpers ./helpers
COPY configs .
COPY file.json .

RUN mkdir -p /export/

ADD main_iot_export.py .

# CMD ["python", "./main_iot_export.py"]

# COPY ./export .