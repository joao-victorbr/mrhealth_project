# Projeto MrHealth
(projeto em andamento)

Esse projeto consiste em prover uma infraestrutura de cloud computing para a empresa fictícia Mr. Health. 

### Contexto:
A Mr. Health é uma empresa de Slow-Food que está em busca de escalar seu negócio e necessita ter as informações para tomada de decisão de forma mais rápida. Dessa maneira, poderá adotar modelos estatísticos para gestão dos estoques de suas unidades.

Atualmente, cada unidade envia as informações, toda a meia noite, sobre o fechamento das vendas diárias (D-1). Arquivos com dados de vendas são gerados em formato CSV de forma manual.
A empresa deseja consolidadar os dados de maneira automática ao serem recebidos, permitindo possam se concentrar na análise destas informações e na tomada de ações junto aos fornecedores e gestores das unidades. Além disso, desejam que o sistema tenha algum tipo de inteligência que gere alertas ou recomendações de forma automática.

### Solução proposta:
A proposta de solução será a seguinte: a infraestrutura de cloud computing será implementada no provedor Amazon Web Services (AWS). O diagrama abaixo ilustra como toda a pipeline de dados ocorre:
![image](https://github.com/user-attachments/assets/38f58aa4-55b6-4710-9f5b-c7726b4010db)
Legenda:

(1) A primeira etapa realiza o fluxo de IaC (infraestrutura como código). Terraform e Docker são utilizados para enviar os dados dos arquivos .csv e do banco da empresa para as buckets no Amazon S3. Além disso, a etapada também cria o 

(2) Buckets no serviço Amazon S3. A camada Silver contém os arquivos `.csv` com dados não transformados. A proposta futura é carregá-los nesse diretório em formato parquet a fim de otimizar o processamento distribuído.
Há duas buckets para o projeto:
![image](https://github.com/user-attachments/assets/c8e9e6af-8c4c-4eef-b52f-5bd74852d5f6)
Onde: 
- `mrhealth-terraform-471112908139` é destinada para armazenar os dados das camadas silver, gold e arquivo de estado do terraform;
- `mrhealth-471112908139` destinada para armazenar os código .py da pipeline e demais arquivos necessários para o cluster. Esta bucket é apagada com a destruição do cluster via terraform.

(3) Cluster do Elastic Map Reduce da AWS. O cluster recebe os jobs provenientes da bucket no S3, executa as transformações dos dados e escreve arquivos parquet na bucket da camada Gold. 

(4) Camada Gold está localizada em `terraform-471112908139/dados/gold`, que contém os arquivos parquet com dados transformados e consolidados. Os arquivos apresentam métricas de negócios, como total de vendas e receita por ano, filial da empresa e maiores receitas por produto. Os dados da camada Gold servirão de entrada para os dashboards no serviço Amazon Quicksight.

(5) Serviço de analytics para a MrHealth verificar métricas relevantes de vendas.

### Observações:
- No momento, ainda não foi possível desenvolver a conexão entre o banco no PostgreSQL e a bucket no Amazon S3. Para que o projeto não siga adiante, os dados dos bancos foram transformados em arquivos `.csv` e carregados na bucket.
- Ainda não foi possível desenvolver o dashboard com métricas de vendas no Amazon Quicksight. Contudo, os arquivos parquet estão prontos para uso e estão localizados na bucket (endereço: `mrhealth-terraform-471112908139/dados/gold`

### Organização dos arquivos de projeto:
O projeto foi organizado em pastas e módulos. 

![image](https://github.com/user-attachments/assets/9eb05962-5546-4a2f-a146-e9efc565bf16)
- Pasta scripts: contém um script .sh que irá instalar o interpretador da linguagem python no cluster EMR.
- Pasta pipeline: contém os aruqivos .py da pipeline e de gravação de logs.
- Pasta modules: arquivos do terraform para a criação de recursos dos serviços EMR, IAM e S3 na AWS
  
![image](https://github.com/user-attachments/assets/69120270-5fb0-4847-b6c6-177154911771)
- Pasta dados: como o nome sugere, são os dados de entrada da pipeline. Há também um arquivo .jar utilizado para testes de leitura dos dados em banco que a empresa possui

### Execução:
1) É necessário ter o Docker instalado e possuir uma conta na AWS.
2) Por questão de segurança, as chaves de acesso à AWS não estão nos arquivos versionados. Dessa forma, é necessário fazer as substituições:
- Substituir as duas chaves de acesso no Dockerfile em "Variáveis de ambiente"
- Substituir IDCONTA pelo id da conta da aws nos arquivos:
  - mrhealth_project/IaC/config.tf
  - mrhealth_project/IaC/terraform.tfvars
  - mrhealth_project/IaC/modules/s3/s3_objects/main.tf
  - mrhealth_project/IaC/pipeline/mrhealth_processamento.py
  - mrhealth_project/IaC/pipeline/projeto2.py
3) Abra o Docker e o terminal.
4) No terminal, onde foi feito o clone do repositório, vá até a pasta onde está o Dockerfile e execute o comando:
`docker build -t mrhealth-terraform-image . && docker run -dit --name mrhealth -v ./IaC:/iac mrhealth-terraform-image /bin/bash`
O comando criará a imagem e o container no docker.
5) Abra o terminal do container docker criado e execute:
`terraform init && terraform apply --auto-approve`
Após a criação da infra ser completada, o fluxo de transformação e carregamentos de dados será feito.
6) Observe quando o cluster for finalizado na interface do Amazon EMR: `https://us-east-2.console.aws.amazon.com/emr/home?region=us-east-2#/clusters`
7) Para finalizar a infra, execute o comando no terminal do container Docker:
`terraform destroy --auto-approve`

### Propostas futuras:
- Implementar a etapa 5 com o serviço Amazon Quicksight
- Carregar dados do banco diretamente na bucket do Amazon S3
- Integrar o serviço do Amazon Simple Notification Service (SNS), que notificará os usuários quando a pipeline finalizar, seja com erro ou não.
- Automatizar a criação da infra e execução da pipeline todos os dias à meia-noite




