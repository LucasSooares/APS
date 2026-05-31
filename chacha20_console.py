python#!/usr/bin/env python3
"""
Arquivo separado com a lógica do ChaCha20 em Python puro.
Este script não usa frontend ou servidor web.
Ele permite criptografar e descriptografar texto pela linha de comando.
"""

# NONCE: "Number used ONCE" (Número usado uma única vez). 
# É um vetor público de 12 bytes que garante que a mesma mensagem criptografada 
# duas vezes com a mesma chave gere textos cifrados completamente diferentes.
NONCE = b"123456789012"


def rotacionar_esquerda(valor, casas):
    """
    O que faz: Pega os bits de um número e os move para a esquerda. 
    Os bits que "transbordam" pela esquerda entram de volta pela direita.
    Por que existe: É uma operação de mistura que embaralha os bits sem apagar 
    nenhuma informação.
    """
    # '& 0xFFFFFFFF' limita o resultado a 32 bits, simulando o comportamento de um processador de 32 bits.
    return ((valor << casas) & 0xFFFFFFFF) | (valor >> (32 - casas))


def quarter_round(estado, a, b, c, d):
    """
    O que faz: Mistura de forma caótica quatro posições (palavras de 32 bits) da 
    lista de estado.
    Por que existe: É o "liquidificador" matemático do ChaCha20. 
    Aplica adições, XOR (^) e rotações para criar o efeito avalanche 
    (mudar 1 bit muda o resultado todo).
    """
    # Passo 1: Mistura 'a' e 'b', depois altera 'd' com base no resultado e rotaciona 16 bits
    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 16)
    
    # Passo 2: Mistura 'c' e 'd', depois altera 'b' com base no resultado e rotaciona 12 bits
    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 12)
    
    # Passo 3: Repete o processo para aumentar o caos, rotacionando 8 bits
    estado[a] = (estado[a] + estado[b]) & 0xFFFFFFFF
    estado[d] = rotacionar_esquerda(estado[d] ^ estado[a], 8)
    
    # Passo 4: Última mistura do bloco de quatro, rotacionando 7 bits
    estado[c] = (estado[c] + estado[d]) & 0xFFFFFFFF
    estado[b] = rotacionar_esquerda(estado[b] ^ estado[c], 7)


def bloco_chacha20(chave, nonce, contador):
    """
    O que faz: Monta a matriz inicial e gera um bloco único de 64 bytes 
    de puro caos (fluxo).
    Por que o 'estado' virou lista? O algoritmo trabalha com uma matriz 
    4x4 de números de 32 bits. 
    A lista no Python nos permite acessar e alterar cada uma dessas 16 
    posições rapidamente por índices (0 a 15).
    """
    # Posições 0 a 3: Constantes fixas do algoritmo (texto "expand 32-byte k" convertido em números)
    estado = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]

    # Posições 4 a 11: Adiciona os 32 bytes da chave divididos em
    # 8 números de 32 bits.
    # O 'little' garante que o Python leia os bytes na ordem correta 
    # exigida pelo ChaCha20.
    for i in range(0, 32, 4):
        estado.append(int.from_bytes(chave[i:i + 4], "little"))

    # Posição 12: O número do bloco atual (contador de blocos para mensagens grandes)
   
    estado.append(contador)

    # Posições 13 a 15: Adiciona os 12 bytes do Nonce divididos em 3 números 
    # de 32 bits
    for i in range(0, 12, 4):
        estado.append(int.from_bytes(nonce[i:i + 4], "little"))

    # 'trabalho' vira uma lista cópia do estado. Ela vai ser totalmente esmagada 
    # e modificada nas rodadas.
    # Mantemos o 'estado' original intacto porque precisaremos dele no final.
    trabalho = estado.copy()

    # Executa 10 rodadas duplas (totalizando 20 rodadas, daí o nome ChaCha20)
    for _ in range(10):
        # Rodadas de Coluna: Mistura verticalmente a matriz
        quarter_round(trabalho, 0, 4, 8, 12)
        quarter_round(trabalho, 1, 5, 9, 13)
        quarter_round(trabalho, 2, 6, 10, 14)
        quarter_round(trabalho, 3, 7, 11, 15)
        # Rodadas Diagonais: Mistura transversalmente a matriz
        quarter_round(trabalho, 0, 5, 10, 15)
        quarter_round(trabalho, 1, 6, 11, 12)
        quarter_round(trabalho, 2, 7, 8, 13)
        quarter_round(trabalho, 3, 4, 9, 14)

    # 'resultado' vai guardar o fluxo final de bytes gerado
    resultado = bytearray()
    
    # Soma a matriz destruída ('trabalho') com a matriz original ('estado'). 
    # Isso impede que alguém faça o caminho inverso para tentar descobrir a chave.
    for i in range(16):
        numero = (trabalho[i] + estado[i]) & 0xFFFFFFFF
        resultado.extend(numero.to_bytes(4, "little")) # Transforma de volta em bytes na ordem 'little-endian'

    return bytes(resultado)


