import http.server  # servidor HTTP básico do Python
import json         # serializa e desserializa dados JSON
import socketserver # cria o socket TCP que aceita conexões de rede

# Este projeto implementa ChaCha20 em Python puro, sem bibliotecas externas.
# O servidor Python serve apenas dados JSON e arquivos estáticos.
# Toda a interface de usuário fica em index.html e o Python não gera HTML.
# O backend usa HTTP sobre TCP para comunicar com o navegador.

# NONCE fixo apenas para este exemplo. Em um uso real, o nonce deve ser diferente para cada mensagem.
NONCE = b"123456789012"


def rotacionar_esquerda(valor, casas):
    # Rotaciona os bits do valor para a esquerda dentro de 32 bits.
    # Esse é um passo comum em algoritmos de cifra para misturar os bits.
    return ((valor << casas) & 0xFFFFFFFF) | (valor >> (32 - casas))


def quarter_round(estado, a, b, c, d):
    # Executa um quarter round do ChaCha20 usando quatro palavras do estado.
    # O ChaCha20 mistura os valores em blocos de 32 bits para espalhar dependências.
    # Cada operação combina soma modular, XOR e rotação para criar mistura não linear.
    # Variáveis:
    # - estado: lista de 16 inteiros de 32 bits que representam o estado atual.
    # - a, b, c, d: índices que apontam para quatro posições do estado.

    # Primeiro, mistura a e b com adição modular.
    # A soma faz com que cada bit de a dependa de b e vice-versa.
    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF

    # Depois, mistura o resultado em d via XOR e rotação.
    # O XOR introduz dependência entre os bits de d e a.
    # A rotação espalha esses bits, impedindo que padrões simples se preservem.
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 16)

    # Em seguida, adiciona d em c.
    # Essa segunda adição modular mistura ainda mais as palavras.
    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF

    # Mistura c em b com XOR e rotação de 12 bits.
    # A rotação torna a operação não comutativa e dispersa os bits.
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 12)

    # Repete a adição em a para propagar a mistura.
    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF

    # XOR e rotação em d novamente, agora usando o novo a.
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 8)

    # Adiciona d em c pela segunda vez.
    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF

    # Finaliza o quarter round misturando c em b com rotação de 7 bits.
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 7)


def bloco_chacha20(chave, nonce, contador):
    # Gera um bloco de 64 bytes do fluxo ChaCha20.
    # O estado inicial tem 16 palavras de 32 bits:
    # - 4 constantes fixas
    # - 8 palavras da chave de 32 bytes
    # - 1 palavra do contador de bloco
    # - 3 palavras do nonce de 12 bytes
    # O contador e o nonce fazem cada bloco ser único.
    estado = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]

    # A chave de 32 bytes é dividida em palavras de 4 bytes em little-endian.
    # ChaCha20 trabalha com operações de 32 bits, por isso convertemos a chave assim.
    for i in range(0, 32, 4):
        estado.append(int.from_bytes(chave[i:i + 4], "little"))

    # Adiciona o contador do bloco.
    # Ele garante que cada bloco tenha um fluxo único, mesmo com a mesma chave e nonce.
    estado.append(contador)

    # Adiciona o nonce de 12 bytes em três palavras little-endian.
    # O nonce deve ser diferente entre mensagens para evitar reutilização de fluxo.
    for i in range(0, 12, 4):
        estado.append(int.from_bytes(nonce[i:i + 4], "little"))

    # Copia o estado inicial para o trabalho, que será transformado.
    # O estado original é preservado para a soma final.
    trabalho = estado.copy()

    # Aplica 10 rodadas do ChaCha20.
    # Cada rodada contém 8 quarter rounds: 4 em colunas e 4 em diagonais.
    # Isso garante que todos os 16 valores do estado se misturem.
    for _ in range(10):
        quarter_round(trabalho, 0, 4, 8, 12)
        quarter_round(trabalho, 1, 5, 9, 13)
        quarter_round(trabalho, 2, 6, 10, 14)
        quarter_round(trabalho, 3, 7, 11, 15)
        quarter_round(trabalho, 0, 5, 10, 15)
        quarter_round(trabalho, 1, 6, 11, 12)
        quarter_round(trabalho, 2, 7, 8, 13)
        quarter_round(trabalho, 3, 4, 9, 14)

    # Soma o estado original com o estado transformado para produzir o bloco final.
    # Isso preserva parte do estado original e adiciona uma camada extra de mistura.
    # `bytearray()` cria um buffer vazio mutável de bytes, que podemos preencher
    # com mais bytes usando `extend()` antes de converter para `bytes`.
    resultado = bytearray()
    for i in range(16):
        numero = (trabalho[i] + estado[i]) & 0xFFFFFFFF
        resultado.extend(numero.to_bytes(4, "little"))

    return bytes(resultado)


