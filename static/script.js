document.addEventListener("DOMContentLoaded", () => {
    // Guarda referencias dos elementos da tela para reutilizar nas funcoes.
    const btnEncrypt = document.getElementById("btn-encrypt");
    const btnDecrypt = document.getElementById("btn-decrypt");
    const inputText = document.getElementById("input-text");
    const outputText = document.getElementById("output-text");
    const inputLabel = document.getElementById("input-label");
    const charCounter = document.getElementById("char-counter");
    const keyArea = document.getElementById("key-area");
    const keyInput = document.getElementById("key-input");
    const actionBtn = document.getElementById("action-btn");
    const messageArea = document.getElementById("message-area");
    const copyBtn = document.getElementById("copy-btn");
    const resultKeyArea = document.getElementById("result-key-area");
    const resultKeyInput = document.getElementById("result-key-input");
    const copyResultKeyBtn = document.getElementById("copy-result-key-btn");
    const logList = document.getElementById("log-list");
    const clearLogBtn = document.getElementById("clear-log-btn");

    let modo = "encrypt";
    let historico = JSON.parse(localStorage.getItem("historicoCripto")) || [];

    function gerarChave() {
        // Cria uma chave aleatoria com 32 caracteres para a criptografia.
        const caracteres = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        let chave = "";

        for (let i = 0; i < 32; i++) {
            const posicao = Math.floor(Math.random() * caracteres.length);
            chave += caracteres[posicao];
        }

        return chave;
    }

    function mostrarMensagem(texto, tipo) {
        // Exibe mensagens de sucesso ou erro abaixo do botao principal.
        messageArea.textContent = texto;
        messageArea.className = tipo;
    }

    function limparMensagem() {
        mostrarMensagem("", "");
    }

    function atualizarContador() {
        // Mostra apenas quantos caracteres foram digitados, sem limite maximo.
        const total = inputText.value.length;
        charCounter.textContent = `${total} ${total === 1 ? "caractere" : "caracteres"}`;
    }

    function limparCampos() {
        // Limpa entradas, resultado, chave gerada e mensagens ao trocar de modo.
        inputText.value = "";
        outputText.value = "";
        keyInput.value = "";
        resultKeyInput.value = "";
        resultKeyArea.classList.add("escondido");
        limparMensagem();
        atualizarContador();
    }

    function mudarModo(novoModo) {
        // Alterna a interface entre criptografar e descriptografar.
        modo = novoModo;
        limparCampos();

        const criptografando = modo === "encrypt";

        btnEncrypt.classList.toggle("ativo", criptografando);
        btnDecrypt.classList.toggle("ativo", !criptografando);
        keyArea.classList.toggle("escondido", criptografando);
        charCounter.classList.toggle("escondido", !criptografando);

        inputLabel.textContent = criptografando ? "Mensagem" : "Texto hexadecimal";
        inputText.placeholder = criptografando ? "Digite sua mensagem" : "Cole o texto criptografado";
        actionBtn.textContent = criptografando ? "Criptografar" : "Descriptografar";
    }

    async function copiarTexto(texto) {
        // Copia o conteudo informado para a area de transferencia do navegador.
        if (!texto) {
            return;
        }

        await navigator.clipboard.writeText(texto);
        mostrarMensagem("Texto copiado.", "sucesso");
    }

    function salvarHistorico(entrada, saida, chave) {
        // Salva as ultimas operacoes no localStorage do navegador.
        historico.unshift({
            modo,
            entrada,
            saida,
            chave,
            hora: new Date().toLocaleTimeString()
        });

        historico = historico.slice(0, 20);
        localStorage.setItem("historicoCripto", JSON.stringify(historico));
        mostrarHistorico();
    }

    function mostrarHistorico() {
        // Renderiza o historico salvo, escapando textos digitados pelo usuario.
        if (historico.length === 0) {
            logList.innerHTML = "<p>Nenhuma operação feita ainda.</p>";
            return;
        }

        logList.innerHTML = "";

        historico.forEach((item) => {
            const div = document.createElement("div");
            const titulo = item.modo === "encrypt" ? "Criptografado" : "Descriptografado";

            div.className = "item-historico";
            div.innerHTML = `
                <strong>${titulo}</strong>
                <span>${item.hora}</span>
                <p>Entrada: ${escaparHtml(item.entrada)}</p>
                <p>Resultado: ${escaparHtml(item.saida)}</p>
                <p>Chave: ${escaparHtml(item.chave)}</p>
            `;

            logList.appendChild(div);
        });
    }

    function escaparHtml(texto) {
        // Evita que textos do usuario sejam interpretados como HTML.
        return texto
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    btnEncrypt.addEventListener("click", () => mudarModo("encrypt"));
    btnDecrypt.addEventListener("click", () => mudarModo("decrypt"));
    inputText.addEventListener("input", atualizarContador);
    copyBtn.addEventListener("click", () => copiarTexto(outputText.value));
    copyResultKeyBtn.addEventListener("click", () => copiarTexto(resultKeyInput.value));

    clearLogBtn.addEventListener("click", () => {
        historico = [];
        localStorage.removeItem("historicoCripto");
        mostrarHistorico();
    });

    actionBtn.addEventListener("click", async () => {
        // Envia a acao escolhida para o Flask e mostra o resultado retornado.
        const texto = inputText.value;
        const chave = modo === "encrypt" ? gerarChave() : keyInput.value;

        if (!texto) {
            mostrarMensagem("Digite um texto.", "erro");
            return;
        }

        if (!chave) {
            mostrarMensagem("Digite a chave.", "erro");
            return;
        }

        actionBtn.disabled = true;
        limparMensagem();

        try {
            const resposta = await fetch("/api/crypt", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: modo, text: texto, key: chave })
            });

            const dados = await resposta.json();

            if (!resposta.ok) {
                mostrarMensagem(dados.error || "Não foi possível concluir.", "erro");
                return;
            }

            outputText.value = dados.result;
            mostrarMensagem("Operação concluída.", "sucesso");
            salvarHistorico(texto, dados.result, chave);

            if (modo === "encrypt") {
                resultKeyInput.value = chave;
                resultKeyArea.classList.remove("escondido");
            }
        } catch {
            mostrarMensagem("Erro ao conectar com o servidor.", "erro");
        } finally {
            actionBtn.disabled = false;
        }
    });

    mudarModo("encrypt");
    mostrarHistorico();
});
