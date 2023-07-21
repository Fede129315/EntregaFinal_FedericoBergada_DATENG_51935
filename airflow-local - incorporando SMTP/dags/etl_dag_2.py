from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import scripts


default_args = {
    'owner': 'Fede B.',
    'start_date': datetime(2023, 7, 6),
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
    'catchup':False
}

# Definición del DAG
dag = DAG(
    'etl_dag_2',
    default_args=default_args,
    description='DAG for ETL process 2',
    schedule_interval='@daily',
)

extraer_copa_mundo = PythonOperator(
    task_id='extraer_copa_mundo',
    python_callable=scripts.extraer_copa_mundo,
    dag=dag,
    on_retry_callback=scripts.enviar_limite_reintentos
)

extraer_ranking = PythonOperator(
    task_id='extraer_ranking',
    python_callable=scripts.extraer_ranking,
    dag=dag,
    on_retry_callback=scripts.enviar_limite_reintentos
)

transformar = PythonOperator(
    task_id='transformar',
    python_callable=scripts.transformar,
    dag=dag,
)

cargar = PythonOperator(
    task_id='cargar',
    python_callable=scripts.cargar,
    dag=dag,
    on_failure_callback=scripts.enviar_error_carga,
)

enviar_exito = PythonOperator(
    task_id='enviar_exito',
    python_callable=scripts.enviar_exito,
    dag=dag,
    trigger_rule='all_success'
)

enviar_fallo = PythonOperator(
    task_id='enviar_fallo',
    python_callable=scripts.enviar_fallo,
    dag=dag,
    trigger_rule='all_failed'
)



# Definición de los operadores (tareas) en el DAG   
inicio = DummyOperator(task_id='inicio', dag=dag)
fin = DummyOperator(task_id='fin', dag=dag,trigger_rule='one_success')

# Definición de las dependencias entre las tareas
inicio >>  (extraer_ranking,extraer_copa_mundo) >> transformar >> cargar >> (enviar_exito,enviar_fallo) >>  fin