def criptografar(chave, nonce, texto):
    # Aplica o fluxo ChaCha20 sobre o texto usando XOR.
    # ChaCha20 gera um fluxo pseudoaleatório a partir de chave + nonce + contador.
    # Cada byte do texto é combinado com o byte correspondente do fluxo.
    # A operação XOR é reversível: aplicar duas vezes com o mesmo fluxo retorna o original.
    # Isso significa que a mesma função serve para cifrar e decifrar.
    # `bytearray()` cria um buffer vazio mutável de bytes, que permite usar
    # `append()` para adicionar o resultado da operação XOR e só depois converter
    # para `bytes` na saída.
    resultado = bytearray()

    # Processa o texto em blocos de 64 bytes.
    # Cada bloco usa um contador diferente para gerar um fluxo distinto.
    for bloco_inicio in range(0, len(texto), 64):
        fluxo = bloco_chacha20(chave, nonce, bloco_inicio // 64)
        parte_texto = texto[bloco_inicio:bloco_inicio + 64]

        for i, byte_texto in enumerate(parte_texto):
            resultado.append(byte_texto ^ fluxo[i])

    return bytes(resultado)


def preparar_chave(chave):
    # Converte a chave legível para exatamente 32 bytes.
    # ChaCha20 exige uma chave de 32 bytes (256 bits).
    # Se a chave for menor, repetimos seu conteúdo para preencher 32 bytes.
    # Isso evita erros de tamanho e mantém o processo simples.
    chave_bytes = chave.encode("utf-8")
    if len(chave_bytes) < 32:
        chave_bytes = (chave_bytes * ((32 // len(chave_bytes)) + 1))[:32]
    return chave_bytes[:32]


def gerar_chave_aleatoria():
    # Gera uma chave de 10 caracteres sem usar bibliotecas externas.
    # Essa chave é única para cada mensagem criptografada.
    # Variáveis principais:
    # - codigo: os bytes do próprio arquivo, usados como fonte de entropia.
    # - valor: acumulador que mistura os bytes do código e o id de um novo objeto.
    # - caracteres: conjunto de caracteres hexadecimais usados na chave.
    # - chave: string final de 10 caracteres.
    codigo = open(__file__, "rb").read()
    valor = 0
    for byte in codigo:
        valor = ((valor << 5) - valor + byte) & 0xFFFFFFFF

    valor ^= id(object()) & 0xFFFFFFFF
    caracteres = "0123456789abcdef"
    chave = ""
    for _ in range(10):
        valor = (valor * 1664525 + 1013904223) & 0xFFFFFFFF
        chave += caracteres[valor % len(caracteres)]

    return chave


def responder_json(handler, dados, status=200):
    # Envia uma resposta JSON para o frontend.
    # O frontend usa fetch para fazer a requisição e espera dados em JSON.
    # JSON é útil porque é um formato leve e fácil de ler no JavaScript.
    resposta = json.dumps(dados).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(resposta)))
    handler.end_headers()
    handler.wfile.write(resposta)


class ChaChaHandler(http.server.SimpleHTTPRequestHandler):
    # Classe que trata requisições HTTP.
    # - GET serve a página estática index.html.
    # - POST em /crypt executa a cifra ChaCha20 e retorna JSON.
    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
            return super().do_GET()
        return super().do_GET()

    def do_POST(self):
        # Apenas a rota /crypt é aceita para processar criptografia/descriptografar.
        if self.path != "/crypt":
            self.send_error(404, "Not found")
            return

        # Lê o corpo da requisição JSON enviado pelo frontend.
        # O frontend usa fetch para enviar um objeto { action, text, key }.
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(tamanho).decode("utf-8")

        try:
            dados = json.loads(corpo)
        except ValueError:
            responder_json(self, {"mensagem": "Formato JSON inválido.", "resultado": ""}, 400)
            return

        # action define se vamos criptografar ou descriptografar.
        # text é o texto digitado pelo usuário.
        # key é a chave usada no ChaCha20 para descriptografa ou a chave exibida no encrypt.
        acao = dados.get("action", "")
        texto = dados.get("text", "")
        chave = dados.get("key", "").strip()

        if not texto:
            responder_json(self, {"mensagem": "Por favor, digite um texto.", "resultado": ""}, 400)
            return

        if acao == "encrypt":
            chave = gerar_chave_aleatoria()
        elif acao == "decrypt":
            if not chave:
                responder_json(self, {"mensagem": "Por favor, informe a chave usada na criptografia.", "resultado": ""}, 400)
                return
        else:
            responder_json(self, {"mensagem": "Ação inválida.", "resultado": ""}, 400)
            return

        chave_bytes = preparar_chave(chave)

        try:
            if acao == "encrypt":
                texto_bytes = texto.encode("utf-8")
                cifrado = criptografar(chave_bytes, NONCE, texto_bytes)
                responder_json(self, {"mensagem": "Texto criptografado.", "resultado": cifrado.hex(), "key": chave})
                return

            if acao == "decrypt":
                texto_bytes = bytes.fromhex(texto.strip())
                decifrado = criptografar(chave_bytes, NONCE, texto_bytes)
                responder_json(self, {"mensagem": "Texto descriptografado.", "resultado": decifrado.decode("utf-8")})
                return

            responder_json(self, {"mensagem": "Ação inválida.", "resultado": ""}, 400)
        except ValueError:
            # Erro ao converter o texto hexadecimal ou ao ler dados inválidos.
            responder_json(self, {"mensagem": "Texto inválido. Use hexadecimal correto.", "resultado": ""}, 400)
        except UnicodeDecodeError:
            # Erro ao decodificar o texto descriptografado de volta para UTF-8.
            responder_json(self, {"mensagem": "Chave incorreta ou texto corrompido.", "resultado": ""}, 400)

    def log_message(self, format, *args):
        # Suprime logs de acesso no console para deixar a saída mais limpa.
        return


def main():
    # Inicia o servidor HTTP na porta 8000.
    # Ele atende o frontend estático e a rota /crypt para a API de criptografia.
    # O servidor HTTP roda sobre TCP, por isso usamos socketserver.TCPServer.
    # Sem TCPServer, não haveria escuta de conexões de rede para receber requisições.
    porta = 8000
    endereco = ("", porta)

    with socketserver.TCPServer(endereco, ChaChaHandler) as servidor:
        print(f"Servidor rodando em http://localhost:{porta}")
        print("Abra http://localhost:8000 no navegador.")
        servidor.serve_forever()


if __name__ == "__main__":
    main()
