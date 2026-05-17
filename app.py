import http.server  # servidor HTTP básico do Python
import json         # serializa e desserializa dados JSON
import socketserver # roda um servidor TCP simples para atender o navegador

# Este projeto implementa ChaCha20 em Python puro, sem bibliotecas externas.
# A interface agora fica em index.html, e o Python só responde dados.

# NONCE fixo apenas para este exemplo. Em um uso real, o nonce deve ser diferente para cada mensagem.
NONCE = b"123456789012"

# Armazena a chave gerada aleatoriamente na sessão
chave_sessao = None


def rotacionar_esquerda(valor, casas):
    # Rotaciona os bits do valor para a esquerda dentro de 32 bits.
    # Esse é um passo comum em algoritmos de cifra para misturar os bits.
    return ((valor << casas) & 0xFFFFFFFF) | (valor >> (32 - casas))


def quarter_round(estado, a, b, c, d):
    # Executa um quarter round do ChaCha20 usando quatro palavras do estado.
    # O ChaCha20 mistura os valores em blocos de 32 bits para espalhar dependências.
    # Cada operação é desenhada para combinar não linearidade e difusão.

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
    # Inicializa o estado com as constantes do ChaCha20.
    # Essas constantes são fixas para o algoritmo e evitam que o estado
    # inicial seja apenas a chave, tornando o fluxo mais seguro.
    estado = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]

    # Adiciona a chave de 32 bytes em palavras little-endian.
    # Cada 4 bytes da chave viram um inteiro de 32 bits.
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
    resultado = bytearray()
    for i in range(16):
        numero = (trabalho[i] + estado[i]) & 0xFFFFFFFF
        resultado.extend(numero.to_bytes(4, "little"))

    return bytes(resultado)


def criptografar(chave, nonce, texto):
    # Aplica o fluxo ChaCha20 sobre o texto usando XOR.
    # ChaCha20 produz um fluxo de bytes pseudoaleatórios.
    # Cada byte do texto é combinado com o byte correspondente do fluxo.
    # A operação XOR é reversível: aplicar duas vezes com o mesmo fluxo retorna o original.
    resultado = bytearray()

    # Processa o texto em blocos de 64 bytes.
    for bloco_inicio in range(0, len(texto), 64):
        fluxo = bloco_chacha20(chave, nonce, bloco_inicio // 64)
        parte_texto = texto[bloco_inicio:bloco_inicio + 64]

        for i, byte_texto in enumerate(parte_texto):
            resultado.append(byte_texto ^ fluxo[i])

    return bytes(resultado)


def preparar_chave(chave):
    # Converte a chave de texto para exatamente 32 bytes.
    # Se a chave for menor, ela é repetida até atingir 32 bytes.
    chave_bytes = chave.encode("utf-8")
    if len(chave_bytes) < 32:
        chave_bytes = (chave_bytes * ((32 // len(chave_bytes)) + 1))[:32]
    return chave_bytes[:32]


def gerar_chave_aleatoria():
    # Gera uma chave de 10 caracteres usando apenas operações do Python.
    # A chave é baseada no próprio código e em um id de objeto novo.
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
    # Retorna um JSON com a resposta para o frontend.
    resposta = json.dumps(dados).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(resposta)))
    handler.end_headers()
    handler.wfile.write(resposta)


class ChaChaHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
            return super().do_GET()
        return super().do_GET()

    def do_POST(self):
        global chave_sessao

        if self.path != "/crypt":
            self.send_error(404, "Not found")
            return

        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(tamanho).decode("utf-8")

        try:
            dados = json.loads(corpo)
        except ValueError:
            responder_json(self, {"mensagem": "Formato JSON inválido.", "resultado": ""}, 400)
            return

        acao = dados.get("action", "")
        texto = dados.get("text", "")

        if not texto:
            responder_json(self, {"mensagem": "Por favor, digite um texto.", "resultado": ""}, 400)
            return

        if acao == "encrypt":
            if not chave_sessao:
                chave_sessao = gerar_chave_aleatoria()
        elif acao == "decrypt":
            if not chave_sessao:
                responder_json(self, {"mensagem": "Nenhuma chave disponível para descriptografar.", "resultado": ""}, 400)
                return
        else:
            responder_json(self, {"mensagem": "Ação inválida.", "resultado": ""}, 400)
            return

        chave_bytes = preparar_chave(chave_sessao)

        try:
            if acao == "encrypt":
                texto_bytes = texto.encode("utf-8")
                cifrado = criptografar(chave_bytes, NONCE, texto_bytes)
                responder_json(self, {"mensagem": "Texto criptografado.", "resultado": cifrado.hex()})
                return

            if acao == "decrypt":
                texto_bytes = bytes.fromhex(texto.strip())
                decifrado = criptografar(chave_bytes, NONCE, texto_bytes)
                responder_json(self, {"mensagem": "Texto descriptografado.", "resultado": decifrado.decode("utf-8")})
                return

            responder_json(self, {"mensagem": "Ação inválida.", "resultado": ""}, 400)
        except ValueError:
            responder_json(self, {"mensagem": "Texto inválido. Use hexadecimal correto.", "resultado": ""}, 400)
        except UnicodeDecodeError:
            responder_json(self, {"mensagem": "Chave incorreta ou texto corrompido.", "resultado": ""}, 400)

    def log_message(self, format, *args):
        return


def main():
    porta = 8000
    endereco = ("", porta)

    with socketserver.TCPServer(endereco, ChaChaHandler) as servidor:
        print(f"Servidor rodando em http://localhost:{porta}")
        print("Abra http://localhost:8000 no navegador.")
        servidor.serve_forever()


if __name__ == "__main__":
    main()
