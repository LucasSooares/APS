# UNIVERSIDADE VANGUARDA

## CURSO DE ANÁLISE E DESENVOLVIMENTO DE SISTEMAS 

`<br><br>``<br><br>``<br>`

# [NOME DO ALUNO OU INTEGRANTES DO GRUPO]

`<br><br>``<br><br>``<br>`

# DESENVOLVIMENTO DE APLICAÇÃO UTILIZANDO TÉCNICAS CRIPTOGRÁFICAS

## Atividades Práticas Supervisionadas (APS) - 1º Semestre

`<br><br>``<br><br>``<br><br>``<br><br>`

**SÃO JOSÉ DOS CAMPOS**
**2026**

---

\pagebreak

# SUMÁRIO

1. [INTRODUÇÃO](#1-introdução)
2. [FUNDAMENTOS DE CRIPTOGRAFIA](#2-fundamentos-de-criptografia)
3. [DESCRIÇÃO DA TÉCNICA CRIPTOGRÁFICA ESCOLHIDA](#3-descrição-da-técnica-criptográfica-escolhida)
4. [SOLUÇÃO DESENVOLVIDA](#4-solução-desenvolvida)
5. [CÓDIGO-FONTE](#5-código-fonte)
6. [REFERÊNCIAS](#6-referências)

---

\pagebreak

# 1. INTRODUÇÃO

Este relatório apresenta o desenvolvimento de uma aplicação em linguagem Python que implementa um algoritmo próprio de criptografia e descriptografia, cumprindo os requisitos da disciplina de Algoritmos e Programação Estruturada para a Atividade Prática Supervisionada (APS) do 1º Semestre.

O objetivo do projeto é demonstrar a capacidade de manipular dados, construir algoritmos lógicos e interagir com o usuário por meio de um menu de opções, sem depender de bibliotecas criptográficas prontas (como exigido nas orientações da APS).

A criptografia é essencial nos dias atuais para garantir a confidencialidade e a integridade da informação. Este trabalho propõe uma abordagem simplificada, mas eficiente, baseada nos conceitos da cifra ChaCha20, construída de forma manual.

*Observação: A Inteligência Artificial (Gemini) foi utilizada para revisão gramatical, auxílio na estruturação deste relatório e na refatoração do código para atender às exigências de validação e menu interativo.*

---

# 2. FUNDAMENTOS DE CRIPTOGRAFIA

A criptografia é a prática e o estudo de técnicas para comunicação segura na presença de terceiros. Trata-se da conversão de informações legíveis (texto claro) em dados incompreensíveis (texto cifrado), sendo acessíveis apenas a quem possui o conhecimento específico (a chave) para reverter o processo.

Historicamente, as cifras evoluíram desde a Cifra de César na Roma Antiga até os algoritmos modernos e complexos, como o AES e o ChaCha20, que utilizam operações matemáticas avançadas e chaves extensas para garantir que as mensagens não sejam decifradas por ataques de força bruta.

Existem dois tipos principais de criptografia:

* **Simétrica**: Utiliza a mesma chave para criptografar e descriptografar. É rápida e eficiente para grandes volumes de dados.
* **Assimétrica**: Utiliza um par de chaves (pública e privada). A chave pública criptografa e a privada descriptografa.

Neste projeto, foi implementado um modelo de criptografia **simétrica**.

---

# 3. DESCRIÇÃO DA TÉCNICA CRIPTOGRÁFICA ESCOLHIDA

A técnica escolhida baseia-se nos princípios do algoritmo **ChaCha20**, uma cifra de fluxo (stream cipher) simétrica. O ChaCha20 foi escolhido por ser seguro e não depender de hardware especializado para ser rápido.

Como as orientações da APS determinam a construção integral do algoritmo pelo aluno, optou-se por implementar manualmente a lógica interna da cifra. O funcionamento ocorre da seguinte forma:

1. **Estado Inicial**: O algoritmo cria uma matriz (estado) de 16 blocos de 32 bits, utilizando constantes fixas, a chave do usuário e um "nonce" (número usado uma única vez).
2. **Mistura (Quarter-Round)**: O estado passa por uma série de 20 rodadas de mistura matemática que utilizam operações de soma, ou exclusivo (XOR) e rotação de bits (`rotate_left`).
3. **Geração do Keystream**: Após a mistura, o estado resultante é transformado em um fluxo de bytes pseudoaleatório.
4. **Cifragem (XOR)**: A mensagem do usuário (texto claro) é combinada (XOR) byte a byte com o keystream. Para descriptografar, o processo inverso com a mesma chave gera o mesmo keystream, recuperando a mensagem original.

Essa abordagem garante que, mesmo sem o uso de bibliotecas especializadas, o sistema seja muito mais seguro do que cifras de substituição simples, atendendo ao nível de complexidade desejado.

---

# 4. SOLUÇÃO DESENVOLVIDA

A solução final é um script em Python de fácil utilização. Ao ser executado, o programa apresenta o seguinte fluxo:

* Exibe um menu principal contendo as opções de Criptografia, Descriptografia e Sair.
* **Na Criptografia**: O sistema solicita ao usuário que insira uma frase. Há uma validação restrita para que a frase não ultrapasse **256 caracteres**. Em seguida, solicita a senha. A chave é normalizada para 32 bytes e a frase é criptografada. O resultado é exibido em formato hexadecimal para que possa ser facilmente copiado e colado pelo usuário.
* **Na Descriptografia**: O sistema solicita o texto cifrado (em hexadecimal) e a senha. Se a senha for a mesma utilizada na origem, o sistema reverte as operações XOR e imprime a mensagem legível. Tratamento de exceções (try/except) garante que a aplicação não quebre caso o usuário insira uma chave incorreta ou dados corrompidos.

A aplicação funciona em um laço infinito (`while True`), retornando ao menu após cada operação, parando apenas se o usuário escolher a opção 3.

---

# 5. CÓDIGO-FONTE

O código foi desenvolvido de maneira integral, respeitando a não utilização de bibliotecas de terceiros para a criptografia em si. A estrutura do código inclui funções de utilidade matemática, a lógica do bloco criptográfico e a interface textual iterativa.

*(Observação: Você deve colar aqui o conteúdo do arquivo `app.py` que concluímos, ou então anexar o arquivo .py ao entregar)*

---

# 6. REFERÊNCIAS

* MENEZES, Alfred J. et al. *Handbook of Applied Cryptography*. CRC Press, 1996.
* STALLINGS, William. *Criptografia e Segurança de Redes: Princípios e Práticas*. 6. ed. São Paulo: Pearson, 2014.
* DOCUMENTAÇÃO DA LINGUAGEM PYTHON. Disponível em: https://docs.python.org/3/. Acesso em: 05 mai. 2026.
* BERNSTEIN, Daniel J. *ChaCha, a variant of Salsa20*. Documento Técnico, 2008.
