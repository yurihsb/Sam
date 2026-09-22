document.addEventListener("DOMContentLoaded", function() {
    // --- CONTROLE DE ALTERAÇÃO EM MODO LISTA / GRADE ---
    const btnGrid = document.getElementById('btnViewGrid');
    const btnList = document.getElementById('btnViewList');
    const container = document.getElementById('ideasContainer');

    if (localStorage.getItem('viewMode') === 'list') {
        enableListView();
    }

    if (btnGrid) {
        btnGrid.addEventListener('click', () => {
            container.classList.remove('view-mode-list');
            btnList.classList.remove('active');
            btnGrid.classList.add('active');
            localStorage.setItem('viewMode', 'grid');
        });
    }

    if (btnList) {
        btnList.addEventListener('click', () => {
            enableListView();
        });
    }

    function enableListView() {
        if (!container) return;
        container.classList.add('view-mode-list');
        if (btnGrid) btnGrid.classList.remove('active');
        if (btnList) btnList.classList.add('active');
        localStorage.setItem('viewMode', 'list');
    }

    // --- CONTROLES DO MODAL DE NOVA IDEIA ---
    const ideaModal = document.getElementById('ideaModal');
    const openModalBtn = document.getElementById('openModalBtn');
    const closeModalX = document.getElementById('closeModalX');
    const closeModalBtn = document.getElementById('closeModalBtn');

    if (openModalBtn && ideaModal) {
        openModalBtn.addEventListener('click', () => {
            ideaModal.classList.add('active');
        });
    }

    if (closeModalX && ideaModal) {
        closeModalX.addEventListener('click', () => {
            ideaModal.classList.remove('active');
        });
    }

    if (closeModalBtn && ideaModal) {
        closeModalBtn.addEventListener('click', () => {
            ideaModal.classList.remove('active');
        });
    }

    if (ideaModal) {
        ideaModal.addEventListener('click', (e) => {
            if (e.target === ideaModal) {
                ideaModal.classList.remove('active');
            }
        });
    }

    // --- CONTROLES DA SIDEBAR DO CHAT DO SAM ---
    const chatOverlay = document.getElementById('chatOverlay');
    const openChatBtn = document.getElementById('openChatBtn');
    const closeChatX = document.getElementById('closeChatX');

    if (openChatBtn && chatOverlay) {
        openChatBtn.addEventListener('click', () => {
            chatOverlay.classList.add('active');
        });
    }

    if (closeChatX && chatOverlay) {
        closeChatX.addEventListener('click', () => {
            chatOverlay.classList.remove('active');
        });
    }

    if (chatOverlay) {
        chatOverlay.addEventListener('click', (e) => {
            if (e.target === chatOverlay) {
                chatOverlay.classList.remove('active');
            }
        });
    }

    // --- LÓGICA DE UPLOAD E PREVIEW DE IMAGEM/ARQUIVO DO SAM ---
    const samImageUpload = document.getElementById('samImageUpload');
    const samImgPreview = document.getElementById('samImgPreview');
    const samImgPreviewSrc = document.getElementById('samImgPreviewSrc');
    const samImgPreviewName = document.getElementById('samImgPreviewName');
    const samBtnRemoveImg = document.getElementById('samBtnRemoveImg');
    let imagemBase64 = null;
    let nomeArquivoAtual = 'arquivo_enviado.jpg';

    if (samImageUpload) {
        samImageUpload.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                nomeArquivoAtual = file.name;
                if (samImgPreviewName) samImgPreviewName.textContent = file.name;
                const reader = new FileReader();
                reader.onload = function(evt) {
                    if (samImgPreviewSrc) samImgPreviewSrc.src = evt.target.result;
                    imagemBase64 = evt.target.result;
                    if (samImgPreview) samImgPreview.style.display = 'flex';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    if (samBtnRemoveImg) {
        samBtnRemoveImg.addEventListener('click', function() {
            if (samImageUpload) samImageUpload.value = '';
            imagemBase64 = null;
            nomeArquivoAtual = 'arquivo_enviado.jpg';
            if (samImgPreview) samImgPreview.style.display = 'none';
        });
    }

    // --- LÓGICA DE ENVIO DO CHAT PARA A VIEW VIA FETCH ---
    const chatInputField = document.getElementById('chatInputField');
    const sendChatBtn = document.getElementById('sendChatBtn');
    const chatMessages = document.getElementById('chatMessages');

    function adicionarMensagem(texto, remetente) {
        if (!chatMessages) return;
        const div = document.createElement('div');
        div.classList.add('msg', remetente);

        // Suporte para interpretar links HTML gerados pelo Sam (ex: Excel)
        if (typeof texto === 'string' && texto.includes('<a href=')) {
            div.innerHTML = texto;
        } else {
            div.textContent = texto;
        }

        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function enviarMensagemSam() {
        if (!chatInputField) return;
        const mensagem = chatInputField.value ? chatInputField.value.trim() : '';

        if (!mensagem && !imagemBase64) return;

        if (mensagem) {
            adicionarMensagem(mensagem, 'user');
        } else {
            adicionarMensagem('📷 [Arquivo enviado]', 'user');
        }

        chatInputField.value = '';

        const imagemParaEnviar = imagemBase64;
        const nomeParaEnviar = nomeArquivoAtual;

        if (samBtnRemoveImg) samBtnRemoveImg.click();

        try {
            const urlEnvio = window.CHAT_SAM_URL || '/chat-sam/';
            const tokenCsrf = window.CSRF_TOKEN || '';

            const resposta = await fetch(urlEnvio, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': tokenCsrf
                },
                body: JSON.stringify({
                    mensagem: mensagem,
                    imagem: imagemParaEnviar,
                    nome_arquivo: nomeParaEnviar
                })
            });

            if (!resposta.ok) {
                throw new Error(`Erro no servidor: Status ${resposta.status}`);
            }

            const dados = await resposta.json();
            adicionarMensagem(dados.response, 'sam');
        } catch (erro) {
            adicionarMensagem('Deu ruim na conexão com o Sam. Veja o console.', 'sam');
            console.error(erro);
        }
    }

    if (sendChatBtn) {
        sendChatBtn.addEventListener('click', enviarMensagemSam);
    }

    if (chatInputField) {
        chatInputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                enviarMensagemSam();
            }
        });
    }
});