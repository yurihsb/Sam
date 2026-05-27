// --- CONTROLE DE ALTERAÇÃO EM MODO LISTA / GRADE ---
const btnGrid = document.getElementById('btnViewGrid');
const btnList = document.getElementById('btnViewList');
const container = document.getElementById('ideasContainer');

if (localStorage.getItem('viewMode') === 'list') {
    enableListView();
}

btnGrid.addEventListener('click', () => {
    container.classList.remove('view-mode-list');
    btnList.classList.remove('active');
    btnGrid.classList.add('active');
    localStorage.setItem('viewMode', 'grid');
});

btnList.addEventListener('click', () => {
    enableListView();
});

function enableListView() {
    container.classList.add('view-mode-list');
    btnGrid.classList.remove('active');
    btnList.classList.add('active');
    localStorage.setItem('viewMode', 'list');
}

// --- CONTROLES DO MODAL DE NOVA IDEIA ---
const ideaModal = document.getElementById('ideaModal');
const openModalBtn = document.getElementById('openModalBtn');
const closeModalX = document.getElementById('closeModalX');
const closeModalBtn = document.getElementById('closeModalBtn');

// Abre o modal injetando a classe .active
openModalBtn.addEventListener('click', () => {
    ideaModal.classList.add('active');
});

// Fecha o modal clicando no 'X'
closeModalX.addEventListener('click', () => {
    ideaModal.classList.remove('active');
});

// Fecha o modal clicando no botão 'Cancelar'
closeModalBtn.addEventListener('click', () => {
    ideaModal.classList.remove('active');
});

// Fecha se o usuário clicar na área escura de fora do box
ideaModal.addEventListener('click', (e) => {
    if (e.target === ideaModal) {
        ideaModal.classList.remove('active');
    }
});

// --- CONTROLES DA SIDEBAR DO CHAT DO SAM ---
const chatOverlay = document.getElementById('chatOverlay');
const openChatBtn = document.getElementById('openChatBtn');
const closeChatX = document.getElementById('closeChatX');

openChatBtn.addEventListener('click', () => {
    chatOverlay.classList.add('active');
});

closeChatX.addEventListener('click', () => {
    chatOverlay.classList.remove('active');
});

chatOverlay.addEventListener('click', (e) => {
    if (e.target === chatOverlay) {
        chatOverlay.classList.remove('active');
    }
});

// --- LÓGICA DE UPLOAD E PREVIEW DE IMAGEM DO SAM ---
const samImageUpload = document.getElementById('samImageUpload');
const samImgPreview = document.getElementById('samImgPreview');
const samImgPreviewSrc = document.getElementById('samImgPreviewSrc');
const samImgPreviewName = document.getElementById('samImgPreviewName');
const samBtnRemoveImg = document.getElementById('samBtnRemoveImg');
let imagemBase64 = null;

samImageUpload.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        samImgPreviewName.textContent = file.name;
        const reader = new FileReader();
        reader.onload = function(evt) {
            samImgPreviewSrc.src = evt.target.result;
            imagemBase64 = evt.target.result; // Salva o Base64 para mandar no JSON
            samImgPreview.style.display = 'flex';
        };
        reader.readAsDataURL(file);
    }
});

samBtnRemoveImg.addEventListener('click', function() {
    samImageUpload.value = '';
    imagemBase64 = null;
    samImgPreview.style.display = 'none';
});

// --- LOGICA DE ENVIO DO CHAT PARA A VIEW VIA FETCH ---
const chatInputField = document.getElementById('chatInputField');
const sendChatBtn = document.getElementById('sendChatBtn');
const chatMessages = document.getElementById('chatMessages');

function adicionarMensagem(texto, remetente) {
    const div = document.createElement('div');
    div.classList.add('msg', remetente);
    div.textContent = texto;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll para baixo
}

async function enviarMensagemSam() {
    const mensagem = chatInputField.value.strip ? chatInputField.value.strip() : chatInputField.value.trim();

    if (!mensagem && !imagemBase64) return;

    // Mostra a mensagem do usuário na tela de imediato
    if (mensagem) {
        adicionarMensagem(mensagem, 'user');
    } else {
        adicionarMensagem('📷 [Imagem enviada]', 'user');
    }

    chatInputField.value = '';

    // Limpa o preview da imagem que acabou de ser enviada
    const imagemParaEnviar = imagemBase64;
    samBtnRemoveImg.click();

    try {
        // Usa as variáveis dinâmicas globais configuradas no index.html
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
                imagem: imagemParaEnviar
            })
        });

        if (!resposta.ok) {
            throw new Error(`Erro no servidor: Status ${resposta.status}`);
        }

        const dados = await browserDados(resposta);
        adicionarMensagem(dados.response, 'sam');
    } catch (erro) {
        adicionarMensagem('Deu ruim na conexão com o Sam. Veja o console.', 'sam');
        console.error(erro);
    }
}

// Função auxiliar para parsear JSON com segurança
async function browserDados(resposta) {
    return await resposta.json();
}

sendChatBtn.addEventListener('click', enviarMensagemSam);
chatInputField.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') enviarMensagemSam();
});