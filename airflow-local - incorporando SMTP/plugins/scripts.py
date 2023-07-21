#Scripts dependecy
import pandas as pd
import os
import dotenv
import redshift_connector
import requests
from bs4 import BeautifulSoup
import numpy as np
import awswrangler as wr
###################### incorporamos lo necesario para el envío de mails
import smtplib
#from email import message
from email.mime.text import MIMEText
###################### incorporo para la prueba en postgre
'''import psycopg2
from io import StringIO 
import csv'''
######################

def extraer_copa_mundo(ti):
    url = 'https://es.wikipedia.org/wiki/Copa_Mundial_de_F%C3%BAtbol_de_2022'
    # en la tabla ya quedo cargado el 2018
    # url='https://es.wikipedia.org/wiki/Copa_Mundial_de_F%C3%BAtbol_de_2018'

    # Lee los datos de la página para obtener los resultados de la fase de grupos
    # #filtranndo por aquellos df con columna dif
    dfs = pd.read_html(url, match='Dif')

    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, 'html.parser')
    titulo = None  # Inicializar la variable 'titulo'
    for title in soup.find_all('title'):
        titulo = title.get_text()
    titulo = titulo.replace(' - Wikipedia, la enciclopedia libre', '')
    titulo = int(titulo.replace('Copa Mundial de Fútbol de ', ''))
    print(titulo)

    dffg = pd.DataFrame()

    for df in dfs:
        try:
            if (df.columns == ['Selección', 'Pts', 'PJ', 'PG', 'PE', 'PP', 'GF', 'GC', 'Dif']).all():
                for i in range(len(df.index)):
                    list_item = []
                    for j in range(9):
                        if type(list(df.iloc[i])[j]) is np.int64:
                            list_item.append(list(df.iloc[i])[j].item())
                        elif type(list(df.iloc[i])[j]) is np.float64:
                            list_item.append(list(df.iloc[i])[j].item())
                        else:
                            list_item.append(list(df.iloc[i])[j])
                    dffg = pd.concat([dffg, pd.DataFrame([list_item])], ignore_index=True)

        except ValueError:
            pass

    dffg = dffg.assign(copa_del_mundo=titulo)

    dffg.rename(columns={dffg.columns[0]: 'Selección',
                         dffg.columns[1]: 'Pts',
                         dffg.columns[2]: 'PJ',
                         dffg.columns[3]: 'PG',
                         dffg.columns[4]: 'PE',
                         dffg.columns[5]: 'PP',
                         dffg.columns[6]: 'GF',
                         dffg.columns[7]: 'GC',
                         dffg.columns[8]: 'Dif',
                         dffg.columns[9]: 'copa_del_mundo'}, inplace=True)
    path = 'dffg.csv'
    dffg.to_csv(path,index=False,sep=';',encoding ='utf-8')
    ti.xcom_push(key="extraer_copa_mundo", value=path)


def extraer_ranking(ti):
    url2 = 'https://es.wikipedia.org/wiki/Anexo:Estad%C3%ADsticas_de_la_clasificaci%C3%B3n_mundial_de_la_FIFA'
    fifadfs = pd.read_html(url2, na_values='$Null$')
    fifadf = pd.DataFrame()

    for fifadf in fifadfs:
        try:
            if (fifadf.columns == ['Pos.', 'V', 'Selección', 'Continente', 'Confederación', 'Total puntos']).all():
                print(fifadf)
                break
        except ValueError:
            pass
    path = 'fifadf.csv'
    fifadf.to_csv(path,index=False,sep=';',encoding ='utf-8')
    ti.xcom_push(key="data_ranking", value=path)


def transformar(ti):
    # Pull data from stack
    path_fifadf = ti.xcom_pull(key="data_ranking",task_ids='extraer_ranking')
    path_dffg = ti.xcom_pull(key="extraer_copa_mundo",task_ids='extraer_copa_mundo')
    fifadf = pd.read_csv(path_fifadf ,sep=';')
    dffg = pd.read_csv(path_dffg ,sep=';')

    print(fifadf)
    print(dffg)
    print("---------------")
    # Merge data
    dffg_fifa_t = pd.merge(dffg, fifadf, on='Selección', how='left')
    dffg_fifa = dffg_fifa_t[
        ['Selección', 'Pts', 'PJ', 'PG', 'PE', 'PP', 'GF', 'GC', 'Dif', 'copa_del_mundo', 'Pos.', 'Continente',
         'Confederación', 'Total puntos']].dropna().sort_values(by=['Pos.'], ignore_index=True)
    # Check dupliate
    cheqdup = dffg_fifa.drop_duplicates()
    if len(cheqdup) == len(dffg_fifa):
        print("Sin duplicados")
    else:
        print("Es necesario remover duplicados")
    print(dffg_fifa)
    path = 'dffg_fifa.csv'
    dffg_fifa.to_csv(path,index=False,sep=';',encoding ='utf-8')
    ti.xcom_push(key="result", value=path)


