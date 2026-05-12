from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

# Nonce fixo usado junto com a chave para gerar o fluxo de bytes do ChaCha20.
NONCE = b"123456789012"


def rotacionar_esquerda(valor, casas):
    # Mantem o numero em 32 bits e move os bits para a esquerda.
    return ((valor << casas) & 0xFFFFFFFF) | (valor >> (32 - casas))


def quarter_round(estado, a, b, c, d):
    # Mistura quatro posicoes do estado, seguindo a operacao basica do ChaCha20.
    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 16)

    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 12)

    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 8)

    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 7)


def bloco_chacha20(chave, nonce, contador):
    # Monta o estado inicial com constantes, chave, contador e nonce.
    estado = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]

    for i in range(0, 32, 4):
        estado.append(int.from_bytes(chave[i:i + 4], "little"))

    estado.append(contador)

    for i in range(0, 12, 4):
        estado.append(int.from_bytes(nonce[i:i + 4], "little"))

    trabalho = estado.copy()

    # O ChaCha20 usa 20 rodadas: 10 repeticoes com duas misturas cada.
    for _ in range(10):
        quarter_round(trabalho, 0, 4, 8, 12)
        quarter_round(trabalho, 1, 5, 9, 13)
        quarter_round(trabalho, 2, 6, 10, 14)
        quarter_round(trabalho, 3, 7, 11, 15)
        quarter_round(trabalho, 0, 5, 10, 15)
        quarter_round(trabalho, 1, 6, 11, 12)
        quarter_round(trabalho, 2, 7, 8, 13)
        quarter_round(trabalho, 3, 4, 9, 14)

    resultado = bytearray()

    # Soma o estado embaralhado ao estado original e transforma em 64 bytes.
    for i in range(16):
        numero = (trabalho[i] + estado[i]) & 0xFFFFFFFF
        resultado.extend(numero.to_bytes(4, "little"))

    return resultado


def criptografar(chave, nonce, texto):
    # Gera blocos de fluxo e aplica XOR em cada byte do texto.
    # A mesma funcao serve para criptografar e descriptografar.
    resultado = bytearray()

    for i in range(0, len(texto), 64):
        fluxo = bloco_chacha20(chave, nonce, i // 64)

        for byte_texto, byte_fluxo in zip(texto[i:i + 64], fluxo):
            resultado.append(byte_texto ^ byte_fluxo)

    return bytes(resultado)


def preparar_chave(chave):
    # Ajusta a chave para exatamente 32 bytes, tamanho esperado pelo ChaCha20.
    return chave.encode("utf-8").ljust(32, b" ")[:32]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/crypt", methods=["POST"])
def api_crypt():
    # Le os dados enviados pelo JavaScript no formato JSON.
    dados = request.get_json() or {}
    acao = dados.get("action")
    texto = dados.get("text", "")
    chave = dados.get("key", "")

    if not texto or not chave:
        return jsonify({"error": "Texto e chave são obrigatórios."}), 400

    chave_bytes = preparar_chave(chave)

    if acao == "encrypt":
        # Converte o texto para bytes, criptografa e devolve em hexadecimal.
        texto_bytes = texto.encode("utf-8")
        cifrado = criptografar(chave_bytes, NONCE, texto_bytes)
        return jsonify({"result": cifrado.hex()})

    if acao == "decrypt":
        try:
            # Converte o hexadecimal de volta para bytes e aplica a mesma cifra.
            texto_bytes = bytes.fromhex(texto.strip())
            decifrado = criptografar(chave_bytes, NONCE, texto_bytes)
            return jsonify({"result": decifrado.decode("utf-8")})
        except ValueError:
            return jsonify({"error": "O texto informado não é um hexadecimal válido."}), 400
        except UnicodeDecodeError:
            return jsonify({"error": "Chave incorreta ou texto corrompido."}), 400

    return jsonify({"error": "Ação inválida."}), 400


if __name__ == "__main__":
    app.run(debug=True)
