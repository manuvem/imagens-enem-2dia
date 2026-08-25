import os
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def cor_similar(pixel, cor_alvo, tolerancia=20):
    """Verifica se a cor RGB de um pixel está dentro da tolerância."""
    if isinstance(pixel, int):
        return False

    r, g, b = pixel[:3]
    return (
        abs(r - cor_alvo[0]) <= tolerancia
        and abs(g - cor_alvo[1]) <= tolerancia
        and abs(b - cor_alvo[2]) <= tolerancia
    )


def validar_faixa(
    pixels, x, y_inicio, altura_imagem, altura_min, altura_max, cor_alvo, tolerancia=20
):
    """Avança verticalmente no pixel (x, y) verificando a extensão da cor."""
    y = y_inicio
    altura_encontrada = 0

    while y < altura_imagem:
        if cor_similar(pixels[x, y], cor_alvo, tolerancia):
            altura_encontrada += 1
            y += 1
            if altura_encontrada > altura_max:
                return 0
        else:
            break

    if altura_encontrada >= altura_min:
        return altura_encontrada
    return 0


def encontrar_padroes_corte(imagem, tolerancia=20):
    """
    Varre a última coluna da direita buscando a sequência de 3 faixas.
    Retorna uma lista simples com as coordenadas Y onde a imagem deve ser cortada.
    """
    largura, altura = imagem.size
    pixels = imagem.load()

    cor_1 = (255, 252, 191)
    cor_2 = (255, 254, 230)
    cor_3 = (255, 252, 191)

    pontos_corte = []
    coluna_x = largura - 1

    if coluna_x < 0:
        return pontos_corte

    y = 0
    while y < altura:
        # CORREÇÃO DE FALSO POSITIVO:
        # Garante que 'y' seja o INÍCIO REAL da faixa, e não o meio de um bloco longo.
        if y > 0 and cor_similar(pixels[coluna_x, y - 1], cor_1, tolerancia):
            y += 1
            continue

        # Faixa 1: target 10px (8 a 12px)
        h1 = validar_faixa(pixels, coluna_x, y, altura, 8, 12, cor_1, tolerancia)
        if h1 > 0:
            # Faixa 2: target 7px (5 a 9px)
            h2 = validar_faixa(pixels, coluna_x, y + h1, altura, 5, 9, cor_2, tolerancia)
            if h2 > 0:
                # Faixa 3: target 4px (2 a 6px)
                h3 = validar_faixa(pixels, coluna_x, y + h1 + h2, altura, 2, 6, cor_3, tolerancia)
                if h3 > 0:
                    h_total = h1 + h2 + h3

                    # Define o corte 13 pixels antes do início do padrão
                    corte_y = max(0, y - 13)
                    pontos_corte.append(corte_y)

                    print(f"Padrão encontrado em y={y}. Corte realizado em y={corte_y}")

                    y += h_total
                    continue

            # Se h1 foi válido mas h2/h3 falharam, salta h1 para economizar processamento
            y += h1
            continue

        y += 1

    return pontos_corte


def dividir_imagem_por_faixas(caminho_imagem, pasta_saida):
    if not os.path.exists(caminho_imagem):
        print(f"Erro: O arquivo '{caminho_imagem}' não foi encontrado!")
        return

    imagem = Image.open(caminho_imagem).convert("RGB")
    largura, altura = imagem.size

    print(f"--- Processando imagem: {largura}x{altura} pixels ---")

    pontos_corte = encontrar_padroes_corte(imagem)

    if not pontos_corte:
        print("Nenhum padrão visual foi encontrado para realizar os cortes.")
        return

    os.makedirs(pasta_saida, exist_ok=True)

    posicao_inicio = 0
    contador = 1

    # Recorta os blocos com base nas coordenadas Y de corte
    for corte_y in pontos_corte:
        if corte_y > posicao_inicio:
            area_corte = (0, posicao_inicio, largura, corte_y)
            secao = imagem.crop(area_corte)

            nome_arquivo = f"parte_{contador:03d}.png"
            caminho_completo = os.path.join(pasta_saida, nome_arquivo)
            secao.save(caminho_completo)
            print(f"-> Salvo: {nome_arquivo} [{secao.width}x{secao.height}px]")

            contador += 1
            posicao_inicio = corte_y

    # Salva o último bloco restante até a base da imagem
    if posicao_inicio < altura:
        area_corte = (0, posicao_inicio, largura, altura)
        secao = imagem.crop(area_corte)

        nome_arquivo = f"parte_{contador:03d}.png"
        caminho_completo = os.path.join(pasta_saida, nome_arquivo)
        secao.save(caminho_completo)
        print(f"-> Salvo bloco final: {nome_arquivo} [{secao.width}x{secao.height}px]")


if __name__ == "__main__":
    caminho_imagem = "colunas_concatenadas_verticalmente.png"
    pasta_saida = "saida_questoes"

    dividir_imagem_por_faixas(caminho_imagem, pasta_saida)
    print("\nProcesso de divisão concluído com sucesso!")

