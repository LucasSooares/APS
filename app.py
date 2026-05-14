import http.server  # servidor HTTP básico do Python
import html         # permite escapar o texto para evitar problemas no HTML
import socketserver # roda um servidor TCP simples para atender o navegador
import urllib.parse # lê os dados enviados pelo formulário HTML
import secrets      # gera números aleatórios seguros para a chave

# Este projeto implementa ChaCha20 em Python puro, sem bibliotecas externas.
# A interface é feita com HTML e CSS puros, usando apenas formulários.

# NONCE fixo apenas para este exemplo. Em um uso real, o nonce deve ser diferente para cada mensagem.
NONCE = b"123456789012"

# Armazena a chave gerada aleatoriamente na sessão
chave_sessao = None


def rotacionar_esquerda(valor, casas):
    # Rotaciona os bits do valor para a esquerda dentro de 32 bits.
    # Esse é um passo comum em algoritmos de cifra para misturar os bits.
    return ((valor << casas) & 0xFFFFFFFF) | (valor >> (32 - casas))


def quarter_round(estado, a, b, c, d):
    # Executa um quarter-round do ChaCha20 usando os índices fornecidos.
    # Cada quarter-round mistura as variáveis com soma modular, XOR e rotação.
    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 16)

    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 12)

    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 8)

    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 7)


def bloco_chacha20(chave, nonce, contador):
    # Inicializa o estado com as constantes do ChaCha20.
    estado = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]

    # Adiciona a chave de 32 bytes em palavras little-endian.
    for i in range(0, 32, 4):
        estado.append(int.from_bytes(chave[i:i + 4], "little"))

    # Adiciona o contador do bloco.
    estado.append(contador)

    # Adiciona o nonce de 12 bytes em três palavras little-endian.
    for i in range(0, 12, 4):
        estado.append(int.from_bytes(nonce[i:i + 4], "little"))

    # Copia o estado inicial para o trabalho, que será transformado.
    trabalho = estado.copy()

    # Aplica 10 rodadas de ChaCha20 (cada rodada tem 8 quarter rounds).
    for _ in range(10):
        quarter_round(trabalho, 0, 4, 8, 12)
        quarter_round(trabalho, 1, 5, 9, 13)
        quarter_round(trabalho, 2, 6, 10, 14)
        quarter_round(trabalho, 3, 7, 11, 15)
        quarter_round(trabalho, 0, 5, 10, 15)
        quarter_round(trabalho, 1, 6, 11, 12)
        quarter_round(trabalho, 2, 7, 8, 13)
        quarter_round(trabalho, 3, 4, 9, 14)

    # Soma o estado original com o estado transformado para gerar o bloco final.
    resultado = bytearray()
    for i in range(16):
        numero = (trabalho[i] + estado[i]) & 0xFFFFFFFF
        resultado.extend(numero.to_bytes(4, "little"))

    return bytes(resultado)


def criptografar(chave, nonce, texto):
    # Aplica o fluxo ChaCha20 sobre o texto usando XOR.
    resultado = bytearray()

    # Processa o texto em blocos de 64 bytes.
    for bloco_inicio in range(0, len(texto), 64):
        fluxo = bloco_chacha20(chave, nonce, bloco_inicio // 64)
        parte_texto = texto[bloco_inicio:bloco_inicio + 64]

        for i, byte_texto in enumerate(parte_texto):
            resultado.append(byte_texto ^ fluxo[i])

    return bytes(resultado)


def preparar_chave(chave):
    # Converte a chave para bytes UTF-8 e garante exatamente 32 bytes.
    # Se for menor, preenche com espaços. Se for maior, corta.
    return chave.encode("utf-8").ljust(32, b" ")[:32]


def gerar_chave_aleatoria():
    # Gera uma chave aleatória segura de 32 bytes e a converte para uma string de 32 caracteres
    chave_bytes = secrets.token_bytes(32)
    # Converte para uma string legível em hexadecimal
    return chave_bytes.hex()


def converter_chave_hex(chave_hex):
    # Converte uma chave em formato hexadecimal de volta para bytes de 32 bytes
    return bytes.fromhex(chave_hex)


def render_result_page(texto='', chave='', resultado='', mensagem='', tipo_mensagem='', texto_criptografado=''):
    # Prepara o texto para ser mostrado com segurança no HTML.
    texto_html = html.escape(texto)
    chave_html = html.escape(chave)
    resultado_html = html.escape(resultado)
    mensagem_html = html.escape(mensagem)
    tipo_html = html.escape(tipo_mensagem)
    texto_cript_html = html.escape(texto_criptografado)

    # Gera uma página HTML completa que contém o mesmo formulário e mostra o resultado.
    # Assim, o resultado aparece na mesma tela após o envio do formulário.
    return f"""<!DOCTYPE html>
<html lang=\"pt-BR\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>ChaCha20</title>
    <link rel=\"stylesheet\" href=\"/style.css\">
</head>
<body>
    <main class=\"container\">
        <h1>ChaCha20</h1>
        <p>Digite sua mensagem para criptografar ou cole o resultado hexadecimal para descriptografar.</p>

        <form action=\"/crypt\" method=\"post\">
            <label for=\"texto\">Texto</label>
            <textarea id=\"texto\" name=\"text\" placeholder=\"Digite a mensagem ou o hexadecimal\">{texto_html}</textarea>

            <label for=\"chave\">Chave (Aleatória)</label>
            <div class=\"chave-container\">
                <input id=\"chave\" name=\"key\" type=\"text\" placeholder=\"Chave gerada automaticamente\" value=\"{chave_html}\" readonly />
                <button type=\"submit\" name=\"action\" value=\"generate_key\" class=\"btn-gerar\">Gerar Nova Chave</button>
            </div>

            <div class=\"modo\">
                <button type="submit" name="action" value="encrypt">Criptografar</button>
                <button type="submit" name="action" value="decrypt">Descriptografar</button>
            </div>
        </form>

        <p class=\"mensagem {tipo_html}\">{mensagem_html}</p>

        <label for=\"resultado\">Resultado</label>
        <textarea id=\"resultado\" readonly placeholder=\"O resultado aparecerá aqui\">{resultado_html}</textarea>
        
        <input type=\"hidden\" id=\"texto_criptografado\" value=\"{texto_cript_html}\" />
    </main>
</body>
</html>"""


def respond_html(handler, texto='', chave='', resultado='', mensagem='', tipo_mensagem='', texto_criptografado=''):
    # Envia a página HTML de resposta para o navegador.
    pagina = render_result_page(texto, chave, resultado, mensagem, tipo_mensagem, texto_criptografado)
    resposta = pagina.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(resposta)))
    handler.end_headers()
    handler.wfile.write(resposta)


class ChaChaHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global chave_sessao
        
        if self.path == "/":
            # Na primeira carga, gera uma chave se ainda não houver uma
            if not chave_sessao:
                chave_sessao = gerar_chave_aleatoria()
            
            # Retorna a página inicial com a chave já gerada
            resposta_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChaCha20</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <main class="container">
        <h1>ChaCha20</h1>

        <form action="/crypt" method="post">
            <label for="texto">Texto</label>
            <textarea id="texto" name="text" placeholder="Digite sua mensagem para criptografar ou cole o hexadecimal para descriptografar"></textarea>

            <label for="chave">Chave (Aleatória)</label>
            <div class="chave-container">
                <input id="chave" name="key" type="text" placeholder="Chave gerada automaticamente" value="{html.escape(chave_sessao)}" readonly />
                <button type="submit" name="action" value="generate_key" class="btn-gerar">Gerar Nova Chave</button>
            </div>

            <div class="modo">
                <button type="submit" name="action" value="encrypt">Criptografar</button>
                <button type="submit" name="action" value="decrypt">Descriptografar</button>
            </div>
        </form>

        <p class="mensagem"></p>

        <label for="resultado">Resultado</label>
        <textarea id="resultado" readonly placeholder="O resultado aparecerá aqui"></textarea>
    </main>
</body>
</html>"""
            resposta = resposta_html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(resposta)))
            self.end_headers()
            self.wfile.write(resposta)
            return
            
        if self.path == "/index.html":
            self.path = "/"
            return self.do_GET()
            
        return super().do_GET()

    def do_POST(self):
        global chave_sessao
        
        if self.path != "/crypt":
            self.send_error(404, "Not found")
            return

        # Recebe os dados enviados pelo formulário HTML.
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(tamanho).decode("utf-8")
        dados = urllib.parse.parse_qs(corpo)

        # action vem do botão pressionado no formulário.
        # text e key vêm dos campos de texto do formulário.
        acao = dados.get("action", [""])[0]
        texto = dados.get("text", [""])[0]
        chave = dados.get("key", [""])[0]

        # Se não houver chave gerada, gera uma
        if not chave_sessao:
            chave_sessao = gerar_chave_aleatoria()

        # Usa a chave da sessão se a chave do formulário estiver vazia
        if not chave:
            chave = chave_sessao
        else:
            chave_sessao = chave

        # Ação para gerar uma nova chave aleatória
        if acao == "generate_key":
            chave_sessao = gerar_chave_aleatoria()
            respond_html(self, texto, chave_sessao, "", "Nova chave gerada com sucesso!", "sucesso")
            return

        if not texto:
            # Se faltar texto, mostra uma mensagem de erro.
            respond_html(self, texto, chave_sessao, "", "Por favor, digite um texto.", "erro")
            return

        # Converte a chave hexadecimal para bytes
        try:
            chave_bytes = converter_chave_hex(chave)
        except ValueError:
            respond_html(self, texto, chave, "", "Formato de chave inválido. Use hexadecimal.", "erro")
            return

        try:
            if acao == "encrypt":
                # Criptografa texto normal e mostra o resultado em hexadecimal.
                texto_bytes = texto.encode("utf-8")
                cifrado = criptografar(chave_bytes, NONCE, texto_bytes)
                respond_html(self, texto, chave, cifrado.hex(), "Texto criptografado.", "sucesso", cifrado.hex())
                return

            if acao == "decrypt":
                # Descriptografa o texto hexadecimal e mostra o texto original.
                texto_bytes = bytes.fromhex(texto.strip())
                decifrado = criptografar(chave_bytes, NONCE, texto_bytes)
                respond_html(self, texto, chave, decifrado.decode("utf-8"), "Texto descriptografado.", "sucesso")
                return

            # Caso o valor de action não seja reconhecido.
            respond_html(self, texto, chave, "", "Ação inválida.", "erro")
        except ValueError:
            # Erro ao converter o texto hexadecimal.
            respond_html(self, texto, chave, "", "Texto inválido. Use hexadecimal correto.", "erro")
        except UnicodeDecodeError:
            # Erro ao decodificar o texto descriptografado como UTF-8.
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
