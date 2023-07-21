FROM apache/airflow:2.6.2-python3.11
COPY ./requirements.txt ./requirements.txt
COPY datos /opt/airflow/datos
RUN pip install -r ./requirements.txt