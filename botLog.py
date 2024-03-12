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
class MyApp:
    def __init__(self, root):
        self.root = root
        root.iconbitmap(default='ico-botlog.ico')
        self.root.title("BotLog - CEABS")
        self.running_flag = False  # Adiciona uma nova variável de controle para o loop
        self.programa_em_execucao = False

        # Configuração dos caminhos pré-definidos
        self.config = self.load_config()

        self.origem_path = self.config.get('Paths', 'source_path', fallback="C:/")
        self.destino_path = self.config.get('Paths', 'destination_path', fallback="C:/")
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
        self.button_parar = None

        self.entry_tipo_produto = None
        self.produtos = self.load_products()
        # Criação da interface gráfica
        self.create_tabs()

        self.iniciar_arquivo_controle()

    def load_products(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        return dict(config.items('Products'))
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
        self.config.set('Paths', 'destination_path', self.destino_path)

        with open('config.ini', 'w') as config_file:
            self.config.write(config_file)
    def create_tabs(self):
        # Aba 1: Informações e Controle
        tab_control = ttk.Notebook(self.root)
        tab1 = ttk.Frame(tab_control)
        tab2 = ttk.Frame(tab_control)
        tab_control.add(tab1, text='Informações e Controle')
        tab_control.add(tab2, text='Configuração')

        # Adiciona um widget Combobox para selecionar o tipo de produto
        label_tipo_produto = tk.Label(tab1, text='Tipo de Produto: ')
        label_tipo_produto.pack(pady=10)

        produtos_disponiveis = [produto.upper() for produto in self.produtos.keys()]
        self.entry_tipo_produto = ttk.Combobox(tab1, values=produtos_disponiveis, state="readonly", width=20)
        # Define o valor padrão em maiúsculas
        self.entry_tipo_produto.set(produtos_disponiveis[0])
        self.entry_tipo_produto.pack(pady=5)
        # Aba 1: Informações e Controle
        label_info = tk.Label(tab1, text="Informações geradas pelo programa:")
        label_info.pack(pady=10)

        # Adiciona um widget Text para exibir informações
        self.info_text = tk.Text(tab1, height=10, width=50)
        self.info_text.pack(pady=10)

        self.button_executar = tk.Button(tab1, text="Executar", command=self.executar_programa)
        self.button_executar.pack(side=tk.LEFT, padx=10)

        self.button_parar = tk.Button(tab1, text="Parar", command=self.parar_programa)
        self.button_parar.pack(side=tk.LEFT, padx=10)

        # Aba 2: Configurações
        label_config = tk.Label(tab2, text="Definir Locais de Arquivos")
        label_config.grid(row=0, column=0, pady=10, sticky=tk.W)
        label_origem = tk.Label(tab2, text='Pasta CEABS: ')
        label_origem.grid(row=1, column=0, pady=10, sticky=tk.W)
        label_logs = tk.Label(tab2, text='Pasta de Logs: ')
        label_logs.grid(row=2, column=0, pady=10, sticky=tk.W)

        # Adicionando campos de entrada para configurar os caminhos
        self.entry_origem = tk.Entry(tab2, width=40)
        self.entry_origem.insert(0, self.origem_path)
        self.entry_origem.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)

        self.entry_destino = tk.Entry(tab2, width=40)
        self.entry_destino.insert(0, self.destino_path)
        self.entry_destino.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)



        # Botão para abrir caixa de diálogo para selecionar novo caminho
        button_selecionar_origem = tk.Button(tab2, text="Local", command=self.selecionar_origem)
        button_selecionar_origem.grid(row=1, column=2, pady=5, padx=5, sticky=tk.W)

        button_selecionar_destino = tk.Button(tab2, text="Local", command=self.selecionar_destino)
        button_selecionar_destino.grid(row=2, column=2, pady=5, padx=5, sticky=tk.W)



        # Botão para salvar configurações
        button_salvar_config = tk.Button(tab2, text="Salvar Configurações", command=self.salvar_configuracoes)
        button_salvar_config.grid(row=5, column=1, pady=10, sticky=tk.W)

        # Adiciona as abas à janela
        tab_control.pack(expand=1, fill="both")

    def executar_programa(self):
        if not self.programa_em_execucao:
            caminho_arquivo_original = obter_caminho_arquivo_original()
            if caminho_arquivo_original != self.config.get('Paths', 'last_source_file', fallback=None):
                limpar_ultima_posicao_lida()
                self.config.set('Paths', 'last_source_file', caminho_arquivo_original)
                self.save_config()

        if not self.programa_em_execucao:
            self.adicionar_info("Programa em execução...")
            self.programa_em_execucao = True
            self.atualizar_estado_botoes()

            self.running_flag = True  # Inicia o loop

            # Inicia um thread separado para executar o loop continuamente
            self.thread_execucao = threading.Thread(target=self.executar_continuamente, daemon=True).start()

    def parar_programa(self):
        if self.programa_em_execucao:
            resposta = messagebox.askyesno("Parar Programa", "Tem certeza que deseja parar o programa?")
            self.adicionar_info("Programa parado...")
            if resposta:
                self.running_flag = False

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
        if os.path.exists(self.origem_path) and os.path.exists(self.destino_path):
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

    def selecionar_destino(self):
        novo_destino = filedialog.askdirectory(title="Selecione a pasta de Logs")
        if novo_destino:
            self.destino_path = novo_destino
            self.adicionar_info("Caminho de logs atualizado.")
            self.entry_destino.config(state="normal")
            self.entry_destino.delete(0, tk.END)
            self.entry_destino.insert(0, self.destino_path)

    def atualizar_estado_botoes(self):
        if self.programa_em_execucao:
            self.button_executar.config(state="disabled")
            self.button_parar.config(state="normal")
        else:
            self.button_executar.config(state="normal")
            self.button_parar.config(state="disabled")

    def adicionar_info(self, info):
        self.info_text.insert(tk.END, info + "\n")
        self.info_text.see(tk.END)

    def salvar_configuracoes(self):
        # Atualiza os caminhos a partir dos widgets de entrada
        self.origem_path = self.entry_origem.get()
        self.destino_path = self.entry_destino.get()

        # Salva as configurações no arquivo config.ini
        self.save_config()

        if os.path.exists(self.origem_path) and os.path.exists(self.destino_path):
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

        if '="SERIAL_NUMBER_STATUS"' in row and row['="SERIAL_NUMBER_STATUS"'] not in ['="PASS"']:
            continue
        elif '="LoRa_ID_STATUS"' in row and row['="LoRa_ID_STATUS"'] not in ['="PASS"']:
            sufixo_arquivo = '_6105'
        elif '="POWER_TEST"' in row and row['="POWER_TEST"'] not in ['="PASS"']:
            sufixo_arquivo = '_6100'
        elif '="V3_TEST"' in row and row['="V3_TEST"'] not in ['="PASS"']:
            sufixo_arquivo = '_6102'
        elif '="V4_TEST"' in row and row['="V4_TEST"'] not in ['="PASS"']:
            sufixo_arquivo = '_6101'
        elif '="UART_TEST"' in row and row['="UART_TEST"'] not in ['="PASS"']:
            sufixo_arquivo = '_6103'
        elif '="FIRMWARE_VERSION_TEST"' in row and row['="FIRMWARE_VERSION_TEST"'] not in ['="PASS"']:
            sufixo_arquivo = '_6104'
        elif '="GPIO_TEST"' in row and row['="GPIO_TEST"'] not in ['="PASS"']:
            sufixo_arquivo = '_6106'
        elif '="ADC_TEST"' in row and row['="ADC_TEST"'] not in ['="PASS"']:
            sufixo_arquivo = '_6107'
        elif '="G-SENSOR_TEST"' in row and row['="G-SENSOR_TEST"'] not in ['="PASS"']:
            sufixo_arquivo = '_6108'
        elif '="LoRa_TEST"' in row and row['="LoRa_TEST"'] not in ['="PASS"']:
            sufixo_arquivo = '_6109'
        elif '="SETUP_DOWNLOAD"' in row and row['="SETUP_DOWNLOAD"'] not in ['="PASS"']:
            sufixo_arquivo = '_6110'
        elif '="LoRa_APP_EUI_STATUS"' in row and row['="LoRa_APP_EUI_STATUS"'] not in ['="PASS"']:
            sufixo_arquivo = '_6113'
        elif '="LoRa_APP_SESSION_KEY_STATUS"' in row and row['="LoRa_APP_SESSION_KEY_STATUS"'] not in ['="PASS"']:
            sufixo_arquivo = '_6114'
        elif '="LoRa_DEV_ADDRESS_STATUS"' in row and row['="LoRa_DEV_ADDRESS_STATUS"'] not in ['="PASS"']:
            sufixo_arquivo = '_6112'
        elif '="LoRa_DEV_EUI_STATUS"' in row and row['="LoRa_DEV_EUI_STATUS"'] not in ['="PASS"']:
            sufixo_arquivo = '_6111'
        elif '="LoRa_NTWK_SESSION_KEY_STATUS"' in row and row['="LoRa_NTWK_SESSION_KEY_STATUS"'] not in ['="PASS"']:
            sufixo_arquivo = '_6115'

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
    copiar_arquivo_para_produto(df, diretorio_destino)
def copiar_arquivo_para_produto(df, diretorio_destino):
    caminho_arquivo_original = obter_caminho_arquivo_original()
    if caminho_arquivo_original:
        produto_selecionado = app.entry_tipo_produto.get()

        # Obtenha o caminho do produto a partir do arquivo de configuração
        try:
            caminho_destino_produto = app.config.get('Products', produto_selecionado)
        except configparser.NoOptionError:
            mensagem_erro = f'Caminho para o produto "{produto_selecionado}" não encontrado no arquivo de configuração.'
            app.adicionar_info_e_rolar(mensagem_erro)
            return

        # Verifique se o diretório de destino do produto existe, se não, crie-o
        if not os.path.exists(caminho_destino_produto):
            mensagem_erro = f'Caminho para backup do produto "{produto_selecionado}" não encontrado no arquivo de configuração.'
            app.adicionar_info_e_rolar(mensagem_erro)

        # Copie o arquivo original para o diretório do produto
        try:
            shutil.copy(caminho_arquivo_original, caminho_destino_produto)
            mensagem_info = f'Arquivo copiado para: {caminho_destino_produto}'
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