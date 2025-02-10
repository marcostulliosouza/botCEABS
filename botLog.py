import shutil
from collections import deque
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
import json

"""
v 2.0.1
- Separado os logs em função da jiga.
- Adicionado falhas especifica por jiga.
- Retirado a opção de produto e deixado opção da dt da jiga
- Melhorado o desempenho do monitoramento da pasta para verificar se trocou o dia após meia noite

v 2.2.0
- Adicionado novo produto
- Criado interface para alternar entre produto

v 3.0.0
- Adicionado novas jigas

v 3.0.1
25/07/24
- Otimizado o código 
- Adicionado uma caixa de pergunta para salvar logs de placas reprovadas

v 4.0.0 
25/07/24
- Adicionado a jiga 1004

V4.1.0
18/09/24
- Melhorado a lógica para garantir que se a placa não apresenta falha não deve ser gerado
o questionamento se deseja retestar a plata
- Adicionado nos logs data e hora para melhor analise.
- Otimizado a questão de trocar o dia meia noite.

V4.1.0
07/12/24
- Otimizado os dados de falha em JSON
- Compatível para rodar a versão nova do software do cliente
"""
"""""
V4.4.0
10/02/25
- Adicionado delay de 10s antes de gerar o log de aprovado ou reprovado.
"""

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


