import tkinter as tk
from tkinter import messagebox
from pymongo import MongoClient
import os
from datetime import datetime


class MyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Verificador de Logs")
        self.root.geometry("400x200")

        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.iniciar_verificacao()

    def iniciar_verificacao(self):
        # Conectar ao MongoDB e buscar logs
        logs = self.buscar_logs()
        self.processar_logs(logs)

    def buscar_logs(self):
        client = MongoClient('mongodb://localhost:27017/')
        db = client['CEABSdb']
        collection = db['colecao_teste']

        # Buscar os logs mais recentes
        logs = collection.find().sort("timestamp", -1).limit(10)  # Limitar os últimos 10 logs
        return list(logs)

    def processar_logs(self, logs):
        for log in logs:
            resultado = self.verificar_aprovacao(log)
            if resultado['aprovado']:
                self.gerar_txt(log['serial_number'], '_0000')
            else:
                self.exibir_alerta_reprovacao(log['serial_number'], resultado['sufixo'])

    def verificar_aprovacao(self, log):
        # Implementar lógica de verificação
        falhas = {
            'teste1': log.get('teste1'),
            'teste2': log.get('teste2'),
            # Adicione outros testes conforme necessário
        }

        for teste, resultado in falhas.items():
            if resultado != 'PASS':
                return {'aprovado': False, 'sufixo': f"_{teste}"}

        return {'aprovado': True}

    def exibir_alerta_reprovacao(self, serial_number, sufixo):
        # Mudar a cor da interface
        self.frame.configure(bg='red')

        # Perguntar se deseja retestar
        retestar = messagebox.askyesno(
            "Atenção",
            f"A placa {serial_number} foi reprovada. Deseja retestar?"
        )

        if retestar:
            self.frame.configure(bg='white')  # Resetar a cor se retestar
            # Aqui você pode adicionar lógica para iniciar o reteste
        else:
            self.gerar_txt(serial_number, sufixo)

    def gerar_txt(self, serial_number, sufixo):
        diretorio_destino = "caminho/do/diretorio/destino"
        caminho_destino = os.path.join(diretorio_destino, f"{serial_number}{sufixo}.txt")

        # Criar o arquivo
        with open(caminho_destino, 'w') as f:
            f.write(f"Log para o serial {serial_number} - Sufixo: {sufixo}\n")

        timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        print(f"[{timestamp}] - Arquivo gerado em: {caminho_destino}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MyApp(root)
    root.mainloop()
