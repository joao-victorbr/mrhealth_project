# Use a imagem oficial do Ubuntu como base
FROM ubuntu:latest

# Mantenedor da imagem (opcional)
LABEL maintainer="MrHealth"

# Atualizar os pacotes do sistema e instalar dependências necessárias
RUN apt-get update && \
    apt-get install -y wget unzip curl git openssh-client iputils-ping

# Definir a versão do Terraform (ajuste conforme necessário)
ENV TERRAFORM_VERSION=1.9.8

# Baixar e instalar Terraform
RUN wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    mv terraform /usr/local/bin/ && \
    rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# Criar a pasta /iac como um ponto de montagem para um volume
RUN mkdir /iac
VOLUME /iac

# Criar a pasta Downloads e instalar o AWS CLI (para acessar a AWS)
RUN mkdir Downloads && \
    cd Downloads && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

# Variáveis de ambiente
ENV AWS_ACCESS_KEY_ID=substituir_chave_primaria
ENV AWS_SECRET_ACCESS_KEY=substituir_chave_privada
ENV AWS_DEFAULT_REGION=us-east-2

# Configurar credenciais AWS
RUN aws configure set aws_access_key_id AWS_ACCESS_KEY_ID && \
    aws configure set aws_secret_access_key AWS_SECRET_ACCESS_KEY && \
    aws configure set region AWS_DEFAULT_REGION

# Definir o comando padrão para execução quando o container for iniciado
CMD ["/bin/bash"]