class MyApp:
    def __init__(self, root):
        self.root = root
        self.version = VERSION
        root.iconbitmap(default='ico-botlog.ico')
        self.root.title("BotLog - CEABS " + self.version)
        self.root.geometry("400x450")
        self.running_flag = False  # Adiciona uma nova variável de controle para o loop
        self.programa_em_execucao = False
        self.alerta_ativo = False  # Indica se uma janela de alerta crítico já está aberta
        self.fila_alertas = deque()

        # Configuração dos caminhos pré-definidos
        self.config = self.load_config()

        self.origem_path = self.config.get('PATH', 'source_path', fallback="C:/")
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
        self.jigas = self.load_jigas()

        self.produtos = self.load_produto()

        # Criação da interface gráfica
        self.create_tabs()

        self.iniciar_arquivo_controle()

    def load_produto(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        return dict(config.items('PRODUTO'))

    def load_jigas(self):
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
        self.config.set('PATH', 'source_path', self.origem_path)

        with open('config.ini', 'w') as config_file:
            self.config.write(config_file)

    def create_tabs(self):
        # Menu Superior
        menu_bar = tk.Menu(self.root)

        # Menu "Arquivo"
        menu_arquivo = tk.Menu(menu_bar, tearoff=0)
        menu_arquivo.add_command(label="Exportar Logs de Apontamento", command=self.salvar_info_text_em_txt)
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label="Sair", command=self.root.quit)
        menu_bar.add_cascade(label="Arquivo", menu=menu_arquivo)
        ajuda_menu = tk.Menu(menu_bar, tearoff=0)
        ajuda_menu.add_command(label="Sobre", command=self.exibir_sobre)
        menu_bar.add_cascade(label="Ajuda", menu=ajuda_menu)

        # Configura o menu na janela principal
        self.root.config(menu=menu_bar)
        # Aba 1: Informações e Controle
        tab_control = ttk.Notebook(self.root)
        tab1 = ttk.Frame(tab_control)
        tab2 = ttk.Frame(tab_control)
        tab_control.add(tab1, text='Informações e Controle')
        tab_control.add(tab2, text='Configuração')

        # Adiciona um widget Combobox para selecionar o tipo de jiga
        labelComboboxProduto = tk.Label(tab1, text='Produto:', font=("Arial", 12))
        labelComboboxProduto.pack(pady=5)

        produtoDisponivel = [produto for produto in self.produtos.keys()]
        self.entry_tipo_produto = ttk.Combobox(tab1, values=produtoDisponivel, state="readonly", width=30)

        self.entry_tipo_produto.set(produtoDisponivel[0])
        self.entry_tipo_produto.pack(pady=5)

        # Adiciona um widget Combobox para selecionar o tipo de jiga
        labelComboboxJiga = tk.Label(tab1, text='DT-JIGA:', font=("Arial", 12))
        labelComboboxJiga.pack(pady=5)

        jigaDisponivel = [jiga for jiga in self.jigas.keys()]
        self.entry_tipo_jiga = ttk.Combobox(tab1, values=jigaDisponivel, state="readonly", width=30)

        self.entry_tipo_jiga.set(jigaDisponivel[0])
        self.entry_tipo_jiga.pack(pady=5)

        # Aba 1: Informações e Controle
        label_info = tk.Label(tab1, text="Informações geradas pelo programa:")
        label_info.pack(pady=10)

        # Adiciona um widget Text para exibir informações
        self.info_text = tk.Text(tab1, height=10, width=45, bg="white", fg="#333")
        self.info_text.pack(pady=10)

        self.button_executar = tk.Button(tab1, text="Executar", command=self.executar_programa, bg="blue2", fg="white", font=("Arial", 12))
        self.button_executar.pack(pady=10)

        # Aba 2: Configurações
        label_config = tk.Label(tab2, text="Definir Local Arquivo Gerado pelo Software CEABS", font=("Arial", 12))
        label_config.grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        label_origem = tk.Label(tab2, text='Pasta CEABS: ', font=("Arial", 10))
        label_origem.grid(row=1, column=0, pady=5, sticky=tk.W)

        # Adicionando campos de entrada para configurar os caminhos
        self.entry_origem = tk.Entry(tab2, width=50)
        self.entry_origem.insert(0, self.origem_path)
        self.entry_origem.grid(row=2, column=0, pady=5, padx=5)

        # Botão para abrir caixa de diálogo para selecionar novo caminho
        button_selecionar_origem = tk.Button(tab2, text="Selecionar", command=self.selecionar_origem)
        button_selecionar_origem.grid(row=2, column=1, pady=5, padx=5)

        # Botão para salvar configurações
        button_salvar_config = tk.Button(tab2, text="Salvar Configuração", command=self.salvar_configuracoes, bg="dark green", fg="white")
        button_salvar_config.grid(row=3, column=0, pady=10)

        # Adiciona as abas à janela
        tab_control.pack(expand=1, fill="both")

        # Atualiza o destino_path quando um novo produto é selecionado
        self.entry_tipo_produto.bind("<<ComboboxSelected>>", self.atualizar_destino_path)

    def exibir_sobre(self):
        """Exibe a janela com informações sobre o aplicativo."""
        sobre_window = tk.Toplevel(self.root)
        sobre_window.title("Sobre")
        sobre_window.geometry("400x200")
        # sobre_window.config(bg="lightgray")

        # Mensagem de Sobre
        mensagem_sobre = f"""Este é um aplicativo para apontamento \nautomático CEABS.\n\nDesenvolvido em Python por Marcos Tullio.\n\nVersão {self.version}"""

        label_sobre = tk.Label(sobre_window, text=mensagem_sobre, font=("Arial", 10), justify=tk.CENTER)
        label_sobre.pack(pady=20)

        # Botão para fechar a janela "Sobre"
        botao_fechar = tk.Button(sobre_window, text="Fechar", command=sobre_window.destroy, bg="blue", fg="white")
        botao_fechar.pack(pady=10)

    def salvar_info_text_em_txt(self):
        """Salva o conteúdo do widget Text em um arquivo .txt escolhido pelo usuário."""
        try:
            # Obtém o conteúdo do widget Text
            conteudo = self.info_text.get("1.0", tk.END).strip()

            # Verifica se há conteúdo para salvar
            if not conteudo:
                print("O widget Text está vazio. Nada para salvar.")
                self.adicionar_info_e_rolar("O widget Text está vazio. Nada para salvar.", "yellow",
                                            "black")
                return

            # Abre a caixa de diálogo para escolher o local e nome do arquivo
            caminho_destino = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])

            if not caminho_destino:  # Verifica se o usuário cancelou a seleção
                print("Operação de salvamento cancelada.")
                self.adicionar_info_e_rolar("Operação de salvamento cancelada.", "yellow", "black")
                return

            # Salva o conteúdo no arquivo especificado
            with open(caminho_destino, "w", encoding="utf-8") as arquivo:
                arquivo.write(conteudo)

            # Confirmação de salvamento
            print(f"Conteúdo salvo com sucesso em: {caminho_destino}")
            self.adicionar_info_e_rolar(f"Conteúdo salvo em {caminho_destino}.")

        except Exception as e:
            print(f"Erro ao salvar o conteúdo: {e}")
            self.adicionar_info_e_rolar(f"Erro ao salvar o conteúdo: {e}", "yellow", "black")

    def alerta_critico(self, mensagem, caminho_destino):
        """Exibe uma janela de alerta crítica em vermelho."""
        if self.alerta_ativo:
            # Se já há um alerta ativo, adiciona o novo à fila
            self.fila_alertas.append((mensagem, caminho_destino))
            return
        self.alerta_ativo = True
        alerta = tk.Toplevel(self.root)
        alerta.title("Alerta Crítico!")
        alerta.geometry("450x150")
        alerta.config(bg="red3")
        alerta.attributes("-topmost", True)  # Garante que o alerta estará em primeiro plano

        mensagem_label = tk.Label(alerta, text=mensagem, bg="red3", fg="white", font=("Arial", 14, "bold"))
        mensagem_label.pack(pady=20)

        # Frame para os botões
        botoes_frame = tk.Frame(alerta, bg="red3")
        botoes_frame.pack(pady=10)

        botao_gerar = tk.Button(botoes_frame, text="Gerar Log Reprovado",
                                command=lambda: self.gerar_log(alerta, caminho_destino),
                                bg="white", fg="red", font=("Arial", 12))
        botao_gerar.pack(side="left", padx=10)

        botao_cancelar = tk.Button(botoes_frame, text="Cancelar", bg="white", fg="black", font=("Arial", 12),
                                   command=lambda: self.cancelar_acao(alerta))
        botao_cancelar.pack(side="left", padx=10)

        # Liga o evento de fechamento da janela à mesma função de "Cancelar"
        alerta.protocol("WM_DELETE_WINDOW", lambda: self.cancelar_acao(alerta))

    def gerar_log(self, alerta, caminho_destino):
        """Gera o log de falha e exibe a mensagem correspondente."""
        try:
            with open(caminho_destino, 'w') as file:
                file.write("Log de reprovação gerado automaticamente.\n")
            timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            mensagem_info = f'[{timestamp}] - Log gerado em: {caminho_destino}'
            self.adicionar_info_e_rolar(mensagem_info, "red", "white")
            self.encerrar_alerta(alerta)
        except Exception as e:
            mensagem_info = f'Erro ao gerar o log: {e}'
            self.adicionar_info_e_rolar(mensagem_info, "yellow", "black")
        finally:
            alerta.destroy()

    def cancelar_acao(self, alerta):
        """Fecha o alerta crítico sem salvar o log."""
        timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        mensagem_info = f'[{timestamp}] - Ação cancelada. Log não foi gerado.'
        self.adicionar_info_e_rolar(mensagem_info, "yellow", "black")
        self.encerrar_alerta(alerta)
        alerta.destroy()

    def encerrar_alerta(self, alerta):
        """Fecha o alerta atual e verifica se há outros na fila."""
        alerta.destroy()
        self.alerta_ativo = False
        if self.fila_alertas:
            # Exibe o próximo alerta na fila
            proximo_mensagem, proximo_caminho = self.fila_alertas.popleft()
            self.alerta_critico(proximo_mensagem, proximo_caminho)

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
            if caminho_arquivo_original != self.config.get('PATH', 'last_source_file', fallback=None):
                limpar_ultima_posicao_lida()
                self.config.set('PATH', 'last_source_file', caminho_arquivo_original)
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
                executar_script(self)
                time.sleep(1)
        finally:
            # Após o término da execução, atualize o estado dos botões
            self.programa_em_execucao = False
            self.atualizar_estado_botoes()

    def adicionar_info_e_rolar(self, info, bg="white", fg="black"):
        """
        Adiciona informações ao campo de texto e rola até o final, estilizando apenas a linha adicionada.

        Parâmetros:
        - info (str): Mensagem a ser adicionada.
        - bg (str): Cor de fundo da mensagem.
        - fg (str): Cor do texto da mensagem.
        """
        # Gerar uma tag única para esta mensagem
        tag_name = f"tag_{len(self.info_text.get('1.0', tk.END).splitlines())}"

        # Configurar estilo para a tag
        self.info_text.tag_configure(tag_name, background=bg, foreground=fg, wrap="word")

        # Inserir a mensagem e aplicar a tag apenas a ela
        start_index = self.info_text.index(tk.END)  # Posição inicial antes da inserção
        self.info_text.insert(tk.END, "---------------------------------------------")
        self.info_text.insert(tk.END,"\n" + info + "\n")
        self.info_text.insert(tk.END,"---------------------------------------------")
        end_index = self.info_text.index(tk.END)  # Posição final após a inserção
        self.info_text.tag_add(tag_name, start_index, end_index)  # Aplicar a tag à mensagem

        # Rolar até o final
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


