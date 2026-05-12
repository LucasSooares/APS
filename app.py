import http.server
import html
import socketserver
import urllib.parse

# Este projeto implementa ChaCha20 em Python puro, sem bibliotecas externas.
# A interface é feita com HTML e CSS puros, usando apenas formulários.

# NONCE fixo apenas para este exemplo. Em um uso real, o nonce deve ser diferente para cada mensagem.
NONCE = b"123456789012"


def rotacionar_esquerda(valor, casas):
    return ((valor << casas) & 0xFFFFFFFF) | (valor >> (32 - casas))


def quarter_round(estado, a, b, c, d):
    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 16)

    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 12)

    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 8)

    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 7)


def bloco_chacha20(chave, nonce, contador):
    estado = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]

    for i in range(0, 32, 4):
        estado.append(int.from_bytes(chave[i:i + 4], "little"))

    estado.append(contador)

    for i in range(0, 12, 4):
        estado.append(int.from_bytes(nonce[i:i + 4], "little"))

    trabalho = estado.copy()

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
    for i in range(16):
        numero = (trabalho[i] + estado[i]) & 0xFFFFFFFF
        resultado.extend(numero.to_bytes(4, "little"))

    return bytes(resultado)


def criptografar(chave, nonce, texto):
    resultado = bytearray()

    for bloco_inicio in range(0, len(texto), 64):
        fluxo = bloco_chacha20(chave, nonce, bloco_inicio // 64)
        parte_texto = texto[bloco_inicio:bloco_inicio + 64]

        for i, byte_texto in enumerate(parte_texto):
            resultado.append(byte_texto ^ fluxo[i])

    return bytes(resultado)


def preparar_chave(chave):
    return chave.encode("utf-8").ljust(32, b" ")[:32]


def render_page(texto='', chave='', resultado='', mensagem='', tipo_mensagem=''):
    texto_html = html.escape(texto)
    chave_html = html.escape(chave)
    resultado_html = html.escape(resultado)
    mensagem_html = html.escape(mensagem)
    tipo_html = html.escape(tipo_mensagem)

    return f"""<!DOCTYPE html>
<html lang=\"pt-BR\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>ChaCha20 Puro</title>
    <link rel=\"stylesheet\" href=\"/style.css\">
</head>
<body>
    <main class=\"container\">
        <h1>ChaCha20 Puro</h1>
        <p>Use a mesma chave para criptografar ou descriptografar. Não há bibliotecas externas.</p>

        <form action=\"/crypt\" method=\"post\">
            <label for=\"texto\">Texto</label>
            <textarea id=\"texto\" name=\"text\" placeholder=\"Digite a mensagem ou o hexadecimal\">{texto_html}</textarea>

            <label for=\"chave\">Chave</label>
            <input id=\"chave\" name=\"key\" type=\"text\" value=\"{chave_html}\" placeholder=\"Digite a chave\" />

            <div class=\"modo\">
                <button type=\"submit\" name=\"action\" value=\"encrypt\">Criptografar</button>
                <button type=\"submit\" name=\"action\" value=\"decrypt\">Descriptografar</button>
            </div>
        </form>

        <p class=\"mensagem {tipo_html}\">{mensagem_html}</p>

        <label for=\"resultado\">Resultado</label>
        <textarea id=\"resultado\" readonly>{resultado_html}</textarea>
    </main>
</body>
</html>"""


def respond_html(handler, texto='', chave='', resultado='', mensagem='', tipo_mensagem=''):
    pagina = render_page(texto, chave, resultado, mensagem, tipo_mensagem)
    resposta = pagina.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(resposta)))
    handler.end_headers()
    handler.wfile.write(resposta)


class ChaChaHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            respond_html(self)
            return

        return super().do_GET()

    def do_POST(self):
        if self.path != "/crypt":
            self.send_error(404, "Not found")
            return

        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(tamanho).decode("utf-8")
        dados = urllib.parse.parse_qs(corpo)

        acao = dados.get("action", [""])[0]
        texto = dados.get("text", [""])[0]
        chave = dados.get("key", [""])[0]

        if not texto or not chave:
            respond_html(self, texto, chave, "", "Texto e chave são obrigatórios.", "erro")
            return

        chave_bytes = preparar_chave(chave)

        try:
            if acao == "encrypt":
                texto_bytes = texto.encode("utf-8")
                cifrado = criptografar(chave_bytes, NONCE, texto_bytes)
                respond_html(self, texto, chave, cifrado.hex(), "Texto criptografado.", "sucesso")
                return

            if acao == "decrypt":
                texto_bytes = bytes.fromhex(texto.strip())
                decifrado = criptografar(chave_bytes, NONCE, texto_bytes)
                respond_html(self, texto, chave, decifrado.decode("utf-8"), "Texto descriptografado.", "sucesso")
                return

            respond_html(self, texto, chave, "", "Ação inválida.", "erro")
        except ValueError:
            respond_html(self, texto, chave, "", "Texto inválido. Use hexadecimal correto.", "erro")
        except UnicodeDecodeError:
            respond_html(self, texto, chave, "", "Chave incorreta ou texto corrompido.", "erro")

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