def cargar(ti):
    ######################################
    ####  Create table if not exist ' ####
    #######################################
    # extract env
    dotenv.load_dotenv()
    ##########################################REDSHIFT###################################################
    usuario = os.getenv('User')
    passwd = os.getenv('Password')
    host = os.getenv('host')
    database = os.getenv('db')
    my_schema = os.getenv('my_schema')
    # Connect db
    conn = redshift_connector.connect(
        host=host,
        database=database,
        port=5439,
        user=usuario,
        password=passwd
    )
    conn.rollback()
    conn.autocommit = True
    # Create table
    cursor = conn.cursor()
    my_schema = os.getenv('my_schema')
    cursor.execute(
        f'CREATE TABLE if not exists {my_schema}.faseDeGruposMundial(Selección VARCHAR(30),'
        f' Pts INT, PJ INT, PG INT, PE INT, PP INT, GF INT, GC INT, Dif VARCHAR(5),copa_del_mundo INT,'
        f'Posición_Fifa float, Continente VARCHAR(30), Confederación VARCHAR(30), Total_puntos_fifa float) '
        f'DISTKEY(Selección) SORTKEY(Selección, Posición_Fifa,copa_del_mundo)')
    
    ##### postgre prueba####
    '''username = os.getenv('POSTGRES_USER')
    passwd = os.getenv('POSTGRES_PASSWORD')
    hostname = os.getenv('POSTGRES_HOST')
    database = os.getenv('POSTGRES_DB')
    my_schema = os.getenv('POSTGRES_SCHEMA')
    port = os.getenv('POSTGRES_PORT')
    conn = psycopg2.connect(host=hostname, dbname=database, user=username, password=passwd, port=port)

    conn.rollback() 
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f'CREATE SCHEMA if not exists {my_schema}')
    cursor.execute(f'CREATE TABLE if not exists {my_schema}.fdg_psy (Selección VARCHAR(30), Pts INT, PJ INT, PG INT, PE INT, PP INT, GF INT, GC INT, Dif VARCHAR(5),Posición_Fifa float, Continente VARCHAR(30), Confederación VARCHAR(30), Total_puntos_fifa float)')'''



    ###############################
    ####  Continue with load  ####
    ###############################
    # Extraer data trasnformada dags

    path_dffg_fifa = ti.xcom_pull(key="result",task_ids='transformar')
    dffg_fifa = pd.read_csv(path_dffg_fifa ,sep=';')
    print(dffg_fifa)
    # Change type
    dffg_fifa_item = pd.DataFrame()
    
    for i in range(len(dffg_fifa.index)):
        list_item = []
        for j in range(14):
            if type(list(dffg_fifa.iloc[i])[j]) is np.int64:
                list_item.append(list(dffg_fifa.iloc[i])[j].item())
            elif type(list(dffg_fifa.iloc[i])[j]) is np.float64:
                list_item.append(list(dffg_fifa.iloc[i])[j].item())
            else:
                list_item.append(list(dffg_fifa.iloc[i])[j])
        dffg_fifa_item = pd.concat([dffg_fifa_item, pd.DataFrame([list_item])], ignore_index=True)

    dffg_fifa_item.rename(columns={dffg_fifa_item.columns[0]: 'selección',
                                   dffg_fifa_item.columns[1]: 'pts',
                                   dffg_fifa_item.columns[2]: 'pj',
                                   dffg_fifa_item.columns[3]: 'pg',
                                   dffg_fifa_item.columns[4]: 'pe',
                                   dffg_fifa_item.columns[5]: 'pp',
                                   dffg_fifa_item.columns[6]: 'gf',
                                   dffg_fifa_item.columns[7]: 'gc',
                                   dffg_fifa_item.columns[8]: 'dif',
                                   dffg_fifa_item.columns[9]: 'copa_del_mundo',
                                   dffg_fifa_item.columns[10]: 'posición_fifa',
                                   dffg_fifa_item.columns[11]: 'continente',
                                   dffg_fifa_item.columns[12]: 'confederación',
                                   dffg_fifa_item.columns[13]: 'total_puntos_fifa'}, inplace=True)

    print(dffg_fifa_item)
     ####LOAD_POSTGREPRUEBA
    '''output = StringIO()
    dffg_fifa.to_csv(output, sep=',', index = False, header = False, quoting=csv.QUOTE_NONE, escapechar='\\')
    output.getvalue()
    output.seek(0)
    try:
        cursor.copy_expert("COPY coder.fdg_psy FROM STDIN  (FORMAT 'csv', HEADER false)",output)     
    except Exception as exeption:
        raise exeption('fallo')'''
   
    ####LOAD_REDSHIFT
    try:
        wr.redshift.to_sql(df=dffg_fifa_item, con=conn, table='fasedegruposmundial', schema='federicobergada_coderhouse',
                            mode='upsert', primary_keys=['selección', 'copa_del_mundo'], use_column_names=True)
    except Exception as exeption:
        raise exeption('fallo')

    cursor.close()
    conn.close()


def enviar_limite_reintentos(context):
    task_instance = context['task_instance']
    retries = task_instance.prev_attempted_tries
    enviar_notificacion(mensaje=f'La tarea {task_instance} ha fallado y van {retries} intentos')


def enviar_error_carga(context):
    task_instance = context['task_instance']
    enviar_notificacion(mensaje=f'La carga de informacion ha sufrido errores en {task_instance}')


def enviar_exito():
    enviar_notificacion(mensaje="El ETL se ha ejecutado satisfactoriamente")


def enviar_fallo():
    enviar_notificacion(mensaje="El ETL se ha ejecutado con fallos")


def enviar_notificacion(mensaje):
    dotenv.load_dotenv()
    email_remitente = os.getenv('remitente')
    password_email = os.getenv('password_email')
    email_destinatario = os.getenv('destinatario')

    message = MIMEText(mensaje)
    message['Subject'] = 'Notificaciones Airflow - Ejecucion ETL copa del mundo'
    message['From'] = email_remitente
    message['To'] = email_destinatario

    try:
        smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
        smtpObj.starttls()
        smtpObj.login(email_remitente, password_email)
        smtpObj.sendmail(email_remitente, email_destinatario, message.as_string())
        smtpObj.quit()
        print('Exito en el envio del mail')
    except smtplib.SMTPException as exception:
        print("Error al enviar el correo:", str(exception))
        raise exception