VERSION = '4.4.0'


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


def carregar_sufixos(caminho):
    with open(caminho, 'r') as f:
        return json.load(f)


def adiciona_caracteres(data):
    new_data = {}
    for key, value in data.items():
        new_key = f"=\"{key}\""  # Adiciona "=" no início e nas aspas
        if isinstance(value, dict):
            new_data[new_key] = adiciona_caracteres(value)  # Recursão para casos aninhados
        else:
            new_data[new_key] = value
    return new_data


def processar_linhas_novas(self, df, ultima_posicao, diretorio_destino):
    if ultima_posicao >= len(df):
        return

    # Carregar o mapeamento de sufixos e o tipo de jiga
    sufixos = carregar_sufixos('suffix_mapping.json')
    tipo_jiga = app.entry_tipo_jiga.get()
    sufixo_map = adiciona_caracteres(sufixos)

    # Processar as linhas novas a partir da última posição lida
    df_novas = df.iloc[ultima_posicao:]
    for _, row in df_novas.iterrows():
        sufixo_arquivo = '_0000'
        houve_falha = False  # Inicializa como falso (sem falha)

        # Verificar se há falha com base no tipo_jiga
        tipo_jiga_key = f'="{tipo_jiga}"'
        if tipo_jiga_key in sufixo_map:
            for status_col, sufixo in sufixo_map[tipo_jiga_key].items():
                if status_col in row and row[status_col] != '="PASS"':
                    sufixo_arquivo = sufixo
                    houve_falha = True
                    break  # Interrompe ao encontrar a primeira falha

        # Recuperar valores das colunas relevantes
        valor_serial_number = row.get('="SERIAL_NUMBER_VALUE"', None)
        valor_lora_id = row.get('="LoRa_ID_VALUE"', None)

        # Verificar se os valores de serial e LoRa são válidos
        if valor_serial_number and valor_lora_id and valor_serial_number != '="0"' and valor_lora_id != '="0"':
            numeric_part_serial = ''.join(filter(str.isdigit, valor_serial_number))
            numeric_part_lora = ''.join(filter(str.isdigit, valor_lora_id))

            # Montar o caminho do arquivo de destino
            caminho_destino = os.path.join(
                diretorio_destino, f'{int(numeric_part_serial)}ç{int(numeric_part_lora)}{sufixo_arquivo}.txt'
            )

            # Adicionar timestamp à mensagem
            timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

            # Caso tenha havido falha, mostrar alerta crítico
            if houve_falha:
                mensagem = (f"Placa: {numeric_part_serial} foi reprovada.\n"
                            "Deseja gerar log de reprovação?")
                self.alerta_critico(mensagem, caminho_destino)
            else:
                # Gerar automaticamente para casos aprovados
                with open(caminho_destino, 'w') as file:
                    file.write("Placa aprovada com sucesso.\n")
                mensagem_info = f'[{timestamp}] - Arquivo gerado em: {caminho_destino}'
                self.adicionar_info_e_rolar(mensagem_info, "light sky blue", "black")

    # Atualizar a última posição lida e copiar o arquivo para a jiga
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
            mensagem_erro = (f'[{timestamp}] - Caminho para o jiga "{jiga_selecionado}" '
                             f'não encontrado no arquivo de configuração.')
            app.adicionar_info_e_rolar(mensagem_erro, "yellow", "black")
            return

        # Verifique se o diretório de destino do jiga existe, se não, crie-o
        if not os.path.exists(caminho_destino_jiga):
            mensagem_erro = (f'[{timestamp}] - Caminho para backup do jiga "{jiga_selecionado}" '
                             f'não encontrado no arquivo de configuração.')
            app.adicionar_info_e_rolar(mensagem_erro, "yellow", "black")

        # Copie o arquivo original para o diretório do jiga
        try:
            shutil.copy(caminho_arquivo_original, caminho_destino_jiga)
            mensagem_info = f'[{timestamp}] - Arquivo copiado para: {caminho_destino_jiga}'
            app.adicionar_info_e_rolar(mensagem_info, "light grey", "black")
        except Exception as e:
            mensagem_erro = f'[{timestamp}] - Erro ao copiar arquivo para o endereço: {e}.'
            app.adicionar_info_e_rolar(mensagem_erro, "yellow", "black")


