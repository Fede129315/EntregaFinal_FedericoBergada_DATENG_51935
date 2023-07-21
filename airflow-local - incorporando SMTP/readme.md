__Para poder ejectutar las pruebas:__    
1. En el directorio "AIRFLOW-LOCAL - INCORPORANDO SMTP" colocar un archivo .env con las credenciales aportadas (para el caso de windows).
2. Colocar en el directorio principal un archivo con el nombre "airflow.cfg" que incluya el contenido que se dio cómo ejemplo en la clase 11 (https://github.com/lucastrubiano/dateng_coder/blob/master/Semana_11/Video5_Airflow_cfg/airflow.cfg).
3. Editar los siguientes parámetros: 
~~~
    -min_file_process_interval = 0 
    -dag_dir_list_interval = 60 
    -smtp_host = smtp.gmail.com 
    -smtp_user = remitente@gmail.com # mail del remitente 
    -smtp_password = contraseñadeaplicación # ver https://support.google.com/mail/answer/185833?hl=es-419 
    -smtp_port = 587 
    -smtp_mail_from = remitente@gmail.com 
~~~

4. Crear ".env" dentro del directorio plugins con las credenciales de Redshift y las variables correspondiente a remitente, contraseña de aplicación y destinatario(usar los nombres de variables que fueron adjuntados con la entrega).
5. Correr el siguiente comando parado en la carpeta principal donde se encuentra el docker-compose.
~~~
docker-compose up airflow-init
~~~
6. Una vez finalizado, correr el siguiente comando parado en la carpeta principal donde se encuentra el docker-compose. 
~~~
docker-compose build
~~~
7. Una vez finalizado, correr el siguiente comando parado en la carpeta principal donde se encuentra el docker-compose.
~~~
docker-compose up
~~~
8. Desde un explorador, abrir http://localhost:8080/ y colocar credenciales para acceder.
9. Ejecutar el Dag  "etl_dag_2".

### COMENTARIOS SOBRE EL USO DE ALERTAS
1. las task **extraer_copa_mundo** y **extraer_ranking** mediante el paremetro **on_retry_callback** llaman en caso de retry a la funcion **enviar_limite_reintentos** que envia notificación por mail utilizando la función **enviar_notificacion**.
2. la task **cargar** mediante el parametro **on_failure_callback** llama en caso de fallo a la función enviar_error_carga que envia notificación por mail utilizando la función **enviar_notificacion**.
3. Una vez finalizado el proceso de ETL en caso de que todas las tareas hayan sido ejecutadas en forma satisfactoria en se envia un mail llamando a la función **enviar_exito** que envia notificación por mail utilizando la función **enviar_notificacion**. En cambio si fueron ejecutadas en forma fallida se envía un mail llamando a al función **enviar_fallo** que envia notificación por mail utilizando la función **enviar_notificacion**.
