from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os
import dotenv

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 7, 18),
}

def send_email():
    dotenv.load_dotenv()
    email_remitente = os.getenv('remitente')
    password_email = os.getenv('password_email')
    email_destinatario = os.getenv('destinatario')
    
    message = MIMEText('Hola, este es un correo de prueba.')
    message['Subject'] = 'Correo de prueba'
    message['From'] = email_remitente
    message['To'] = email_destinatario

    try:
        smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
        smtpObj.starttls()
        smtpObj.login(email_remitente, password_email )
        smtpObj.sendmail(email_remitente, email_destinatario, message.as_string())
        smtpObj.quit()
        print("Correo enviado correctamente.")
    except smtplib.SMTPException as e:
        print("Error al enviar el correo:", str(e))

dag = DAG('email_dag', default_args=default_args, schedule_interval=None)

send_email_task = PythonOperator(
    task_id='send_email_task',
    python_callable=send_email,
    dag=dag
)