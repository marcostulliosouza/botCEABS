import tkinter as tk
from tkinter import messagebox
from pymongo import MongoClient


class MeuAplicativo:
    def __init__(self, master):
        self.master = master
        self.master.title("Verificador de Seriais")

        # Conexão com o MongoDB
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['CEABSdb']
        self.collection = self.db['colecao_teste']

        # Campo de entrada para tipo de jiga
        self.label_tipo_jiga = tk.Label(master, text="Modelo da Jiga:")
        self.label_tipo_jiga.pack()
        self.entry_tipo_jiga = tk.Entry(master)
        self.entry_tipo_jiga.pack()

        # Botão para verificar o último serial
        self.button_verificar = tk.Button(master, text="Verificar Último Serial", command=self.verificar_ultimo_serial)
        self.button_verificar.pack()

        # Área de texto para exibir informações
        self.text_info = tk.Text(master, height=10, width=50)
        self.text_info.pack()

    def adicionar_info(self, mensagem):
        self.text_info.insert(tk.END, mensagem + "\n")
        self.text_info.see(tk.END)

    def verificar_ultimo_serial(self):
        # Busca os últimos itens adicionados na coleção
        ultimos_itens = self.collection.find().sort("_id", -1).limit(10)
        for registro in ultimos_itens:
            self.verificar_serial_no_banco(registro)

    def verificar_serial_no_banco(self, registro):
        serial = registro.get("SERIAL_NUMBER_VALUE", "0")
        print(registro)
        falhas = self.verificar_todas_etapas_pass(registro)

        modelo_jiga = self.entry_tipo_jiga.get()
        if falhas:
            # Se houver falhas, gera arquivo com código de falha
            for falha in falhas:
                sufixo_falha = self.obter_sufixo_falha(modelo_jiga, falha)
                if sufixo_falha:
                    nome_arquivo = f"{serial}_{sufixo_falha}.txt"
                    with open(nome_arquivo, 'w') as arquivo:
                        arquivo.write(f'Serial: {serial} - Falhou no teste {falha}!\n')
                    self.adicionar_info(f"Arquivo {nome_arquivo} gerado com falha!")
                    break  # Para não gerar múltiplos arquivos de falha
        else:
            # Se todas as etapas passaram, gera arquivo com serial
            nome_arquivo = f"{serial}_0000.txt"
            with open(nome_arquivo, 'w') as arquivo:
                arquivo.write(f'Serial: {serial} - Todas as etapas passaram!\n')
            self.adicionar_info(f"Arquivo {nome_arquivo} gerado com sucesso!")

    def verificar_todas_etapas_pass(self, registro):
        # Lista de testes a serem verificados
        testes = [
            'LoRa_ID_STATUS',
            'POWER_TEST',
            'V1_TEST',
            'V3_TEST',
            'V4_TEST',
            'V5_TEST',
            'UART_TEST',
            'FIRMWARE_VERSION_TEST',
            'GPIO_TEST',
            'ADC_TEST',
            'LoRa_TEST',
            '1-WIRE_TEST',
            'GSM_TEST',
            'GPS_TEST',
            'SETUP_DOWNLOAD',
            'LoRa_APP_EUI_STATUS',
            'LoRa_APP_SESSION_KEY_STATUS',
            'LoRa_DEV_ADDRESS_STATUS',
            'LoRa_DEV_EUI_STATUS',
            'LoRa_NTWK_SESSION_KEY_STATUS'
        ]

        falhas = []
        for teste in testes:
            if registro.get(teste) != "PASS":
                falhas.append(teste)  # Adiciona teste que falhou

        return falhas  # Retorna a lista de testes que falharam

    def obter_sufixo_falha(self, modelo_jiga, teste):
        # Mapeia o modelo da jiga e teste para o sufixo correspondente
        sufixo_map = {
            '001004': {
                'LoRa_ID_STATUS': '6460',
                'POWER_TEST': '6461',
                'V1_TEST': '6462',
                'V3_TEST': '6463',
                'V4_TEST': '6464',
                'V5_TEST': '6465',
                'UART_TEST': '6466',
                'FIRMWARE_VERSION_TEST': '6467',
                'GPIO_TEST': '6468',
                'ADC_TEST': '6469',
                'LoRa_TEST': '6470',
                '1-WIRE_TEST': '6471',
                'GSM_TEST': '6472',
                'GPS_TEST': '6473',
                'SETUP_DOWNLOAD': '6474',
                'LoRa_APP_EUI_STATUS': '6475',
                'LoRa_APP_SESSION_KEY_STATUS': '6476',
                'LoRa_DEV_ADDRESS_STATUS': '6477',
                'LoRa_DEV_EUI_STATUS': '6478',
                'LoRa_NTWK_SESSION_KEY_STATUS': '6479'
            },
            # Adicione os outros modelos aqui
        }

        # Retorna o sufixo correspondente se o modelo e o teste existirem
        return sufixo_map.get(modelo_jiga, {}).get(teste, None)


if __name__ == "__main__":
    root = tk.Tk()
    app = MeuAplicativo(root)
    root.mainloop()
