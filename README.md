# BotLog - CEABS

Este programa Python foi desenvolvido para automatizar a geração e organização de arquivos com base em dados provenientes de um arquivo CSV. Ele monitora alterações em um diretório específico, processa novos dados e gera arquivos de saída em um diretório de destino. Além disso, oferece uma interface gráfica para configurar caminhos e controlar a execução do programa.

## Pré-requisitos
- Python 3.x
- Bibliotecas Python: `shutil`, `pandas`, `datetime`, `os`, `time`, `watchdog`, `tkinter`, `threading`, `configparser`, `csv`

## Como usar
1. Clone o repositório ou faça o download dos arquivos.
2. Certifique-se de ter os pré-requisitos instalados.
3. Execute o script `botlog_ceabs.py`.

## Funcionalidades

### Interface Gráfica
- A interface possui duas abas: "Informações e Controle" e "Configuração".
- Na aba "Informações e Controle", você pode selecionar o tipo de produto, visualizar informações geradas pelo programa e controlar a execução.
- Na aba "Configuração", é possível definir os caminhos para a pasta CEABS e a pasta de Logs.

### Configuração
- O programa utiliza um arquivo de configuração (`config.ini`) para armazenar caminhos pré-definidos e configurações.
- Os caminhos para a pasta CEABS e a pasta de Logs podem ser configurados na aba "Configuração".
- As configurações são salvas automaticamente quando você pressiona o botão "Salvar Configurações".

### Execução Automática
- O programa monitora alterações na pasta CEABS usando a biblioteca `watchdog`.
- Quando um arquivo é modificado, o programa processa as novas linhas e gera arquivos de saída.

### Tipos de Produto
- Os arquivos gerados são categorizados de acordo com o tipo de produto selecionado na interface gráfica.
- Os caminhos para os diretórios de destino de cada tipo de produto são especificados no arquivo de configuração.

## Como Contribuir
1. Faça um fork do repositório.
2. Crie uma branch para sua contribuição (`git checkout -b feature/nova-feature`).
3. Faça suas alterações e commit (`git commit -m 'Adiciona nova feature'`).
4. Faça push para a branch (`git push origin feature/nova-feature`).
5. Abra um Pull Request.

## Observações
- Certifique-se de configurar corretamente os caminhos antes de iniciar a execução.
- O programa continua em execução até ser explicitamente interrompido.

**Aproveite o BotLog - CEABS!**

![ceabs-logs](https://github.com/marcostulliosouza/botCEABS/assets/31325472/2135d0d6-5f08-4c58-8854-9a0a0a741d4a)