def criptografar(chave, nonce, texto):
    """
    O que faz: Corta o texto em blocos de 64 bytes e aplica a criptografia 
    usando o operador XOR (^).
    Curiosidade: No ChaCha20, criptografar e descriptografar usam EXATAMENTE a 
    mesma função. 
    Fazer o XOR da mensagem com o fluxo gera o código secreto. Fazer o
    XOR de novo anula e traz a mensagem de volta.
    """
    resultado = bytearray()
    
    # Roda de 64 em 64 bytes do texto informado pelo usuário
    for bloco_inicio in range(0, len(texto), 64):
        # 'fluxo': Gera 64 bytes de números caóticos para este bloco específico
        fluxo = bloco_chacha20(chave, nonce, bloco_inicio // 64)
        
        # Recorta o pedaço atual do texto
        parte_texto = texto[bloco_inicio:bloco_inicio + 64]
        
        # 'byte_texto' é o caractere original e 'fluxo[i]' é o número caótico gerado. 
        # O '^' (XOR) mistura os dois de forma reversível.
        for i, byte_texto in enumerate(parte_texto):
            resultado.append(byte_texto ^ fluxo[i])
            
    return bytes(resultado)


def preparar_chave(chave):
    """
    O que faz: Ajusta o tamanho da chave digitada pelo usuário.
    Por que existe: O ChaCha20 exige estritamente uma chave de 32 bytes 
    (256 bits). 
    Se o usuário digitar menos que isso, 
    essa função replica o texto até alcançar o tamanho correto.
    """
    chave_bytes = chave.encode("utf-8")
    if len(chave_bytes) < 32:
        # Multiplica e repete a chave para preencher os espaços vazios
        chave_bytes = (chave_bytes * ((32 // len(chave_bytes)) + 1))[:32]
    return chave_bytes[:32] # Garante o corte final cravado em 32 bytes


def gerar_chave_aleatoria():
    """
    O que faz: Cria uma chave aleatória caseira baseada em cálculos lendo o 
    próprio arquivo do script.
    Aviso: É apenas uma simulação matemática simples para o script rodar sozinho. 
    Para sistemas reais, o correto seria usar funções seguras do sistema
    """
    codigo = open(__file__, "rb").read()
    valor = 0
    # Gera uma semente numérica misturando os bytes do código deste arquivo
    for byte in codigo:
        valor = ((valor << 5) - valor + byte) & 0xFFFFFFFF
    
    # Mistura o endereço físico de memória do Python atual usando a 
    # função id() para dar aleatoriedade
    valor ^= id(object()) & 0xFFFFFFFF
    caracteres = "0123456789abcdef"
    chave = ""
    
    # Gera 10 caracteres hexadecimais usando um gerador de números pseudo-aleatórios linear congruente
    for _ in range(10):
        valor = (valor * 1664525 + 1013904223) & 0xFFFFFFFF
        chave += caracteres[valor % len(caracteres)]
    return chave


def main():
    """
    O que faz: Controla a interface de terminal (linhas de comando).
    Gerencia as escolhas do usuário, recebe as entradas de texto e exibe 
    os resultados na tela.
    """
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
            
            # Criptografa a mensagem string convertida em bytes (utf-8)
            cifrado = criptografar(chave_bytes, NONCE, texto.encode("utf-8"))
            
            # Exibe o resultado transformado em hexadecimal legível (ex: 4a2b9f...)
            print("\nTexto cifrado (hex):", cifrado.hex())
            print("Chave usada:", chave)

        elif opcao == "2":
            texto_hex = input("Cole o texto cifrado em hexadecimal: ").strip()
            chave = input("Digite a chave usada na criptografia: ").strip()
            try:
                # Transforma a string hexadecimal de volta em bytes brutos para o algoritmo processar
                texto_bytes = bytes.fromhex(texto_hex)
                chave_bytes = preparar_chave(chave)
                
                # Executa a mesma função de criptografar (que agora vai descriptografar)
                decifrado = criptografar(chave_bytes, NONCE, texto_bytes)
                
                # Traduz os bytes finais de volta para um texto legível na tela
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