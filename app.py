# ==============================================================================
# APS: SISTEMA DE CRIPTOGRAFIA
# Algoritmo Base: ChaCha20 (Implementação Manual e Didática)
# Objetivo: Criptografar e Descriptografar mensagens sem o uso de bibliotecas externas prontas.
# ==============================================================================

def rotate_left(v, c):
    """
    Função auxiliar que realiza uma rotação de bits para a esquerda (Circular Shift).
    Essa operação é fundamental em algoritmos de criptografia para "misturar" 
    os bits e garantir que o resultado pareça aleatório (difusão).
    """
    return ((v << c) & 0xffffffff) | (v >> (32 - c))

def quarter_round(x, a, b, c, d):
    """
    Função 'Quarter Round' (Rodada de Quarto):
    É o coração da mistura matemática do ChaCha20. 
    Ela atualiza 4 elementos do array de estado (x) usando três operações básicas:
    Soma (Adição), Ou Exclusivo (XOR - ^) e Rotação de Bits.
    Essa combinação (Adicionar-Rotacionar-XOR) é o que torna o algoritmo seguro.
    """
    # 1ª parte da mistura
    x[a] = (x[a] + x[b]) & 0xffffffff
    x[d] ^= x[a]
    x[d] = rotate_left(x[d], 16)
    
    # 2ª parte da mistura
    x[c] = (x[c] + x[d]) & 0xffffffff
    x[b] ^= x[c]
    x[b] = rotate_left(x[b], 12)
    
    # 3ª parte da mistura
    x[a] = (x[a] + x[b]) & 0xffffffff
    x[d] ^= x[a]
    x[d] = rotate_left(x[d], 8)
    
    # 4ª parte da mistura
    x[c] = (x[c] + x[d]) & 0xffffffff
    x[b] ^= x[c]
    x[b] = rotate_left(x[b], 7)

def chacha20_block(key, nonce, counter):
    """
    Gera um "bloco de keystream" (fluxo de chaves) de 64 bytes.
    Para gerar esse bloco, é montada uma matriz inicial (estado) de 16 números inteiros.
    """
    # Constante mágica do ChaCha20 (representa a string "expand 32-byte k" em ASCII hexadecimal)
    # Isso serve para garantir um ponto de partida fixo e seguro.
    ctx = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
    
    # Adiciona a chave de 32 bytes (dividida em 8 inteiros de 32 bits) no estado
    for i in range(0, 32, 4):
        ctx.append(int.from_bytes(key[i:i+4], 'little'))
        
    # Adiciona o contador numérico (para garantir que blocos diferentes tenham resultados diferentes)
    ctx.append(counter)
    
    # Adiciona o "nonce" (Número usado uma vez só), que garante que a mesma mensagem com a mesma chave
    # gere criptografias diferentes se o nonce for diferente. (No nosso caso, usamos um fixo por simplicidade).
    for i in range(0, 12, 4):
        ctx.append(int.from_bytes(nonce[i:i+4], 'little'))
    
    # Copia o estado inicial para fazer a mistura
    x = list(ctx)
    
    # Executa 20 rodadas (10 iterações duplas) de mistura (Quarter Rounds).
    # As rodadas pares misturam as colunas e as ímpares misturam as diagonais.
    for _ in range(10):
        quarter_round(x, 0, 4, 8, 12); quarter_round(x, 1, 5, 9, 13)
        quarter_round(x, 2, 6, 10, 14); quarter_round(x, 3, 7, 11, 15)
        quarter_round(x, 0, 5, 10, 15); quarter_round(x, 1, 6, 11, 12)
        quarter_round(x, 2, 7, 8, 13); quarter_round(x, 3, 4, 9, 14)
        
    # Soma o estado final misturado (x) com o estado inicial (ctx).
    # Isso protege o algoritmo contra ataques de reversão matemática.
    res = bytearray()
    for i in range(16):
        val = (x[i] + ctx[i]) & 0xffffffff
        res.extend(val.to_bytes(4, 'little'))
        
    return res

def crypt(key, nonce, plaintext):
    """
    Função principal de cifragem/decifragem.
    Como é uma cifra de fluxo, o processo para Criptografar e Descriptografar é exatamente o mesmo!
    Basta fazer um XOR (^) da mensagem original com o fluxo de chaves gerado.
    """
    result = bytearray()
    
    # Quebra a mensagem (plaintext) em blocos de 64 bytes para ir aplicando a cifra.
    for i in range(0, len(plaintext), 64):
        # Gera o fluxo pseudoaleatório (keystream) matemático
        keystream = chacha20_block(key, nonce, i // 64)
        
        # Mistura o texto claro com o keystream usando XOR (^)
        # Propriedade do XOR: (Texto Claro ^ Keystream) = Texto Cifrado
        #                     (Texto Cifrado ^ Keystream) = Texto Claro
        for b, k in zip(plaintext[i:i+64], keystream):
            result.append(b ^ k)
            
    return bytes(result)

# ==============================================================================
# INTERAÇÃO COM O USUÁRIO (WEB API)
# ==============================================================================

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# O "Nonce" é um número auxiliar usado na criptografia (12 bytes). 
# Em aplicações reais, ele deve ser único por mensagem, mas aqui mantemos fixo.
nonce_fixo = b"123456789012" 

@app.route('/')
def index():
    """Renderiza a página principal (HTML)"""
    return render_template('index.html')

@app.route('/api/crypt', methods=['POST'])
def api_crypt():
    """Endpoint da API para criptografar e descriptografar"""
    data = request.json
    action = data.get('action') # 'encrypt' ou 'decrypt'
    text = data.get('text')
    key = data.get('key')
    
    if not text or not key:
        return jsonify({'error': 'Texto e chave são obrigatórios.'}), 400
        
    # Normaliza a chave para que ela sempre tenha exatamente 32 bytes de tamanho.
    chave_bytes = key.encode('utf-8').ljust(32, b' ')[:32]
    
    try:
        if action == 'encrypt':
            # Validação de 256 caracteres
            if len(text) > 256:
                return jsonify({'error': 'A frase deve ter no máximo 256 caracteres.'}), 400
                
            texto_bytes = text.encode('utf-8')
            resultado_cifrado = crypt(chave_bytes, nonce_fixo, texto_bytes)
            return jsonify({'result': resultado_cifrado.hex()})
            
        elif action == 'decrypt':
            try:
                texto_cifrado_bytes = bytes.fromhex(text.strip())
                decifrado_bytes = crypt(chave_bytes, nonce_fixo, texto_cifrado_bytes)
                return jsonify({'result': decifrado_bytes.decode('utf-8')})
            except ValueError:
                return jsonify({'error': 'O texto inserido não é um hexadecimal válido.'}), 400
            except UnicodeDecodeError:
                return jsonify({'error': 'Chave incorreta ou dados corrompidos. Não foi possível descriptografar.'}), 400
        else:
            return jsonify({'error': 'Ação inválida.'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)