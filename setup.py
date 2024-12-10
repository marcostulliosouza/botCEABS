# setup.py
from cx_Freeze import setup, Executable
from botLog import VERSION

# Lista de módulos que você está usando no seu script
modules = ["pandas", "datetime", "os", "time", "watchdog", "tkinter", "threading", "configparser", "csv", "shutil"]

# Inclua automaticamente todos os pacotes necessários
packages = ["encodings"]

# Se o seu aplicativo usa arquivos adicionais, especifique-os aqui
include_files = ["ico-botlog.ico", "config.ini", "suffix_mapping.json"]

# Configuração do executável
executables = [Executable("botLog.py", base="Win32GUI")]

setup(
    name="botLog",
    version=VERSION,
    options={
        "build_exe": {
            "packages": modules + packages,
            "include_files": include_files,
            "include_msvcr": True,
        }
    },
    executables=executables
)