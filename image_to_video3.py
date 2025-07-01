import os
import sys
import numpy as np
from PIL import Image
from moviepy.editor import ImageClip
import tkinter as tk
from tkinter import filedialog
import subprocess

def aplicar_zoom_suave(clip, zoom_ratio=0.04):
    def efeito_zoom(get_frame, t):
        img = Image.fromarray(get_frame(t))
        base_size = img.size

        # Calcula o novo tamanho
        new_size = (
            round(base_size[0] * (1 + (zoom_ratio * t))),
            round(base_size[1] * (1 + (zoom_ratio * t)))
        )

        # Garante que as dimensões sejam pares
        new_size = (
            new_size[0] + (new_size[0] % 2),
            new_size[1] + (new_size[1] % 2)
        )

        # Redimensiona a imagem
        img = img.resize(new_size, Image.LANCZOS)

        # Calcula as coordenadas para recortar a imagem de volta ao tamanho original
        x = round((new_size[0] - base_size[0]) / 2)
        y = round((new_size[1] - base_size[1]) / 2)
        img = img.crop((x, y, x + base_size[0], y + base_size[1]))

        return np.array(img)

    return clip.fl(efeito_zoom)

def selecionar_imagens():
    root = tk.Tk()
    root.withdraw()  # Oculta a janela principal
    caminhos_imagens = filedialog.askopenfilenames(
        title="Selecione as imagens",
        filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("Todos os arquivos", "*.*")]
    )
    return list(caminhos_imagens)

def copiar_metadados(origem, destino):
    try:
        res = subprocess.run(
            ["exiftool", "-overwrite_original", "-tagsfromfile", str(origem), str(destino)],
            capture_output=True, text=True
        )
        if res.returncode != 0:
            print(f"Erro ao copiar metadados: {res.stderr}")
        else:
            print(f"Metadados copiados de {origem} para {destino}")
    except FileNotFoundError:
        print("Aviso: ExifTool não encontrado. Os metadados não serão copiados.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao usar o ExifTool: {e}")

def main():
    # Configurações
    fps = 24
    duracao = 8  # duração de cada imagem em segundos
    zoom_ratio = 0.02  # taxa de zoom por segundo

    # Seleciona as imagens
    caminhos_imagens = selecionar_imagens()
    if not caminhos_imagens:
        print("Nenhuma imagem selecionada.")
        return

    for caminho_imagem in caminhos_imagens:
        nome_imagem = os.path.basename(caminho_imagem)
        pasta_imagem = os.path.dirname(caminho_imagem)
        pasta_video = os.path.join(pasta_imagem, "video_4k")
        os.makedirs(pasta_video, exist_ok=True)

        # Arquivo de controle na pasta de saída
        arquivo_controle = os.path.join(pasta_video, "videos_processados.txt")

        # Lê o arquivo de controle para obter a lista de imagens já processadas
        if os.path.exists(arquivo_controle):
            with open(arquivo_controle, "r", encoding="utf-8") as f:
                processados = set(linha.strip() for linha in f)
        else:
            processados = set()

        if nome_imagem in processados:
            print(f"Imagem já processada: {nome_imagem}")
            continue

        if not os.path.isfile(caminho_imagem):
            print(f"Arquivo não encontrado: {caminho_imagem}")
            continue

        try:
            print(f"Processando: {nome_imagem}")
            clip = ImageClip(caminho_imagem, duration=duracao)
            clip = aplicar_zoom_suave(clip, zoom_ratio=zoom_ratio)
            clip = clip.set_position('center')

            nome_video = os.path.splitext(nome_imagem)[0] + "_zoom.mp4"
            caminho_video = os.path.join(pasta_video, nome_video)

            clip.write_videofile(caminho_video, fps=fps, codec='libx264', bitrate="20M")

            # Copia os metadados da imagem para o vídeo
            copiar_metadados(caminho_imagem, caminho_video)

            # Atualiza o arquivo de controle
            with open(arquivo_controle, "a", encoding="utf-8") as f:
                f.write(nome_imagem + "\n")

        except Exception as e:
            print(f"Erro ao processar {nome_imagem}: {e}")

if __name__ == "__main__":
    main()
