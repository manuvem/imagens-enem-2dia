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
    Varre o penúltimo pixel da direita buscando a sequência de 3 faixas.
    Retorna pares com (fim_da_questao_atual, inicio_da_proxima_questao).
    """
    largura, altura = imagem.size
    pixels = imagem.load()

    cor_1 = (255, 252, 191)
    cor_2 = (255, 254, 230)
    cor_3 = (255, 252, 191)

    intervalos_corte = []

    coluna_x = largura - 2
    if coluna_x < 0:
        return intervalos_corte

    y = 0
    while y < altura:
        h1 = validar_faixa(pixels, coluna_x, y, altura, 10, 10, cor_1, tolerancia)
        if h1 > 0:
            h2 = validar_faixa(pixels, coluna_x, y + h1, altura, 7, 7, cor_2, tolerancia)
            if h2 > 0:
                h3 = validar_faixa(pixels, coluna_x, y + h1 + h2, altura, 4, 4, cor_3, tolerancia)
                if h3 > 0:
                    h_total = h1 + h2 + h3
                    # Recorta a questão anterior 10px antes da faixa
                    fim_questao = max(0, y - 10)
                    # Inicia a próxima questão 10px depois que a faixa termina
                    inicio_proxima = min(altura, y + h_total + 10)

                    intervalos_corte.append((fim_questao, inicio_proxima))

                    print(f"Divisor encontrado em y={y}. Fim da questão em y={fim_questao}, início da próxima em y={inicio_proxima}")

                    y += h_total
                    continue

        y += 1

    return intervalos_corte


def dividir_imagem_por_faixas(caminho_imagem, pasta_saida):
    if not os.path.exists(caminho_imagem):
        print(f"Erro: O arquivo '{caminho_imagem}' não foi encontrado!")
        return

    imagem = Image.open(caminho_imagem).convert("RGB")
    largura, altura = imagem.size

    print(f"--- Processando imagem: {largura}x{altura} pixels ---")

    intervalos_corte = encontrar_padroes_corte(imagem)

    if not intervalos_corte:
        print("Nenhum padrão visual foi encontrado para realizar os cortes.")
        return

    os.makedirs(pasta_saida, exist_ok=True)

    posicao_inicio = 0
    contador = 1

    # Recorta individualmente cada questão isolada entre as faixas divisa
    for fim_questao, inicio_proxima in intervalos_corte:
        if fim_questao > posicao_inicio:
            area_corte = (0, posicao_inicio, largura, fim_questao)
            secao = imagem.crop(area_corte)

            nome_arquivo = f"parte_{contador:03d}.png"
            caminho_completo = os.path.join(pasta_saida, nome_arquivo)
            secao.save(caminho_completo)
            print(f"-> Salvo: {nome_arquivo} [{secao.width}x{secao.height}px]")

            contador += 1

        # Salta a faixa divisória amarela para iniciar a próxima questão limpa
        posicao_inicio = inicio_proxima

    # Salva a última questão (do final do último padrão até a base da imagem)
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

