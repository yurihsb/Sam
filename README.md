Markdown
# 🌿 Jardim de Ideias & Assistente Sam

O **Jardim de Ideias** é uma aplicação web desenvolvida em **Django** projetada para centralizar, organizar e gerenciar pensamentos, tarefas, perguntas, reflexões e insights. O grande diferencial do projeto é o **Sam**, um assistente de inteligência artificial de elite e altamente autônomo integrado diretamente ao chat para gerenciar dados, criar relatórios em Excel e documentos Word por meio de chamadas de ferramentas (*Function Calling*).

> ⚠️ **Aviso de Desenvolvimento:** Este projeto ainda **não está 100% pronto**. Novas funcionalidades, melhorias na interface e ajustes de estabilidade estão sendo implementados continuamente.

---

## 🚀 Funcionalidades Principais

* **Gerenciamento de Pensamentos (CRUD):** Crie, edite, filtre e exclua anotações categorizadas (ideia, tarefa, pergunta, reflexao, insight) com suporte a tags e anexos (imagens e PDFs).
* **Sam (Assistente IA Autônomo):** Um agente inteligente integrado via chat (alimentado primariamente por OpenAI e secundariamente por Anthropic Claude) capaz de:
  * Criar e buscar pensamentos diretamente no banco de dados via chat.
  * Gerar e exportar planilhas inteligentes em **Excel (`.xlsx`)** estruturadas.
  * Criar e formatar documentos profissionais em **Word (`.docx`)** sob demanda.
* **Autenticação Segura:** Suporte a login tradicional e autenticação via **Google OAuth**.
* **Interface Moderna:** Design responsivo e limpo com suporte a busca em tempo real e filtros rápidos.

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python, Django
* **Inteligência Artificial:** OpenAI API (GPT-4o-mini), Anthropic API (Claude) & Google GenAI
* **Manipulação de Arquivos:** `openpyxl` (Excel), `python-docx` (Word), Pillow (Imagens)
* **Banco de Dados:** SQLite (padrão do Django)
* **Estilização/Frontend:** HTML5, CSS3, JavaScript

---

## ⚙️ Pré-requisitos e Instalação

Certifique-se de ter o **Python** instalado em sua máquina. Siga os passos abaixo para rodar o projeto localmente:

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/jardim-de-ideias.git](https://github.com/seu-usuario/jardim-de-ideias.git)
   cd jardim-de-ideias
Crie e ative um ambiente virtual:

Bash
python -m venv venv

# No Windows:
venv\Scripts\activate

# No Linux/Mac:
source venv/bin/activate
Instale as dependências:

Bash
pip install -r requirements.txt
(Caso não tenha um requirements.txt, instale manualmente os pacotes principais: pip install django openai anthropic openpyxl python-docx pillow requests)

Configure as Variáveis de Ambiente:
Crie um arquivo .env na raiz do projeto (ou configure diretamente nas variáveis do seu sistema operacional) contendo as suas chaves de API:

Snippet de código
OPENAI_API_KEY=sua-chave-openai-aqui
ANTHROPIC_API_KEY=sua-chave-anthropic-aqui
GOOGLE_CLIENT_ID=seu-client-id-do-google (opcional para o OAuth)
GOOGLE_CLIENT_SECRET=seu-client-secret-do-google (opcional para o OAuth)
Execute as migrações do banco de dados:

Bash
python manage.py makemigrations
python manage.py migrate
Inicie o servidor de desenvolvimento:

Bash
python manage.py runserver
Acesse no navegador: http://127.0.0.1:8000/

💬 Exemplo de Uso com o Sam
Abra o chat com o assistente na interface e teste comandos autônomos como:

"Crie uma nova ideia de projeto chamada 'App de Finanças' com a tag 'financas'."

"Gere um relatório em Excel com todas as minhas tarefas pendentes."

"Faça um documento Word chamado 'Estratégia_2026' com um resumo sobre inteligência artificial."

🛡️ Licença
Este projeto é de uso livre para estudos, portfólios e desenvolvimento pessoal.
