# Processamento

# Imports
from pyspark.sql import *
from pyspark.sql.functions import * 
from mrhealth_log import mrhealth_grava_log

from pyspark.sql import functions as f

# Tentei criar uma função para leitura de tabelas em banco. A leitura funcionou localmente em um notebook jupyter de testes, mas está comentada porque não consegui ler através do cluster EMR na AWS.
# def read_postgres(spark,TABLE):
# 	URL = "jdbc:postgresql://localhost:5432/mrhealth_db"    
# 	PROPERTIES = {
# 		"user": "postgres",                          
# 		"password": "",                       
# 		"driver": "org.postgresql.Driver"               
# }
# 	return spark.read.jdbc(url=URL, table=TABLE, properties=PROPERTIES)

# Função para limpeza e transformação
def mrhealth_limpa_transforma_dados(spark, bucket, nome_bucket, ambiente_execucao_EMR):
	
	# Define o caminho para armazenar o resultado do processamento
	path =  f"s3://mrhealth-terraform-IDCONTA/dados/silver/" if ambiente_execucao_EMR else  "dados/silver/"

	# Grava no log
	mrhealth_grava_log("Log MrHealth - Importando os dados...", bucket)

	# Carrega os arquivos CSV
	df_pedido = spark.read.csv(path+'PEDIDO.csv', header=True, inferSchema=True)
	df_item_pedido = spark.read.csv(path+'ITEM_PEDIDO.csv', header=True, inferSchema=True)

	# Grava no log
	mrhealth_grava_log("Log MrHealth - Dados Importados com Sucesso.", bucket)
	mrhealth_grava_log("Log MrHealth - Total de Pedidos: " + str(df_pedido.count()), bucket)

	# Grava no log
	mrhealth_grava_log("Log MrHealth - Verificando status de pedidos.", bucket)
	
	# Conta os registros de avaliações positivas e negativas
	count_finalized = df_pedido.where(df_pedido['Status'] == "Finalizado").count()
	count_pending = df_pedido.where(df_pedido['Status'] == "Pendente").count()
	count_canceled = df_pedido.where(df_pedido['Status'] == "Cancelado").count()
     
	# Grava no log
	mrhealth_grava_log("Log MrHealth - Existem " + str(count_finalized) + " finalizados, " + str(count_pending) + " pendentes e " + str(count_canceled) + " cancelados", bucket)

	# Início da consolidação
	df_pedido_w_itens = (
		df_pedido
		.join(df_item_pedido,'Id_Pedido')
		.withColumn('uid',f.concat_ws('-',f.col('Id_Pedido'),f.col('Id_Item_Pedido'),f.col('Data_Pedido')))
		.withColumn('ano',f.year(f.col('Data_Pedido')))
		.withColumn('mes',f.month(f.col('Data_Pedido')))
	)
	
	# Grava no log
	mrhealth_grava_log("Log MrHealth - Lendo tabelas do provenientes do banco", bucket)
	# Os 4 comentários abaixo seriam a leitura de tabelas que estão no banco. Porém, não consegui realizar isso através do cluster na AWS. Então, logo em seguida, fiz a leitura dos .csv:
	# df_estados = read_postgres(spark,'estados')
	# df_produtos = read_postgres(spark,'produtos')
	# df_paises = read_postgres(spark,'paises')
	# df_unidades = read_postgres(spark,'unidades')
	df_estados = spark.read.csv(path+'Tabela_Estado.csv', header=True, inferSchema=True)
	df_produtos = spark.read.csv(path+'Tabela_Produto.csv', header=True, inferSchema=True)
	df_paises = spark.read.csv(path+'Tabela_Pais.csv', header=True, inferSchema=True)
	df_unidades = spark.read.csv(path+'Tabela_Unidade.csv', header=True, inferSchema=True)

	# Grava no log
	mrhealth_grava_log("Log MrHealth - Salvar tabelas em parquet na camada silver", bucket)
	try:
		df_estados.write.mode("Overwrite").partitionBy("id_pais").parquet(path)
		df_produtos.write.mode("Overwrite").partitionBy("id_produto").parquet(path)
		df_paises.write.mode("Overwrite").partitionBy("id_pais").parquet(path)
		df_unidades.write.mode("Overwrite").partitionBy("id_estado").parquet(path)
	except:
		df_estados.write.partitionBy("id_pais").parquet(path)
		df_produtos.write.partitionBy("id_produto").parquet(path)
		df_paises.write.partitionBy("id_pais").parquet(path)
		df_unidades.write.partitionBy("id_estado").parquet(path)

	# Grava no log
	mrhealth_grava_log("Log MrHealth - Transformando os Dados", bucket)

	# Dataframe consolidado:
	df_consolidado = (
		df_pedido_w_itens
		.join(df_produtos.withColumnRenamed('id_produto','Id_Produto'),'Id_Produto')
		.join(df_unidades.withColumnRenamed('id_unidade','Id_Unidade'),'Id_Unidade')
		.join(df_estados,'id_estado')
		.join(df_paises,'id_pais')
		.drop('id_pais','id_estado','id_Unidade','Id_Produto','Id_Pedido','Id_Item_Pedido')
	)
	df_consolidado_tratado = (
		df_consolidado
		.withColumnRenamed('Tipo_Pedido','Forma de venda')
		.withColumnRenamed('Data_Pedido','Data')
		.withColumnRenamed('Vlr_Pedido','Valor do pedido')
		.withColumnRenamed('Endereco Entrega','Endereço de entraega')
		.withColumnRenamed('Taxa_Entrega','Taxa de entrega')
		.withColumnRenamed('Qtd','Quantidade do item')
		.withColumnRenamed('Vlr_Item','Valor do item')
		.withColumnRenamed('ano','Ano')
		.withColumnRenamed('mes','Mês')
		.withColumnRenamed('nome_produto','Produto')
		.withColumnRenamed('nome_unidade','Filial')
		.withColumnRenamed('nome_estado','Estado')
		.withColumnRenamed('nome_pais','País')
		.withColumn('Valor do item',f.round('Valor do item',2))
		.withColumn('Taxa de entrega',f.round('Taxa de entrega',2))
		.withColumn('Valor do item',f.round('Valor do item',2))
	)
	df_consolidado_tratado = df_consolidado_tratado.select([df_consolidado_tratado.uid] + df_consolidado_tratado.columns[:])

	# Grava no log
	mrhealth_grava_log("Log MrHealth - Gerando tabelas com insights", bucket)

	df_vendas_produtos_global = (
		df_consolidado_tratado.groupBy('Produto').sum('Quantidade do item','Valor do item')
		.withColumnRenamed('sum(Quantidade do item)','Total vendido')
		.withColumnRenamed('sum(Valor do item)','Receita (R$)')
		.orderBy(f.desc('Total vendido'))
	)

	df_vendas_pais = (
		df_consolidado_tratado.groupBy('País')
		.agg(f.count('*').alias('Vendas'), f.round(f.sum('Valor do pedido'),2).alias('Receita (R$)'))
	)

	df_vendas_ano = (
		df_consolidado_tratado.groupBy('Ano', 'Filial', 'País')
		.agg(
			f.count('*').alias('Vendas'),
			f.round(f.sum('Valor do pedido'), 2).alias('Receita (R$)')
		)
		.orderBy(f.desc('Ano'),f.desc('Receita (R$)'))
	)

	# Grava no log
	mrhealth_grava_log("Log MrHealth - Salvando os insights na camada gold do S3.", bucket)

	path_gold = f"s3://mrhealth-terraform-IDCONTA/dados/gold/" if ambiente_execucao_EMR else  "dados/gold/"
	df_vendas_produtos_global.write.mode("Overwrite").partitionBy("Status").parquet(path_gold)
	df_vendas_pais.write.mode("Overwrite").partitionBy("Status").parquet(path_gold)
	df_vendas_ano.write.mode("Overwrite").partitionBy("Status").parquet(path_gold)
	df_consolidado_tratado.write.mode("Overwrite").partitionBy("Status").parquet(path)

	return df_vendas_produtos_global,df_vendas_pais,df_vendas_ano,df_consolidado_tratado


	