import shutil
import pandas as pd
from datetime import datetime
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
__version__ = '2.2.0'
class MyApp:
    def __init__(self, root):
        self.root = root
        root.iconbitmap(default='ico-botlog.ico')
        self.root.title("BotLog - CEABS "+__version__)
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
                                 "O arquivo originado pelo software CEABS não foi encontrado. Certifique-se de que o arquivo tenha sido gerado após os testes.")



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

def obter_caminho_arquivo_original():
    diretorio_origem = app.origem_path

    data_atual = datetime.now().strftime('%Y-%m-%d')
    nome_arquivo_esperado = f'{data_atual}.csv'

    caminho_arquivo = os.path.join(diretorio_origem, nome_arquivo_esperado)

    if os.path.exists(caminho_arquivo):
        return caminho_arquivo
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

    df_novas = df.iloc[ultima_posicao:]

    for _, row in df_novas.iterrows():
        sufixo_arquivo = '_0000'
        # Verifica se a DT-JIGA é igual a 000977
        if app.entry_tipo_jiga.get() == '000977':
            if '="SERIAL_NUMBER_STATUS"' in row and row['="SERIAL_NUMBER_STATUS"'] not in ['="PASS"']:
                continue
            elif '="LoRa_ID_STATUS"' in row and row['="LoRa_ID_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6144'
            elif '="POWER_TEST"' in row and row['="POWER_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6145'
            elif '="V3_TEST"' in row and row['="V3_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6146'
            elif '="V4_TEST"' in row and row['="V4_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6147'
            elif '="UART_TEST"' in row and row['="UART_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6148'
            elif '="FIRMWARE_VERSION_TEST"' in row and row['="FIRMWARE_VERSION_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6149'
            elif '="GPIO_TEST"' in row and row['="GPIO_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6150'
            elif '="ADC_TEST"' in row and row['="ADC_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6151'
            elif '="G-SENSOR_TEST"' in row and row['="G-SENSOR_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6152'
            elif '="LoRa_TEST"' in row and row['="LoRa_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6153'
            elif '="SETUP_DOWNLOAD"' in row and row['="SETUP_DOWNLOAD"'] not in ['="PASS"']:
                sufixo_arquivo = '_6154'
            elif '="LoRa_APP_EUI_STATUS"' in row and row['="LoRa_APP_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6155'
            elif '="LoRa_APP_SESSION_KEY_STATUS"' in row and row['="LoRa_APP_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6156'
            elif '="LoRa_DEV_ADDRESS_STATUS"' in row and row['="LoRa_DEV_ADDRESS_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6157'
            elif '="LoRa_DEV_EUI_STATUS"' in row and row['="LoRa_DEV_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6158'
            elif '="LoRa_NTWK_SESSION_KEY_STATUS"' in row and row['="LoRa_NTWK_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6159'
        elif app.entry_tipo_jiga.get() == '000978':
            if '="SERIAL_NUMBER_STATUS"' in row and row['="SERIAL_NUMBER_STATUS"'] not in ['="PASS"']:
                continue
            elif '="LoRa_ID_STATUS"' in row and row['="LoRa_ID_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6161'
            elif '="POWER_TEST"' in row and row['="POWER_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6162'
            elif '="V3_TEST"' in row and row['="V3_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6163'
            elif '="V4_TEST"' in row and row['="V4_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6164'
            elif '="UART_TEST"' in row and row['="UART_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6165'
            elif '="FIRMWARE_VERSION_TEST"' in row and row['="FIRMWARE_VERSION_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6166'
            elif '="GPIO_TEST"' in row and row['="GPIO_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6167'
            elif '="ADC_TEST"' in row and row['="ADC_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6168'
            elif '="G-SENSOR_TEST"' in row and row['="G-SENSOR_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6169'
            elif '="LoRa_TEST"' in row and row['="LoRa_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6170'
            elif '="SETUP_DOWNLOAD"' in row and row['="SETUP_DOWNLOAD"'] not in ['="PASS"']:
                sufixo_arquivo = '_6171'
            elif '="LoRa_APP_EUI_STATUS"' in row and row['="LoRa_APP_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6172'
            elif '="LoRa_APP_SESSION_KEY_STATUS"' in row and row['="LoRa_APP_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6173'
            elif '="LoRa_DEV_ADDRESS_STATUS"' in row and row['="LoRa_DEV_ADDRESS_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6174'
            elif '="LoRa_DEV_EUI_STATUS"' in row and row['="LoRa_DEV_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6175'
            elif '="LoRa_NTWK_SESSION_KEY_STATUS"' in row and row['="LoRa_NTWK_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6176'
        elif app.entry_tipo_jiga.get() == '000981':
            if '="SERIAL_NUMBER_STATUS"' in row and row['="SERIAL_NUMBER_STATUS"'] not in ['="PASS"']:
                continue
            elif '="LoRa_ID_STATUS"' in row and row['="LoRa_ID_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6178'
            elif '="POWER_TEST"' in row and row['="POWER_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6179'
            elif '="V3_TEST"' in row and row['="V3_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6180'
            elif '="V4_TEST"' in row and row['="V4_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6181'
            elif '="UART_TEST"' in row and row['="UART_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6182'
            elif '="FIRMWARE_VERSION_TEST"' in row and row['="FIRMWARE_VERSION_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6183'
            elif '="GPIO_TEST"' in row and row['="GPIO_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6184'
            elif '="ADC_TEST"' in row and row['="ADC_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6185'
            elif '="G-SENSOR_TEST"' in row and row['="G-SENSOR_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6186'
            elif '="LoRa_TEST"' in row and row['="LoRa_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6187'
            elif '="SETUP_DOWNLOAD"' in row and row['="SETUP_DOWNLOAD"'] not in ['="PASS"']:
                sufixo_arquivo = '_6188'
            elif '="LoRa_APP_EUI_STATUS"' in row and row['="LoRa_APP_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6189'
            elif '="LoRa_APP_SESSION_KEY_STATUS"' in row and row['="LoRa_APP_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6190'
            elif '="LoRa_DEV_ADDRESS_STATUS"' in row and row['="LoRa_DEV_ADDRESS_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6191'
            elif '="LoRa_DEV_EUI_STATUS"' in row and row['="LoRa_DEV_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6192'
            elif '="LoRa_NTWK_SESSION_KEY_STATUS"' in row and row['="LoRa_NTWK_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6193'
        elif app.entry_tipo_jiga.get() == '000985':
            if '="SERIAL_NUMBER_STATUS"' in row and row['="SERIAL_NUMBER_STATUS"'] not in ['="PASS"']:
                continue
            elif '="LoRa_ID_STATUS"' in row and row['="LoRa_ID_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6195'
            elif '="POWER_TEST"' in row and row['="POWER_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6196'
            elif '="V3_TEST"' in row and row['="V3_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6197'
            elif '="V4_TEST"' in row and row['="V4_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6198'
            elif '="UART_TEST"' in row and row['="UART_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6199'
            elif '="FIRMWARE_VERSION_TEST"' in row and row['="FIRMWARE_VERSION_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6200'
            elif '="GPIO_TEST"' in row and row['="GPIO_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6201'
            elif '="ADC_TEST"' in row and row['="ADC_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6202'
            elif '="G-SENSOR_TEST"' in row and row['="G-SENSOR_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6203'
            elif '="LoRa_TEST"' in row and row['="LoRa_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6204'
            elif '="SETUP_DOWNLOAD"' in row and row['="SETUP_DOWNLOAD"'] not in ['="PASS"']:
                sufixo_arquivo = '_6205'
            elif '="LoRa_APP_EUI_STATUS"' in row and row['="LoRa_APP_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6206'
            elif '="LoRa_APP_SESSION_KEY_STATUS"' in row and row['="LoRa_APP_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6207'
            elif '="LoRa_DEV_ADDRESS_STATUS"' in row and row['="LoRa_DEV_ADDRESS_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6208'
            elif '="LoRa_DEV_EUI_STATUS"' in row and row['="LoRa_DEV_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6209'
            elif '="LoRa_NTWK_SESSION_KEY_STATUS"' in row and row['="LoRa_NTWK_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6210'
        elif app.entry_tipo_jiga.get() == '000986':
            if '="SERIAL_NUMBER_STATUS"' in row and row['="SERIAL_NUMBER_STATUS"'] not in ['="PASS"']:
                continue
            elif '="LoRa_ID_STATUS"' in row and row['="LoRa_ID_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6212'
            elif '="POWER_TEST"' in row and row['="POWER_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6213'
            elif '="V3_TEST"' in row and row['="V3_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6214'
            elif '="V4_TEST"' in row and row['="V4_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6215'
            elif '="UART_TEST"' in row and row['="UART_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6216'
            elif '="FIRMWARE_VERSION_TEST"' in row and row['="FIRMWARE_VERSION_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6217'
            elif '="GPIO_TEST"' in row and row['="GPIO_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6218'
            elif '="ADC_TEST"' in row and row['="ADC_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6219'
            elif '="G-SENSOR_TEST"' in row and row['="G-SENSOR_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6220'
            elif '="LoRa_TEST"' in row and row['="LoRa_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6221'
            elif '="SETUP_DOWNLOAD"' in row and row['="SETUP_DOWNLOAD"'] not in ['="PASS"']:
                sufixo_arquivo = '_6222'
            elif '="LoRa_APP_EUI_STATUS"' in row and row['="LoRa_APP_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6223'
            elif '="LoRa_APP_SESSION_KEY_STATUS"' in row and row['="LoRa_APP_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6224'
            elif '="LoRa_DEV_ADDRESS_STATUS"' in row and row['="LoRa_DEV_ADDRESS_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6225'
            elif '="LoRa_DEV_EUI_STATUS"' in row and row['="LoRa_DEV_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6226'
            elif '="LoRa_NTWK_SESSION_KEY_STATUS"' in row and row['="LoRa_NTWK_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6227'

        elif app.entry_tipo_jiga.get() == '000988':
            if '="SERIAL_NUMBER_STATUS"' in row and row['="SERIAL_NUMBER_STATUS"'] not in ['="PASS"']:
                continue
            elif '="LoRa_ID_STATUS"' in row and row['="LoRa_ID_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6230'
            elif '="POWER_TEST"' in row and row['="POWER_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6231'
            elif '="V1_TEST"' in row and row['="V1_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6232'
            elif '="V3_TEST"' in row and row['="V3_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6233'
            elif '="V4_TEST"' in row and row['="V4_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6234'
            elif '="V5_TEST"' in row and row['="V5_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6235'
            elif '="UART_TEST"' in row and row['="UART_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6236'
            elif '="FIRMWARE_VERSION_TEST"' in row and row['="FIRMWARE_VERSION_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6237'
            elif '="GPIO_TEST"' in row and row['="GPIO_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6238'
            elif '="ADC_TEST"' in row and row['="ADC_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6239'
            elif '="LoRa_TEST"' in row and row['="LoRa_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6240'
            elif '="1-WIRE_TEST"' in row and row['="1-WIRE_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6241'
            elif '="GSM_TEST"' in row and row['="GSM_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6242'
            elif '="GPS_TEST"' in row and row['="GPS_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6243'
            elif '="SETUP_DOWNLOAD"' in row and row['="SETUP_DOWNLOAD"'] not in ['="PASS"']:
                sufixo_arquivo = '_6244'
            elif '="LoRa_APP_EUI_STATUS"' in row and row['="LoRa_APP_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6245'
            elif '="LoRa_APP_SESSION_KEY_STATUS"' in row and row['="LoRa_APP_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6246'
            elif '="LoRa_DEV_ADDRESS_STATUS"' in row and row['="LoRa_DEV_ADDRESS_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6247'
            elif '="LoRa_DEV_EUI_STATUS"' in row and row['="LoRa_DEV_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6248'
            elif '="LoRa_NTWK_SESSION_KEY_STATUS"' in row and row['="LoRa_NTWK_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6249'

        elif app.entry_tipo_jiga.get() == '000989':
            if '="SERIAL_NUMBER_STATUS"' in row and row['="SERIAL_NUMBER_STATUS"'] not in ['="PASS"']:
                continue
            elif '="LoRa_ID_STATUS"' in row and row['="LoRa_ID_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6250'
            elif '="POWER_TEST"' in row and row['="POWER_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6251'
            elif '="V1_TEST"' in row and row['="V1_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6252'
            elif '="V3_TEST"' in row and row['="V3_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6253'
            elif '="V4_TEST"' in row and row['="V4_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6254'
            elif '="V5_TEST"' in row and row['="V5_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6255'
            elif '="UART_TEST"' in row and row['="UART_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6256'
            elif '="FIRMWARE_VERSION_TEST"' in row and row['="FIRMWARE_VERSION_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6257'
            elif '="GPIO_TEST"' in row and row['="GPIO_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6258'
            elif '="ADC_TEST"' in row and row['="ADC_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6259'
            elif '="LoRa_TEST"' in row and row['="LoRa_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6260'
            elif '="1-WIRE_TEST"' in row and row['="1-WIRE_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6261'
            elif '="GSM_TEST"' in row and row['="GSM_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6262'
            elif '="GPS_TEST"' in row and row['="GPS_TEST"'] not in ['="PASS"']:
                sufixo_arquivo = '_6263'
            elif '="SETUP_DOWNLOAD"' in row and row['="SETUP_DOWNLOAD"'] not in ['="PASS"']:
                sufixo_arquivo = '_6264'
            elif '="LoRa_APP_EUI_STATUS"' in row and row['="LoRa_APP_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6265'
            elif '="LoRa_APP_SESSION_KEY_STATUS"' in row and row['="LoRa_APP_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6266'
            elif '="LoRa_DEV_ADDRESS_STATUS"' in row and row['="LoRa_DEV_ADDRESS_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6267'
            elif '="LoRa_DEV_EUI_STATUS"' in row and row['="LoRa_DEV_EUI_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6268'
            elif '="LoRa_NTWK_SESSION_KEY_STATUS"' in row and row['="LoRa_NTWK_SESSION_KEY_STATUS"'] not in ['="PASS"']:
                sufixo_arquivo = '_6269'
        else:
            messagebox.showerror("Erro","Não foi identificado a jiga")


        valor_serial_number = row['="SERIAL_NUMBER_VALUE"']
        valor_lora_id = row['="LoRa_ID_VALUE"']
        numeric_part_serial = ''.join(filter(str.isdigit, valor_serial_number))
        numeric_part_lora = ''.join(filter(str.isdigit, valor_lora_id))
        caminho_destino = os.path.join(diretorio_destino, f'{int(numeric_part_serial)}ç{int(numeric_part_lora)}{sufixo_arquivo}.txt')

        with open(caminho_destino, 'w'):
            pass

        mensagem_info = f'Arquivo gerado em: {caminho_destino}'
        app.adicionar_info_e_rolar(mensagem_info)

    salvar_ultima_posicao_lida(len(df))
    salvar_ultima_posicao_lida(len(df))
    copiar_arquivo_para_jiga(df, diretorio_destino)
def copiar_arquivo_para_jiga(df, diretorio_destino):
    caminho_arquivo_original = obter_caminho_arquivo_original()
    if caminho_arquivo_original:
        jiga_selecionado = app.entry_tipo_jiga.get()

        # Obtenha o caminho do jiga a partir do arquivo de configuração
        try:
            caminho_destino_jiga = app.config.get('DT-JIGA', jiga_selecionado)
        except configparser.NoOptionError:
            mensagem_erro = f'Caminho para o jiga "{jiga_selecionado}" não encontrado no arquivo de configuração.'
            app.adicionar_info_e_rolar(mensagem_erro)
            return

        # Verifique se o diretório de destino do jiga existe, se não, crie-o
        if not os.path.exists(caminho_destino_jiga):
            mensagem_erro = f'Caminho para backup do jiga "{jiga_selecionado}" não encontrado no arquivo de configuração.'
            app.adicionar_info_e_rolar(mensagem_erro)

        # Copie o arquivo original para o diretório do jiga
        try:
            shutil.copy(caminho_arquivo_original, caminho_destino_jiga)
            mensagem_info = f'Arquivo copiado para: {caminho_destino_jiga}'
            app.adicionar_info_e_rolar(mensagem_info)
        except Exception as e:
            mensagem_erro = f'Erro ao copiar arquivo para o endereço: {e}.'
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