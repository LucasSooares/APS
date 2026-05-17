#!/usr/bin/env python3
"""
Arquivo separado com a lógica do ChaCha20 em Python puro.
Este script não usa frontend ou servidor web.
Ele permite criptografar e descriptografar texto pela linha de comando.
"""

NONCE = b"123456789012"


def rotacionar_esquerda(valor, casas):
    """Rotaciona os bits do valor para a esquerda dentro de 32 bits."""
    return ((valor << casas) & 0xFFFFFFFF) | (valor >> (32 - casas))


def quarter_round(estado, a, b, c, d):
    """Aplica um quarter round do ChaCha20 em quatro palavras do estado."""
    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 16)
    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 12)
    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 8)
    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 7)


def bloco_chacha20(chave, nonce, contador):
    """Gera um bloco de 64 bytes do fluxo ChaCha20."""
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
    """Criptografa ou descriptografa o texto usando o fluxo ChaCha20."""
    resultado = bytearray()
    for bloco_inicio in range(0, len(texto), 64):
        fluxo = bloco_chacha20(chave, nonce, bloco_inicio // 64)
        parte_texto = texto[bloco_inicio:bloco_inicio + 64]
        for i, byte_texto in enumerate(parte_texto):
            resultado.append(byte_texto ^ fluxo[i])
    return bytes(resultado)


def preparar_chave(chave):
    """Converte a chave para 32 bytes, repetindo-a se necessário."""
    chave_bytes = chave.encode("utf-8")
    if len(chave_bytes) < 32:
        chave_bytes = (chave_bytes * ((32 // len(chave_bytes)) + 1))[:32]
    return chave_bytes[:32]


def gerar_chave_aleatoria():
    """Gera uma chave simples de 10 caracteres para demonstrar a criptografia."""
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


def main():
    print("ChaCha20 console - somente lógica do algoritmo")
    while True:
        print("\nEscolha uma opção:")
        print("1 - Criptografar mensagem")
        print("2 - Descriptografar mensagem")
        print("3 - Sair")
        opcao = input("Digite 1, 2 ou 3: ").strip()

        if opcao == "1":
            texto = input("Digite a mensagem a ser criptografada: ")
            chave = gerar_chave_aleatoria()
            chave_bytes = preparar_chave(chave)
            cifrado = criptografar(chave_bytes, NONCE, texto.encode("utf-8"))
            print("\nTexto cifrado (hex):", cifrado.hex())
            print("Chave usada:", chave)

        elif opcao == "2":
            texto_hex = input("Cole o texto cifrado em hexadecimal: ").strip()
            chave = input("Digite a chave usada na criptografia: ").strip()
            try:
                texto_bytes = bytes.fromhex(texto_hex)
                chave_bytes = preparar_chave(chave)
                decifrado = criptografar(chave_bytes, NONCE, texto_bytes)
                print("\nTexto decifrado:", decifrado.decode("utf-8"))
            except ValueError:
                print("Texto inválido. Use hexadecimal correto.")
            except UnicodeDecodeError:
                print("Chave incorreta ou texto corrompido.")

        elif opcao == "3":
            print("Saindo...")
            break
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
