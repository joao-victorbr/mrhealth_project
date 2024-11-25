# Script Principal

# Instala pacote Python dentro de código Python
import subprocess
comando = "pip install boto3"
subprocess.run(comando.split())

# Imports
import os
import boto3
import traceback
import pyspark 
from pyspark.sql import SparkSession
from mrhealth_log import mrhealth_grava_log
from mrhealth_processamento import mrhealth_limpa_transforma_dados

# Nome do Bucket
NOME_BUCKET = "mrhealth-IDCONTA"

# Chaves de acesso à AWS
AWSACCESSKEYID = "AKIAW3MEEPVV7TPKNM5U"
AWSSECRETKEY = "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"

print("\nLog MrHealth - Inicializando o Processamento.")

# Cria um recurso de acesso ao S3 via código Python
s3_resource = boto3.resource('s3', aws_access_key_id = AWSACCESSKEYID, aws_secret_access_key = AWSSECRETKEY)

# Define o objeto de acesso ao bucket via Python
bucket = s3_resource.Bucket(NOME_BUCKET)

# Grava o log
mrhealth_grava_log("Log MrHealth - Bucket Encontrado.", bucket)

# Grava o log
mrhealth_grava_log("Log MrHealth - Inicializando o Apache Spark.", bucket)

# Cria a Spark Session e grava o log no caso de erro
try:
	spark = SparkSession.builder.appName("MrHealth").config("spark.jars", "/home/joao-vicbr/mrhealth_project/data/postgresql-42.7.4.jar").getOrCreate()
	spark.sparkContext.setLogLevel("ERROR")
except:
	mrhealth_grava_log("Log MrHealth - Ocorreu uma falha na Inicializacao do Spark", bucket)
	mrhealth_grava_log(traceback.format_exc(), bucket)
	raise Exception(traceback.format_exc())

# Grava o log
mrhealth_grava_log("Log MrHealth - Spark Inicializado.", bucket)

# Define o ambiente de execução do Amazon EMR
ambiente_execucao_EMR = False if os.path.isdir('dados/') else True

# Bloco de limpeza e transformação
try:
	df_vendas_produtos_global,df_vendas_pais,df_vendas_ano,df_consolidado_tratado = mrhealth_limpa_transforma_dados(spark, 
																							  bucket, 
																							  NOME_BUCKET, 
																							  ambiente_execucao_EMR)
except:
	mrhealth_grava_log("Log MrHealth - Ocorreu uma falha na limpeza e transformacao dos dados", bucket)
	mrhealth_grava_log(traceback.format_exc(), bucket)
	spark.stop()
	raise Exception(traceback.format_exc())

# Grava o log
mrhealth_grava_log("Log MrHealth - Modelos Criados e Salvos no S3.", bucket)

# Grava o log
mrhealth_grava_log("Log MrHealth - Processamento Finalizado com Sucesso.", bucket)

# Finaliza o Spark (encerra o cluster EMR)
spark.stop()



