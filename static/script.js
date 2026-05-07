document.addEventListener('DOMContentLoaded', () => {
    // Referencias dos elementos
    const btnEncrypt = document.getElementById('btn-encrypt');
    const btnDecrypt = document.getElementById('btn-decrypt');
    const keyInput = document.getElementById('key-input');
    const toggleKey = document.getElementById('toggle-key');
    const toggleIcon = document.getElementById('toggle-icon');
    const actionBtn = document.getElementById('action-btn');
    const inputText = document.getElementById('input-text');
    const outputText = document.getElementById('output-text');
    const inputLabel = document.getElementById('input-label');
    const charCounter = document.getElementById('char-counter');
    const copyBtn = document.getElementById('copy-btn');
    const messageArea = document.getElementById('message-area');

    let currentMode = 'encrypt'; // 'encrypt' ou 'decrypt'

    // Alternar modo para Criptografar
    btnEncrypt.addEventListener('click', () => {
        if (currentMode !== 'encrypt') {
            inputText.value = '';
            outputText.value = '';
        }
        currentMode = 'encrypt';
        btnEncrypt.classList.add('active');
        btnDecrypt.classList.remove('active');
        inputLabel.textContent = '2. Insira a Frase Original';
        inputText.placeholder = 'Digite a frase para criptografar (máx 256 caracteres)...';
        actionBtn.innerHTML = "Criptografar Texto <i class='bx bx-lock'></i>";
        inputText.setAttribute('maxlength', '256');
        charCounter.style.display = 'block';
        updateCharCounter();
        clearMessages();
    });

    // Alternar modo para Descriptografar
    btnDecrypt.addEventListener('click', () => {
        if (currentMode !== 'decrypt') {
            inputText.value = '';
            outputText.value = '';
        }
        currentMode = 'decrypt';
        btnDecrypt.classList.add('active');
        btnEncrypt.classList.remove('active');
        inputLabel.textContent = '2. Insira o Texto Hexadecimal';
        inputText.placeholder = 'Cole o texto hexadecimal para descriptografar...';
        actionBtn.innerHTML = "Descriptografar Texto <i class='bx bx-lock-open'></i>";
        inputText.removeAttribute('maxlength');
        charCounter.style.display = 'none';
        clearMessages();
    });

    // Visibilidade da Senha
    toggleKey.addEventListener('click', () => {
        if (keyInput.type === 'password') {
            keyInput.type = 'text';
            toggleIcon.classList.replace('bx-hide', 'bx-show');
        } else {
            keyInput.type = 'password';
            toggleIcon.classList.replace('bx-show', 'bx-hide');
        }
    });

    // Contador de Caracteres
    inputText.addEventListener('input', () => {
        if (currentMode === 'encrypt') {
            updateCharCounter();
        }
    });

    function updateCharCounter() {
        const length = inputText.value.length;
        charCounter.textContent = `${length} / 256`;
    }

    // Limpar mensagens
    function clearMessages() {
        messageArea.textContent = '';
        messageArea.className = 'message-area';
    }

    // Mostrar mensagens
    function showMessage(msg, type) {
        messageArea.textContent = msg;
        messageArea.className = `message-area ${type}`;
    }

    // Copiar para area de transferencia
    copyBtn.addEventListener('click', () => {
        if (!outputText.value) return;
        
        outputText.select();
        document.execCommand('copy');
        
        const originalHtml = copyBtn.innerHTML;
        copyBtn.innerHTML = "<i class='bx bx-check'></i> Copiado!";
        setTimeout(() => {
            copyBtn.innerHTML = originalHtml;
        }, 2000);
    });

    // Acao de Criptografar/Descriptografar
    actionBtn.addEventListener('click', async () => {
        const text = inputText.value;
        const key = keyInput.value;

        if (!text) {
            showMessage('Por favor, insira um texto.', 'error');
            return;
        }
        if (!key) {
            showMessage('Por favor, insira sua chave secreta.', 'error');
            return;
        }

        clearMessages();
        actionBtn.disabled = true;
        const originalBtnHtml = actionBtn.innerHTML;
        actionBtn.innerHTML = "<i class='bx bx-loader-alt bx-spin'></i> Processando...";

        try {
            const response = await fetch('/api/crypt', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: currentMode,
                    text: text,
                    key: key
                })
            });

            const data = await response.json();

            if (!response.ok) {
                showMessage(data.error || 'Ocorreu um erro.', 'error');
            } else {
                outputText.value = data.result;
                showMessage('Operação realizada com sucesso!', 'success');
                addLogEntry(currentMode, text, data.result, key);
            }
        } catch (error) {
            showMessage('Erro de conexão com o servidor.', 'error');
        } finally {
            actionBtn.disabled = false;
            actionBtn.innerHTML = originalBtnHtml;
        }
    });

    // Funções de Log
    const logList = document.getElementById('log-list');
    const clearLogBtn = document.getElementById('clear-log-btn');

    let logsArray = JSON.parse(localStorage.getItem('cryptoLogs')) || [];

    function renderLogs() {
        if (logsArray.length === 0) {
            logList.innerHTML = '<div class="no-logs">Nenhuma operação realizada ainda.</div>';
            return;
        }
        
        logList.innerHTML = '';
        
        logsArray.forEach(log => {
            const entry = document.createElement('div');
            entry.className = 'log-item';
            
            const typeLabel = log.mode === 'encrypt' ? 'Criptografado' : 'Descriptografado';
            const icon = log.mode === 'encrypt' ? 'bx-lock' : 'bx-lock-open';
            const colorClass = log.mode === 'encrypt' ? 'color-encrypt' : 'color-decrypt';
            
            entry.innerHTML = `
                <div class="log-item-header">
                    <span class="log-type ${colorClass}"><i class='bx ${icon}'></i> ${typeLabel}</span>
                    <span class="log-time">${log.time}</span>
                </div>
                <div class="log-content">
                    <div class="log-row"><strong>Original:</strong> <span>${escapeHtml(log.input)}</span></div>
                    <div class="log-row"><strong>Resultado:</strong> <span class="log-result">${escapeHtml(log.output)}</span></div>
                    <div class="log-row log-key"><strong>Chave:</strong> <span>${escapeHtml(log.key)}</span></div>
                </div>
            `;
            logList.appendChild(entry);
        });
    }

    function addLogEntry(mode, input, output, key) {
        const newLog = {
            mode: mode,
            input: input,
            output: output,
            key: key,
            time: new Date().toLocaleTimeString()
        };
        
        // Adiciona ao topo do array
        logsArray.unshift(newLog);
        
        // Limita o histórico a 50 itens para não sobrecarregar
        if (logsArray.length > 50) {
            logsArray.pop();
        }
        
        // Salva no localStorage
        localStorage.setItem('cryptoLogs', JSON.stringify(logsArray));
        renderLogs();
    }

    clearLogBtn.addEventListener('click', () => {
        logsArray = [];
        localStorage.removeItem('cryptoLogs');
        renderLogs();
    });

    function escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }

    // Renderiza o log inicial ao carregar a página
    renderLogs();
});