def limpar_ultima_posicao_lida():
    salvar_ultima_posicao_lida(0)


def encerrar_programa(signal, frame):
    resposta = messagebox.askyesno("Encerrar Programa", "Tem certeza que deseja encerrar o programa?")
    if resposta:
        observer.stop()
        observer.join()
        root.destroy()


class FileModifiedHandler(FileSystemEventHandler):
    def __init__(self, app, intervalo_estabilidade=10, timeout_maximo=60):
        self.app = app
        self.intervalo_estabilidade = intervalo_estabilidade
        self.timeout_maximo = timeout_maximo
        self.ultima_modificacao = None
        self.thread_verificacao = None

    def on_modified(self, event):
        if event.is_directory:
            return
        elif event.event_type == 'modified':
            print(f'Arquivo {event.src_path} foi modificado. Verificando estabilidade...')
            self.ultima_modificacao = time.time()  # Registra o momento da última modificação

            # Inicia uma thread para verificar a estabilidade após o intervalo
            if self.thread_verificacao is None or not self.thread_verificacao.is_alive():
                self.thread_verificacao = threading.Thread(
                    target=self.verificar_estabilidade,
                    args=(event.src_path,),
                    daemon=True
                )
                self.thread_verificacao.start()

    def verificar_estabilidade(self, caminho_arquivo):
        """
        Verifica se o arquivo permanece inalterado por um intervalo de tempo.
        """
        start_time = time.time()
        while time.time() - start_time < self.timeout_maximo:
            if self.ultima_modificacao and (time.time() - self.ultima_modificacao >= self.intervalo_estabilidade):
                print(f'Arquivo {caminho_arquivo} está estável. Processando...')
                self.app.executar_programa()
                break  # Sai do loop após processar o arquivo
            time.sleep(1)  # Verifica a cada 1 segundo
        else:
            print(f"Timeout: Arquivo {caminho_arquivo} não se tornou estável após {self.timeout_maximo} segundos.")

def executar_script(self):
    if verificar_existencia_arquivo_original():
        df_original = ler_arquivo_original()

        if df_original is not None:
            ultima_posicao = obter_ultima_posicao_lida()
            processar_linhas_novas(self, df_original, ultima_posicao, app.destino_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = MyApp(root)

    observer = Observer()
    event_handler = FileModifiedHandler(app, intervalo_estabilidade=30, timeout_maximo=120) #melhorado

    observer.schedule(event_handler, path=app.origem_path, recursive=False)
    observer.start()

    root.protocol("WM_DELETE_WINDOW", lambda: encerrar_programa(None, None))
    root.mainloop()
