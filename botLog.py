import shutil
import pandas as pd
from datetime import datetime, timedelta
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox
import threading
import configparser
import csv
import logging

"""
v 2.0.1

- Separado os logs em função da jiga.
- Adicionado falhas especifica por jiga.
- Retirado a opção de produto e deixado opção da dt da jiga
- Melhorado o desempenho do monitoramento da pasta para verificar se trocou o dia após meia noite

"""

"""

v 2.2.0

- Adicionado novo produto
- Criado interface para alternar entre produto

"""

"""

v 3.0.0

- Adicionado novas jigas

"""

"""

v 3.0.1
25/07/24
- Otimizado o código 
- Adicionado uma caixa de pergunta para salvar logs de placas reprovadas

"""

"""

v 4.0.0 
25/07/24
- Adicionado a jiga 1004

"""

"""
V4.1.0
18/09/24
- Melhorado a lógica para garantir que se a placa não apresenta falha não deve ser gerado
o questionamento se deseja retestar a plata
- Adicionado nos logs data e hora para melhor analise.
- Otimizado a questão de trocar o dia meia noite.
"""
__version__ = '4.1.0'
# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


class MyApp:
    def __init__(self, root):
        self.root = root
        root.iconbitmap(default='ico-botlog.ico')
        self.root.title("BotLog - CEABS " + __version__)
        self.root.geometry("850x450")
        self.running_flag = False  # Adiciona uma nova variável de controle para o loop
        self.programa_em_execucao = False

        # Configuração dos caminhos pré-definidos
        self.config = self.load_config()

        self.origem_path = self.config.get('Paths', 'source_path', fallback="C:/")
        self.controle_path = os.path.dirname(os.path.realpath(__file__))

        # Inicializar as variáveis para a aba 1
        self.ultima_posicao = 0
        self.programa_em_execucao = False

        # Variáveis para armazenar os widgets Entry na aba de configurações
        self.entry_origem = None
        self.entry_destino = None

        # Variável para armazenar o widget Text na aba de informações
        self.info_text = None

        # Variável de instância para o botão Executar
        self.button_executar = None

        self.entry_tipo_jiga = None
        self.jigas = self.loadJigas()

        self.produtos = self.loadProduto()

        # Criação da interface gráfica
        self.create_tabs()

        self.iniciar_arquivo_controle()

    def loadProduto(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        return dict(config.items('PRODUTO'))

    def loadJigas(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        return dict(config.items('DT-JIGA'))

    def iniciar_arquivo_controle(self):
        caminho_arquivo_controle = os.path.join(self.controle_path, 'controlposition.txt')
        if not os.path.exists(caminho_arquivo_controle):
            with open(caminho_arquivo_controle, 'w') as f:
                f.write('0')

    def load_config(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        return config

    def save_config(self):
        self.config.set('Paths', 'source_path', self.origem_path)

        with open('config.ini', 'w') as config_file:
            self.config.write(config_file)

    def create_tabs(self):
        # Aba 1: Informações e Controle
        tab_control = ttk.Notebook(self.root)
        tab1 = ttk.Frame(tab_control)
        tab2 = ttk.Frame(tab_control)
        tab_control.add(tab1, text='Informações e Controle')
        tab_control.add(tab2, text='Configuração')

        # Adiciona um widget Combobox para selecionar o tipo de jiga
        labelComboboxProduto = tk.Label(tab1, text='Produto:')
        labelComboboxProduto.pack(pady=10)

        produtoDisponivel = [produto for produto in self.produtos.keys()]
        self.entry_tipo_produto = ttk.Combobox(tab1, values=produtoDisponivel, state="readonly", width=20)

        self.entry_tipo_produto.set(produtoDisponivel[0])
        self.entry_tipo_produto.pack(pady=5)

        # Adiciona um widget Combobox para selecionar o tipo de jiga
        labelComboboxJiga = tk.Label(tab1, text='DT-JIGA:')
        labelComboboxJiga.pack(pady=10)

        jigaDisponivel = [jiga for jiga in self.jigas.keys()]
        self.entry_tipo_jiga = ttk.Combobox(tab1, values=jigaDisponivel, state="readonly", width=20)

        self.entry_tipo_jiga.set(jigaDisponivel[0])
        self.entry_tipo_jiga.pack(pady=5)

        # Aba 1: Informações e Controle
        label_info = tk.Label(tab1, text="Informações geradas pelo programa:")
        label_info.pack(pady=10)

        # Adiciona um widget Text para exibir informações
        self.info_text = tk.Text(tab1, height=10, width=100)
        self.info_text.pack(pady=10)

        self.button_executar = tk.Button(tab1, text="Executar", command=self.executar_programa)
        self.button_executar.pack(padx=10, pady=10)

        # Aba 2: Configurações
        label_config = tk.Label(tab2, text="Definir Local Arquivo Gerado pelo Software CEABS")
        label_config.grid(row=0, column=0, pady=10, sticky=tk.W)
        label_origem = tk.Label(tab2, text='Pasta CEABS: ')
        label_origem.grid(row=1, column=0, pady=10, sticky=tk.W)

        # Adicionando campos de entrada para configurar os caminhos
        self.entry_origem = tk.Entry(tab2, width=40)
        self.entry_origem.insert(0, self.origem_path)
        self.entry_origem.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)

        # Botão para abrir caixa de diálogo para selecionar novo caminho
        button_selecionar_origem = tk.Button(tab2, text="Local", command=self.selecionar_origem)
        button_selecionar_origem.grid(row=1, column=2, pady=5, padx=5, sticky=tk.W)

        # Botão para salvar configurações
        button_salvar_config = tk.Button(tab2, text="Salvar Configuração", command=self.salvar_configuracoes)
        button_salvar_config.grid(row=5, column=1, pady=10, sticky=tk.W)

        # Adiciona as abas à janela
        tab_control.pack(expand=1, fill="both")

        # Atualiza o destino_path quando um novo produto é selecionado
        self.entry_tipo_produto.bind("<<ComboboxSelected>>", self.atualizar_destino_path)

    def atualizar_destino_path(self, event):
        produto_selecionado = self.entry_tipo_produto.get()
        if produto_selecionado in self.produtos:
            self.destino_path = self.produtos[produto_selecionado]
        else:
            messagebox.showerror("Produto não encontrado",
                                 "O produto selecionado não foi encontrado no arquivo de configuração.")

    def atualizar_caminho_arquivo(self):
        # Atualiza o caminho do arquivo com base na data atual
        global caminho_arquivo_original
        caminho_arquivo_original = obter_caminho_arquivo_original()

    def executar_programa(self):
        self.atualizar_caminho_arquivo()  # Chama a função dentro do contexto da instância
        if caminho_arquivo_original:
            if caminho_arquivo_original != self.config.get('Paths', 'last_source_file', fallback=None):
                limpar_ultima_posicao_lida()
                self.config.set('Paths', 'last_source_file', caminho_arquivo_original)
                self.save_config()

            if not self.programa_em_execucao:
                self.adicionar_info("Programa em execução...")
                self.programa_em_execucao = True
                self.atualizar_estado_botoes()  # Atualiza o estado dos botões

                self.running_flag = True  # Inicia o loop

                # Desativa o widget de combobox
                self.entry_tipo_produto.config(state="disabled")
                self.entry_tipo_jiga.config(state="disabled")

                # Inicia um thread separado para executar o loop continuamente
                self.thread_execucao = threading.Thread(target=self.executar_continuamente, daemon=True).start()
        else:
            messagebox.showerror("Erro",
                                 "O arquivo originado pelo software CEABS não foi encontrado. "
                                 "Certifique-se de que o arquivo tenha sido gerado após os testes.")

    def executar_continuamente(self):
        try:
            while self.running_flag:
                executar_script()
                time.sleep(1)
        finally:
            # Após o término da execução, atualize o estado dos botões
            self.programa_em_execucao = False
            self.atualizar_estado_botoes()

    def adicionar_info_e_rolar(self, info):
        self.info_text.insert(tk.END, info + "\n\n")
        self.info_text.see(tk.END)
        self.root.update_idletasks()

    def salvar_configuracoes(self):
        if os.path.exists(self.origem_path):
            self.adicionar_info("Configurações salvas.")
        else:
            messagebox.showerror("Erro", "Um ou mais diretórios especificados não existem.")

    def selecionar_origem(self):
        novo_origem = filedialog.askdirectory(title="Selecione a pasta CEABS")
        if novo_origem:
            self.origem_path = novo_origem
            self.adicionar_info("Caminho CEABS atualizado.")
            self.entry_origem.config(state="normal")
            self.entry_origem.delete(0, tk.END)
            self.entry_origem.insert(0, self.origem_path)

    #
    # def selecionar_destino(self):
    #     novo_destino = filedialog.askdirectory(title="Selecione a pasta de Logs")
    #     if novo_destino:
    #         self.destino_path = novo_destino
    #         self.adicionar_info("Caminho de logs atualizado.")
    #         self.entry_destino.config(state="normal")
    #         self.entry_destino.delete(0, tk.END)
    #         self.entry_destino.insert(0, self.destino_path)

    def atualizar_estado_botoes(self):
        if self.programa_em_execucao:
            self.button_executar.config(state="disabled")
            self.entry_tipo_jiga.config(state="disabled")  # Desativa o widget de combobox
        else:
            self.button_executar.config(state="normal")

    def adicionar_info(self, info):
        self.info_text.insert(tk.END, info + "\n")
        self.info_text.see(tk.END)

    def salvar_configuracoes(self):
        # Atualiza os caminhos a partir dos widgets de entrada
        self.origem_path = self.entry_origem.get()

        # Salva as configurações no arquivo config.ini
        self.save_config()

        if os.path.exists(self.origem_path):
            self.adicionar_info("Configurações salvas.")
        else:
            messagebox.showerror("Erro", "Um ou mais diretórios especificados não existem.")

    def confirmar_salvar_arquivo(self, placa_reprovada):
        """
            SE CASO REPROVAR PERGUNTAR SE QUER SAVAR O LOG
            TULLIO - 23/07/2024
        """
        self.resposta = messagebox.askyesno(
            'Placa Reprovada',
            f'Deseja salvar o log de placa reprova: {placa_reprovada}?'
        )
        return self.resposta


def obter_ultima_posicao_lida():
    caminho_arquivo_controle = os.path.join(app.controle_path, 'controlposition.txt')

    try:
        with open(caminho_arquivo_controle, 'r') as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return 0
    except Exception as e:
        print(f"Erro ao obter a última posição lida: {e}")
        return 0


def salvar_ultima_posicao_lida(posicao):
    caminho_arquivo_controle = os.path.join(app.controle_path, 'controlposition.txt')

    with open(caminho_arquivo_controle, 'w') as f:
        f.write(str(posicao))


# Função para obter o caminho do arquivo original (com fallback para o dia anterior)
def obter_caminho_arquivo_original():
    diretorio_origem = app.origem_path

    # Verifica o arquivo de hoje
    data_atual = datetime.now().strftime('%Y-%m-%d')
    nome_arquivo_hoje = f'{data_atual}.csv'
    caminho_arquivo_hoje = os.path.join(diretorio_origem, nome_arquivo_hoje)

    # Verifica o arquivo de ontem (caso a data tenha mudado, mas o arquivo de hoje não esteja disponível ainda)
    data_ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    nome_arquivo_ontem = f'{data_ontem}.csv'
    caminho_arquivo_ontem = os.path.join(diretorio_origem, nome_arquivo_ontem)

    if os.path.exists(caminho_arquivo_hoje):
        return caminho_arquivo_hoje
    elif os.path.exists(caminho_arquivo_ontem):
        return caminho_arquivo_ontem
    else:
        return None


def verificar_existencia_arquivo_original():
    caminho_arquivo = obter_caminho_arquivo_original()
    return caminho_arquivo is not None


def ler_arquivo_original():
    caminho_arquivo = obter_caminho_arquivo_original()

    if caminho_arquivo:
        df = pd.read_csv(caminho_arquivo, sep=',', engine='python', skiprows=1, quoting=csv.QUOTE_NONE)
        return df
    else:
        return None


def processar_linhas_novas(df, ultima_posicao, diretorio_destino):
    if ultima_posicao >= len(df):
        return

    tipo_jiga = app.entry_tipo_jiga.get()
    sufixo_map = {
        '000977': {
            '="LoRa_ID_STATUS"': '_6144',
            '="POWER_TEST"': '_6145',
            '="V3_TEST"': '_6146',
            '="V4_TEST"': '_6147',
            '="UART_TEST"': '_6148',
            '="FIRMWARE_VERSION_TEST"': '_6149',
            '="GPIO_TEST"': '_6150',
            '="ADC_TEST"': '_6151',
            '="G-SENSOR_TEST"': '_6152',
            '="LoRa_TEST"': '_6153',
            '="SETUP_DOWNLOAD"': '_6154',
            '="LoRa_APP_EUI_STATUS"': '_6155',
            '="LoRa_APP_SESSION_KEY_STATUS"': '_6156',
            '="LoRa_DEV_ADDRESS_STATUS"': '_6157',
            '="LoRa_DEV_EUI_STATUS"': '_6158',
            '="LoRa_NTWK_SESSION_KEY_STATUS"': '_6159'
        },
        '000978': {
            '="LoRa_ID_STATUS"': '_6161',
            '="POWER_TEST"': '_6162',
            '="V3_TEST"': '_6163',
            '="V4_TEST"': '_6164',
            '="UART_TEST"': '_6165',
            '="FIRMWARE_VERSION_TEST"': '_6166',
            '="GPIO_TEST"': '_6167',
            '="ADC_TEST"': '_6168',
            '="G-SENSOR_TEST"': '_6169',
            '="LoRa_TEST"': '_6170',
            '="SETUP_DOWNLOAD"': '_6171',
            '="LoRa_APP_EUI_STATUS"': '_6172',
            '="LoRa_APP_SESSION_KEY_STATUS"': '_6173',
            '="LoRa_DEV_ADDRESS_STATUS"': '_6174',
            '="LoRa_DEV_EUI_STATUS"': '_6175',
            '="LoRa_NTWK_SESSION_KEY_STATUS"': '_6176'
        },
        '000981': {
            '="LoRa_ID_STATUS"': '_6178',
            '="POWER_TEST"': '_6179',
            '="V3_TEST"': '_6180',
            '="V4_TEST"': '_6181',
            '="UART_TEST"': '_6182',
            '="FIRMWARE_VERSION_TEST"': '_6183',
            '="GPIO_TEST"': '_6184',
            '="ADC_TEST"': '_6185',
            '="G-SENSOR_TEST"': '_6186',
            '="LoRa_TEST"': '_6187',
            '="SETUP_DOWNLOAD"': '_6188',
            '="LoRa_APP_EUI_STATUS"': '_6189',
            '="LoRa_APP_SESSION_KEY_STATUS"': '_6190',
            '="LoRa_DEV_ADDRESS_STATUS"': '_6191',
            '="LoRa_DEV_EUI_STATUS"': '_6192',
            '="LoRa_NTWK_SESSION_KEY_STATUS"': '_6193'
        },
        '000985': {
            '="LoRa_ID_STATUS"': '_6195',
            '="POWER_TEST"': '_6196',
            '="V3_TEST"': '_6197',
            '="V4_TEST"': '_6198',
            '="UART_TEST"': '_6199',
            '="FIRMWARE_VERSION_TEST"': '_6200',
            '="GPIO_TEST"': '_6201',
            '="ADC_TEST"': '_6202',
            '="G-SENSOR_TEST"': '_6203',
            '="LoRa_TEST"': '_6204',
            '="SETUP_DOWNLOAD"': '_6205',
            '="LoRa_APP_EUI_STATUS"': '_6206',
            '="LoRa_APP_SESSION_KEY_STATUS"': '_6207',
            '="LoRa_DEV_ADDRESS_STATUS"': '_6208',
            '="LoRa_DEV_EUI_STATUS"': '_6209',
            '="LoRa_NTWK_SESSION_KEY_STATUS"': '_6210'
        },
        '000986': {
            '="LoRa_ID_STATUS"': '_6212',
            '="POWER_TEST"': '_6213',
            '="V3_TEST"': '_6214',
            '="V4_TEST"': '_6215',
            '="UART_TEST"': '_6216',
            '="FIRMWARE_VERSION_TEST"': '_6217',
            '="GPIO_TEST"': '_6218',
            '="ADC_TEST"': '_6219',
            '="G-SENSOR_TEST"': '_6220',
            '="LoRa_TEST"': '_6221',
            '="SETUP_DOWNLOAD"': '_6222',
            '="LoRa_APP_EUI_STATUS"': '_6223',
            '="LoRa_APP_SESSION_KEY_STATUS"': '_6224',
            '="LoRa_DEV_ADDRESS_STATUS"': '_6225',
            '="LoRa_DEV_EUI_STATUS"': '_6226',
            '="LoRa_NTWK_SESSION_KEY_STATUS"': '_6227'
        },
        '000988': {
            '="LoRa_ID_STATUS"': '_6230',
            '="POWER_TEST"': '_6231',
            '="V1_TEST"': '_6232',
            '="V3_TEST"': '_6233',
            '="V4_TEST"': '_6234',
            '="V5_TEST"': '_6235',
            '="UART_TEST"': '_6236',
            '="FIRMWARE_VERSION_TEST"': '_6237',
            '="GPIO_TEST"': '_6238',
            '="ADC_TEST"': '_6239',
            '="LoRa_TEST"': '_6240',
            '="1-WIRE_TEST"': '_6241',
            '="GSM_TEST"': '_6242',
            '="GPS_TEST"': '_6243',
            '="SETUP_DOWNLOAD"': '_6244',
            '="LoRa_APP_EUI_STATUS"': '_6245',
            '="LoRa_APP_SESSION_KEY_STATUS"': '_6246',
            '="LoRa_DEV_ADDRESS_STATUS"': '_6247',
            '="LoRa_DEV_EUI_STATUS"': '_6248',
            '="LoRa_NTWK_SESSION_KEY_STATUS"': '_6249'
        },
        '000989': {
            '="LoRa_ID_STATUS"': '_6250',
            '="POWER_TEST"': '_6251',
            '="V1_TEST"': '_6252',
            '="V3_TEST"': '_6253',
            '="V4_TEST"': '_6254',
            '="V5_TEST"': '_6255',
            '="UART_TEST"': '_6256',
            '="FIRMWARE_VERSION_TEST"': '_6257',
            '="GPIO_TEST"': '_6258',
            '="ADC_TEST"': '_6259',
            '="LoRa_TEST"': '_6260',
            '="1-WIRE_TEST"': '_6261',
            '="GSM_TEST"': '_6262',
            '="GPS_TEST"': '_6263',
            '="SETUP_DOWNLOAD"': '_6264',
            '="LoRa_APP_EUI_STATUS"': '_6265',
            '="LoRa_APP_SESSION_KEY_STATUS"': '_6266',
            '="LoRa_DEV_ADDRESS_STATUS"': '_6267',
            '="LoRa_DEV_EUI_STATUS"': '_6268',
            '="LoRa_NTWK_SESSION_KEY_STATUS"': '_6269'
        },
        '000998': {
            '="LoRa_ID_STATUS"': '_6379',
            '="POWER_TEST"': '_6380',
            '="V1_TEST"': '_6381',
            '="V3_TEST"': '_6382',
            '="V4_TEST"': '_6383',
            '="V5_TEST"': '_6384',
            '="UART_TEST"': '_6385',
            '="FIRMWARE_VERSION_TEST"': '_6386',
            '="GPIO_TEST"': '_6387',
            '="ADC_TEST"': '_6388',
            '="LoRa_TEST"': '_6389',
            '="1-WIRE_TEST"': '_6390',
            '="GSM_TEST"': '_6391',
            '="GPS_TEST"': '_6392',
            '="SETUP_DOWNLOAD"': '_6393',
            '="LoRa_APP_EUI_STATUS"': '_6394',
            '="LoRa_APP_SESSION_KEY_STATUS"': '_6395',
            '="LoRa_DEV_ADDRESS_STATUS"': '_6396',
            '="LoRa_DEV_EUI_STATUS"': '_6397',
            '="LoRa_NTWK_SESSION_KEY_STATUS"': '_6398'
        },
        '001001': {
            '="LoRa_ID_STATUS"': '_6420',
            '="POWER_TEST"': '_6421',
            '="V1_TEST"': '_6422',
            '="V3_TEST"': '_6423',
            '="V4_TEST"': '_6424',
            '="V5_TEST"': '_6425',
            '="UART_TEST"': '_6426',
            '="FIRMWARE_VERSION_TEST"': '_6427',
            '="GPIO_TEST"': '_6428',
            '="ADC_TEST"': '_6429',
            '="LoRa_TEST"': '_6430',
            '="1-WIRE_TEST"': '_6431',
            '="GSM_TEST"': '_6432',
            '="GPS_TEST"': '_6433',
            '="SETUP_DOWNLOAD"': '_6434',
            '="LoRa_APP_EUI_STATUS"': '_6435',
            '="LoRa_APP_SESSION_KEY_STATUS"': '_6436',
            '="LoRa_DEV_ADDRESS_STATUS"': '_6437',
            '="LoRa_DEV_EUI_STATUS"': '_6438',
            '="LoRa_NTWK_SESSION_KEY_STATUS"': '_6439'
        },
        '001002': {
            '="LoRa_ID_STATUS"': '_6440',
            '="POWER_TEST"': '_6441',
            '="V1_TEST"': '_6442',
            '="V3_TEST"': '_6443',
            '="V4_TEST"': '_6444',
            '="V5_TEST"': '_6445',
            '="UART_TEST"': '_6446',
            '="FIRMWARE_VERSION_TEST"': '_6447',
            '="GPIO_TEST"': '_6448',
            '="ADC_TEST"': '_6449',
            '="LoRa_TEST"': '_6450',
            '="1-WIRE_TEST"': '_6451',
            '="GSM_TEST"': '_6452',
            '="GPS_TEST"': '_6453',
            '="SETUP_DOWNLOAD"': '_6454',
            '="LoRa_APP_EUI_STATUS"': '_6455',
            '="LoRa_APP_SESSION_KEY_STATUS"': '_6456',
            '="LoRa_DEV_ADDRESS_STATUS"': '_6457',
            '="LoRa_DEV_EUI_STATUS"': '_6458',
            '="LoRa_NTWK_SESSION_KEY_STATUS"': '_6459'
        },
        '001004': {
            '="LoRa_ID_STATUS"': '_6460',
            '="POWER_TEST"': '_6461',
            '="V1_TEST"': '_6462',
            '="V3_TEST"': '_6463',
            '="V4_TEST"': '_6464',
            '="V5_TEST"': '_6465',
            '="UART_TEST"': '_6466',
            '="FIRMWARE_VERSION_TEST"': '_6467',
            '="GPIO_TEST"': '_6468',
            '="ADC_TEST"': '_6469',
            '="LoRa_TEST"': '_6470',
            '="1-WIRE_TEST"': '_6471',
            '="GSM_TEST"': '_6472',
            '="GPS_TEST"': '_6473',
            '="SETUP_DOWNLOAD"': '_6474',
            '="LoRa_APP_EUI_STATUS"': '_6475',
            '="LoRa_APP_SESSION_KEY_STATUS"': '_6476',
            '="LoRa_DEV_ADDRESS_STATUS"': '_6477',
            '="LoRa_DEV_EUI_STATUS"': '_6478',
            '="LoRa_NTWK_SESSION_KEY_STATUS"': '_6479'
        }
    }

    df_novas = df.iloc[ultima_posicao:]
    for _, row in df_novas.iterrows():
        sufixo_arquivo = '_0000'
        houve_falha = False  # Inicializa como falso (sem falha)
        if tipo_jiga in sufixo_map:
            for status_col, sufixo in sufixo_map[tipo_jiga].items():
                if status_col in row and row[status_col] not in ['="PASS"']:
                    sufixo_arquivo = sufixo
                    houve_falha = True
                    break
        valor_serial_number = row['="SERIAL_NUMBER_VALUE"']
        valor_lora_id = row['="LoRa_ID_VALUE"']

        if valor_serial_number and valor_lora_id and valor_serial_number != '="0"' and valor_lora_id != '="0"':
            numeric_part_serial = ''.join(filter(str.isdigit, valor_serial_number))
            numeric_part_lora = ''.join(filter(str.isdigit, valor_lora_id))
            caminho_destino = os.path.join(
                diretorio_destino, f'{int(numeric_part_serial)}ç{int(numeric_part_lora)}{sufixo_arquivo}.txt')

            # Adicionar timestamp à mensagem
            timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

            if houve_falha:
                if app.confirmar_salvar_arquivo(numeric_part_serial):
                    with open(caminho_destino, 'w'):
                        pass
                    mensagem_info = f'[{timestamp}] - Arquivo gerado em: {caminho_destino}'
                    app.adicionar_info_e_rolar(mensagem_info)
                else:
                    mensagem_info = f'[{timestamp}] - A placa com o número de série {numeric_part_serial} foi reprovada. ' \
                                    'O log correspondente não foi salvo.'
                    app.adicionar_info_e_rolar(mensagem_info)
            else:
                # Se não houve falha, gerar o arquivo automaticamente sem perguntar
                with open(caminho_destino, 'w'):
                    pass
                mensagem_info = f'[{timestamp}] - Arquivo gerado em: {caminho_destino}'
                app.adicionar_info_e_rolar(mensagem_info)

    salvar_ultima_posicao_lida(len(df))
    copiar_arquivo_para_jiga(df, diretorio_destino)


def copiar_arquivo_para_jiga(df, diretorio_destino):
    caminho_arquivo_original = obter_caminho_arquivo_original()
    # Adicionar timestamp à mensagem
    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    if caminho_arquivo_original:
        jiga_selecionado = app.entry_tipo_jiga.get()

        # Obtenha o caminho do jiga a partir do arquivo de configuração
        try:
            caminho_destino_jiga = app.config.get('DT-JIGA', jiga_selecionado)
        except configparser.NoOptionError:
            mensagem_erro = f'[{timestamp}] - Caminho para o jiga "{jiga_selecionado}" não encontrado no arquivo de configuração.'
            app.adicionar_info_e_rolar(mensagem_erro)
            return

        # Verifique se o diretório de destino do jiga existe, se não, crie-o
        if not os.path.exists(caminho_destino_jiga):
            mensagem_erro = f'[{timestamp}] - Caminho para backup do jiga "{jiga_selecionado}" não encontrado no arquivo de configuração.'
            app.adicionar_info_e_rolar(mensagem_erro)

        # Copie o arquivo original para o diretório do jiga
        try:
            shutil.copy(caminho_arquivo_original, caminho_destino_jiga)
            mensagem_info = f'[{timestamp}] - Arquivo copiado para: {caminho_destino_jiga}'
            app.adicionar_info_e_rolar(mensagem_info)
        except Exception as e:
            mensagem_erro = f'[{timestamp}] - Erro ao copiar arquivo para o endereço: {e}.'
            app.adicionar_info_e_rolar(mensagem_erro)


def limpar_ultima_posicao_lida():
    salvar_ultima_posicao_lida(0)


def encerrar_programa(signal, frame):
    resposta = messagebox.askyesno("Encerrar Programa", "Tem certeza que deseja encerrar o programa?")
    if resposta:
        observer.stop()
        observer.join()
        root.destroy()


class FileModifiedHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        elif event.event_type == 'modified':
            print(f'Arquivo {event.src_path} foi modificado. Esperando antes de executar o script...')
            time.sleep(1)
            app.executar_programa()


def executar_script():
    if verificar_existencia_arquivo_original():
        df_original = ler_arquivo_original()

        if df_original is not None:
            ultima_posicao = obter_ultima_posicao_lida()
            processar_linhas_novas(df_original, ultima_posicao, app.destino_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = MyApp(root)

    observer = Observer()
    event_handler = FileModifiedHandler()

    observer.schedule(event_handler, path=app.origem_path, recursive=False)
    observer.start()

    root.protocol("WM_DELETE_WINDOW", lambda: encerrar_programa(None, None))
    root.mainloop()
