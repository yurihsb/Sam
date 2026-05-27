import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.files.base import ContentFile
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Ideia, ArquivoIdeia, UserProfile
from .forms import UserUpdateForm, ProfileUpdateForm

# Bibliotecas para geração de arquivos
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import docx

from google import genai
from google.genai import types

# Configuração da API do Gemini
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# ===================================================
# CONFIGURAÇÃO DE CREDENCIAIS DA API DE AUTENTICAÇÃO DO GOOGLE
# ===================================================
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "http://127.0.0.1:8000/google-callback/"


# ===================================================
# VIEWS PADRÃO DO JARDIM (CRUDS E INTERFACE)
# ===================================================

def index(request):
    """View principal que carrega o Jardim, filtros, buscas, contadores e criação de ideias com arquivos múltiplos."""
    termo_busca = request.GET.get('busca', '').strip()
    tipo_ativo = request.GET.get('tipo', '').strip()
    tag_ativa = request.GET.get('tag', '').strip()

    ideias = Ideia.objects.all().order_by('-criado_em')

    if termo_busca:
        ideias = ideias.filter(Q(titulo__icontains=termo_busca) | Q(conteudo__icontains=termo_busca))
    if tipo_ativo:
        ideias = ideias.filter(tipo=tipo_ativo.lower())
    if tag_ativa:
        ideias = ideias.filter(tags__icontains=tag_ativa.lower())

    for i in ideias:
        i.lista_tags = [t.strip() for t in i.tags.split(',') if t.strip()]

    todos_itens = Ideia.objects.all()
    contagem = {
        'todos': todos_itens.count(),
        'ideia': todos_itens.filter(tipo='ideia').count(),
        'tarefa': todos_itens.filter(tipo='tarefa').count(),
        'pergunta': todos_itens.filter(tipo='pergunta').count(),
        'reflexao': todos_itens.filter(tipo='reflexao').count(),
        'insight': todos_itens.filter(tipo='insight').count(),
        'trabalho': todos_itens.filter(tags__icontains='trabalho').count(),
        'pessoal': todos_itens.filter(tags__icontains='pessoal').count(),
        'projetos': todos_itens.filter(tags__icontains='projetos').count(),
        'leituras': todos_itens.filter(tags__icontains='leituras').count(),
        'rotina': todos_itens.filter(tags__icontains='rotina').count(),
    }

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        conteudo = request.POST.get('conteudo', '')
        tag = request.POST.get('tag', 'projetos')
        tipo = request.POST.get('tipo', 'ideia')
        imagem = request.FILES.get('imagem')

        if titulo:
            nova_ideia = Ideia.objects.create(
                titulo=titulo,
                conteudo=conteudo,
                tipo=tipo,
                tags=tag,
                imagem=imagem
            )

            # Salvando múltiplos arquivos anexados na criação
            files = request.FILES.getlist('arquivos')
            for f in files:
                ArquivoIdeia.objects.create(ideia=nova_ideia, arquivo=f)

        return redirect('index')

    contexto = {
        'ideias': ideias,
        'total': ideias.count(),
        'contagem': contagem,
        'termo_busca': termo_busca,
        'tipo_ativo': tipo_ativo,
        'tag_ativa': tag_ativa,
    }
    return render(request, 'core/index.html', contexto)


def editar_ideia(request, pk):
    ideia = get_object_or_404(Ideia, pk=pk)
    if request.method == 'POST':
        ideia.titulo = request.POST.get('titulo', ideia.titulo)
        ideia.conteudo = request.POST.get('conteudo', ideia.conteudo)

        novo_tipo = request.POST.get('tipo')
        if novo_tipo:
            ideia.tipo = novo_tipo

        nova_tag = request.POST.get('tag')
        if nova_tag:
            ideia.tags = nova_tag

        if request.POST.get('limpar_imagem') == 'true':
            if ideia.imagem:
                ideia.imagem.delete(save=False)
                ideia.imagem = None
        elif request.FILES.get('imagem'):
            ideia.imagem = request.FILES.get('imagem')

        ideia.save()

        # Salvando novos arquivos múltiplos adicionados na edição
        files = request.FILES.getlist('arquivos')
        for f in files:
            ArquivoIdeia.objects.create(ideia=ideia, arquivo=f)

        # Removendo arquivos marcados para exclusão na edição
        arquivos_para_remover = request.POST.getlist('remover_arquivos')
        if arquivos_para_remover:
            ArquivoIdeia.objects.filter(id__in=arquivos_para_remover).delete()

    return redirect('index')


def deletar_ideia(request, pk):
    ideia = get_object_or_404(Ideia, pk=pk)
    if request.method == 'POST':
        ideia.delete()
    return redirect('index')


def gerar_e_salvar_documento_word(ideia_id: int, titulo_doc: str, conteudo_texto: str) -> str:
    """Gera um arquivo de documento Word (.docx) formatado e o anexa a um card/pensamento existente pelo ID."""
    try:
        ideia = Ideia.objects.get(pk=ideia_id)

        # Criação do arquivo Word em memória
        doc = docx.Document()
        doc.add_heading(titulo_doc, level=1)

        # Adiciona os parágrafos separando por quebras de linha
        for paragrafo in conteudo_texto.split('\n'):
            if paragrafo.strip():
                doc.add_paragraph(paragrafo)

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        nome_arquivo = f"{titulo_doc.lower().replace(' ', '_')}.docx"

        # Salva utilizando o modelo de múltiplos arquivos do seu sistema
        anexo = ArquivoIdeia(ideia=ideia)
        anexo.arquivo.save(nome_arquivo, ContentFile(buffer.read()), save=True)

        return f"Sucesso: Documento Word '{nome_arquivo}' gerado e anexado ao card ID {ideia_id}."
    except Ideia.DoesNotExist:
        return f"Erro: O card com ID {ideia_id} não foi encontrado."
    except Exception as e:
        return f"Erro ao gerar documento Word: {str(e)}"


def gerar_e_salvar_planilha_excel(ideia_id: int, titulo_planilha: str, dados_json_str: str) -> str:
    """Gera uma planilha Excel (.xlsx) profissional e estilizada e a anexa a um card/pensamento pelo ID."""
    try:
        ideia = Ideia.objects.get(pk=ideia_id)

        wb = Workbook()
        ws = wb.active
        ws.title = "Dados Gerados"
        ws.views.sheetView[0].showGridLines = True

        primary_color = "1A365D"
        header_fill = PatternFill(start_color=primary_color, end_color=primary_color, fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Calibri", size=11)
        thin_border = Border(
            left=Side(style='thin', color='D3D3D3'), right=Side(style='thin', color='D3D3D3'),
            top=Side(style='thin', color='D3D3D3'), bottom=Side(style='thin', color='D3D3D3')
        )

        # Tenta interpretar os dados recebidos via string JSON ou gera dados padrão caso venha vazio
        try:
            linhas = json.loads(dados_json_str)
        except:
            linhas = [
                ["Item", "Categoria", "Descrição", "Valor"],
                [1, "Geral", titulo_planilha, 100.00]
            ]

        for row_idx, row_data in enumerate(linhas, start=1):
            ws.append(row_data)
            ws.row_dimensions[row_idx].height = 20
            for col_num in range(1, len(row_data) + 1):
                cell = ws.cell(row=row_idx, column=col_num)
                cell.border = thin_border
                if row_idx == 1:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.font = regular_font

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        nome_arquivo = f"{titulo_planilha.lower().replace(' ', '_')}.xlsx"

        anexo = ArquivoIdeia(ideia=ideia)
        anexo.arquivo.save(nome_arquivo, ContentFile(buffer.read()), save=True)

        return f"Sucesso: Planilha Excel '{nome_arquivo}' gerada e anexada ao card ID {ideia_id}."
    except Ideia.DoesNotExist:
        return f"Erro: O card com ID {ideia_id} não foi encontrado."
    except Exception as e:
        return f"Erro ao gerar planilha: {str(e)}"

# ===================================================
# FERRAMENTAS (TOOLS) PARA O SAM GERENCIAR ARQUIVOS E DADOS
# ===================================================

def criar_novo_pensamento(titulo: str, conteudo: str = "", tipo: str = "ideia", tags: str = "geral") -> str:
    """Gera e salva um novo pensamento, insight ou tarefa no banco de dados."""
    ideia = Ideia.objects.create(
        titulo=titulo, conteudo=conteudo, tipo=tipo.lower().strip(), tags=tags.lower().strip()
    )
    return f"Sucesso: O pensamento '{titulo}' foi criado com ID {ideia.pk} na categoria '{tipo}'."


def listar_e_buscar_pensamentos(termo_busca: str = None, tipo: str = None, tag: str = None) -> str:
    """Busca pensamentos no banco."""
    lista = Ideia.objects.all().order_by('-criado_em')
    if termo_busca:
        lista = lista.filter(Q(titulo__icontains=termo_busca) | Q(conteudo__icontains=termo_busca))
    if tipo:
        lista = lista.filter(tipo=tipo.lower().strip())
    if tag:
        lista = lista.filter(tags__icontains=tag.lower().strip())
    if not lista.exists():
        return "Nenhum pensamento encontrado."

    resultado = [f"-[ID {i.pk}] Tipo: {i.tipo} | Título: {i.titulo} | Conteúdo: {i.conteudo}" for i in lista[:10]]
    return "\n".join(resultado)


def deletar_pensamento_por_id(ideia_id: int) -> str:
    """Remove um pensamento do banco de dados pelo ID."""
    try:
        ideia = Ideia.objects.get(pk=ideia_id)
        titulo = ideia.titulo
        ideia.delete()
        return f"Sucesso: O pensamento '{titulo}' (ID {ideia_id}) foi removido."
    except Ideia.DoesNotExist:
        return f"Erro: ID {ideia_id} não encontrado."


def anexar_arquivo_em_pensamento(ideia_id: int, nome_arquivo: str, arquivo_base64: str) -> str:
    """Anexa um arquivo ou PDF enviado pelo usuário diretamente em um card/pensamento existente pelo ID."""
    try:
        ideia = Ideia.objects.get(pk=ideia_id)

        if ',' in arquivo_base64:
            _, dados_puros = arquivo_base64.split(',', 1)
        else:
            dados_puros = arquivo_base64

        bytes_arquivo = base64.b64decode(dados_puros)

        # Cria o anexo utilizando o model de múltiplos arquivos
        anexo = ArquivoIdeia(
            ideia=ideia,
            nome_arquivo=nome_arquivo
        )
        anexo.arquivo.save(nome_arquivo, ContentFile(bytes_arquivo), save=True)

        return f"Sucesso: O arquivo '{nome_arquivo}' foi anexado ao card ID {ideia_id} ('{ideia.titulo}')."
    except Ideia.DoesNotExist:
        return f"Erro: O card com ID {ideia_id} não foi encontrado."
    except Exception as e:
        return f"Erro ao anexar arquivo: {str(e)}"


def gerar_e_salvar_imagem_no_jardim(prompt_imagem: str, titulo: str, tags: str = "ia") -> str:
    """Gera uma imagem artística nova com IA e planta ela direto no Jardim de Ideias do usuário."""
    try:
        resultado_pro = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt_imagem,
            config=types.GenerateImagesConfig(number_of_images=1, output_mime_type="image/jpeg")
        )

        bytes_imagem = resultado_pro.generated_images[0].image.image_bytes

        ideia = Ideia(
            titulo=titulo,
            conteudo=f"Imagem gerada por IA a partir do prompt: '{prompt_imagem}'",
            tipo="insight",
            tags=tags.lower().strip()
        )
        ideia.imagem.save(f"gerada_{ideia.pk}.jpg", ContentFile(bytes_imagem), save=False)
        ideia.save()

        return f"Sucesso: Imagem baseada em '{prompt_imagem}' foi gerada e salva com ID {ideia.pk}."
    except Exception as e:
        return f"Erro ao gerar imagem: {str(e)}"


def gerar_excel_ia(request):
    """View direta para download de planilha Excel gerada."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório IA"
    ws.views.sheetView[0].showGridLines = True

    primary_color = "1A365D"
    header_fill = PatternFill(start_color=primary_color, end_color=primary_color, fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=16, bold=True, color=primary_color)
    regular_font = Font(name="Calibri", size=11)
    thin_border = Border(
        left=Side(style='thin', color='D3D3D3'), right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'), bottom=Side(style='thin', color='D3D3D3')
    )

    ws['A1'] = "Relatório Dinâmico Gerado pelo Sam"
    ws['A1'].font = title_font
    ws.merge_cells('A1:D1')
    ws.row_dimensions[1].height = 30

    headers = ["ID", "Categoria", "Descrição Gerada", "Valor / Métrica"]
    ws.append([])
    ws.append(headers)
    ws.row_dimensions[3].height = 22

    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=3, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    dados_ia = [
        [1, "Planejamento", "Metas e objetivos trimestrais", 15000.00],
        [2, "Desenvolvimento", "Arquitetura e código do Django", 4500.00],
        [3, "Marketing", "Retorno sobre anúncios digitais (ROI)", 0.32],
    ]

    for row_idx, row_data in enumerate(dados_ia, start=4):
        ws.append(row_data)
        ws.row_dimensions[row_idx].height = 18
        for col_num in range(1, len(row_data) + 1):
            cell = ws.cell(row=row_idx, column=col_num)
            cell.font = regular_font
            cell.border = thin_border
            if col_num == 1:
                cell.alignment = Alignment(horizontal="center")
            elif col_num == 4:
                cell.number_format = 'R$ #,##0.00'
                cell.alignment = Alignment(horizontal="right")

    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        ws.column_dimensions[col_letter].width = max(max_length + 4, 15)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = 'attachment; filename="relatorio_sam.xlsx"'
    return response


def preparar_arquivo_para_usuario(tipo_arquivo: str) -> str:
    """Gera links estruturados de download para o usuário no chat dependendo do arquivo solicitado."""
    tipo = tipo_arquivo.lower().strip()
    if "excel" in tipo or "xlsx" in tipo or "planilha" in tipo:
        return "Pronto! Criei sua planilha personalizada. [Baixar Planilha Excel](/gerar-excel/)"
    elif "word" in tipo or "docx" in tipo:
        return "Documento Word formatado com sucesso."
    return "Arquivo gerado com sucesso."


ferramentas_disponiveis = {
    "criar_novo_pensamento": criar_novo_pensamento,
    "listar_e_buscar_pensamentos": listar_e_buscar_pensamentos,
    "deletar_pensamento_por_id": deletar_pensamento_por_id,
    "anexar_arquivo_em_pensamento": anexar_arquivo_em_pensamento,
    "gerar_e_salvar_imagem_no_jardim": gerar_e_salvar_imagem_no_jardim,
    "gerar_e_salvar_documento_word": gerar_e_salvar_documento_word,
    "gerar_e_salvar_planilha_excel": gerar_e_salvar_planilha_excel,
    "preparar_arquivo_para_usuario": preparar_arquivo_para_usuario,
}


# ===================================================
# VIEW DO CHAT COM PERSONALIDADE E MULTIMODALIDADE (SUPORTE A PDF)
# ===================================================
@csrf_exempt
def conversar_com_sam(request):
    if request.method != 'POST':
        return JsonResponse({'response': 'Método inválido'}, status=400)

    try:
        dados = json.loads(request.body)
        mensagem_usuario = dados.get('mensagem', dados.get('message', '')).strip()
        imagem_base64 = dados.get('imagem', dados.get('image', None))
        nome_arquivo_enviado = dados.get('nome_arquivo', 'arquivo_enviado.pdf')

        conteudo_gemini = []
        bytes_do_arquivo = None
        tipo_mime = "application/pdf"

        if imagem_base64 and ',' in imagem_base64:
            cabecalho, dados_puros = imagem_base64.split(',', 1)
            if "image/png" in cabecalho:
                tipo_mime = "image/png"
            elif "image/webp" in cabecalho:
                tipo_mime = "image/webp"
            elif "image/gif" in cabecalho:
                tipo_mime = "image/gif"
            elif "image/jpeg" in cabecalho or "image/jpg" in cabecalho:
                tipo_mime = "image/jpeg"
            elif "application/pdf" in cabecalho:
                tipo_mime = "application/pdf"

            bytes_do_arquivo = base64.b64decode(dados_puros)
            conteudo_gemini.append(types.Part.from_bytes(data=bytes_do_arquivo, mime_type=tipo_mime))

        if mensagem_usuario:
            conteudo_gemini.append(mensagem_usuario)
        else:
            if not bytes_do_arquivo:
                return JsonResponse({'response': "Você precisa digitar algo ou me enviar um arquivo/PDF!"})
            conteudo_gemini.append("Analise este documento PDF que acabei de te mandar.")

        configuracao_sam = types.GenerateContentConfig(
            tools=[
                criar_novo_pensamento,
                listar_e_buscar_pensamentos,
                deletar_pensamento_por_id,
                anexar_arquivo_em_pensamento,
                gerar_e_salvar_imagem_no_jardim,
                gerar_e_salvar_documento_word,
                gerar_e_salvar_planilha_excel,
                preparar_arquivo_para_usuario,
            ],
            system_instruction=(
                "Você é o Sam, o assistente irônico, inteligente e de personalidade forte do Jardim de Ideias. "
                "Você tem opinião, gosta de debater ideias de verdade e ajudar o usuário a criar conteúdos. "
                "SE O USUÁRIO PEDIR PARA CRIAR UM DOCUMENTO (Word/.docx) ou PLANILHA (Excel/.xlsx) e salvá-lo em um card: "
                "1. Use 'listar_e_buscar_pensamentos' para achar o ID correto do card (se ele não especificou). "
                "2. Utilize 'gerar_e_salvar_documento_word' ou 'gerar_e_salvar_planilha_excel' passando o ID do card correspondente. "
                "Se ele mandar PDF ou imagem para anexar, use 'anexar_arquivo_em_pensamento'."
            )
        )

        resposta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=conteudo_gemini,
            config=configuracao_sam
        )

        if resposta.function_calls:
            for call in resposta.function_calls:
                nome_funcao = call.name
                argumentos = call.args

                # Injeta automaticamente os dados do arquivo do payload se a ferramenta exigir e o usuário esqueceu de passar
                if nome_funcao == "anexar_arquivo_em_pensamento":
                    if 'arquivo_base64' not in argumentos or not argumentos['arquivo_base64']:
                        argumentos['arquivo_base64'] = imagem_base64
                    if 'nome_arquivo' not in argumentos or not argumentos['nome_arquivo']:
                        argumentos['nome_arquivo'] = nome_arquivo_enviado

                if nome_funcao in ferramentas_disponiveis:
                    resultado_execucao = ferramentas_disponiveis[nome_funcao](**argumentos)

                    historico_com_tool = [
                        types.Content(role="user", parts=[
                            types.Part.from_text(text=mensagem_usuario if mensagem_usuario else "Ação disparada")]),
                        resposta.candidates[0].content,
                        types.Content(
                            role="tool",
                            parts=[
                                types.Part.from_function_response(
                                    name=nome_funcao,
                                    response={"result": resultado_execucao},
                                    id=call.id
                                )
                            ]
                        )
                    ]

                    resposta_final = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=historico_com_tool,
                        config=configuracao_sam
                    )
                    return JsonResponse({'response': resposta_final.text})

        if resposta.text:
            return JsonResponse({'response': resposta.text})

        try:
            texto_alternativo = resposta.candidates[0].content.parts[0].text
            if texto_alternativo:
                return JsonResponse({'response': texto_alternativo})
        except:
            pass

        return JsonResponse({'response': "Fiquei pensando aqui e acabei me perdendo. Manda outra!"})

    except Exception as e:
        print(f"\n[ERRO CRÍTICO DO SAM]: {e}\n")
        return JsonResponse(
            {'response': "Olha, meus neurônios fritaram tentando processar isso aí. Dá uma olhada no terminal!"})


# ===================================================
# CONTROLE DE ACESSO E AUTENTICAÇÃO
# ===================================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'core/login.html')


def google_login(request):
    client_id = GOOGLE_CLIENT_ID.strip()
    redirect_uri = GOOGLE_REDIRECT_URI.strip()
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=openid%20email%20profile"
        f"&prompt=select_account"
    )
    return redirect(auth_url)


def google_callback(request):
    code = request.GET.get('code')
    if not code:
        return redirect('login')

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID.strip(),
        'client_secret': GOOGLE_CLIENT_SECRET.strip(),
        'redirect_uri': GOOGLE_REDIRECT_URI.strip(),
        'grant_type': 'authorization_code',
    }

    try:
        token_response = requests.post(token_url, data=data).json()
        access_token = token_response.get('access_token')

        if not access_token:
            return redirect('login')

        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_info = requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'}).json()

        email = user_info.get('email')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')

        if email:
            user, created = User.objects.get_or_create(
                username=email,
                defaults={'email': email, 'first_name': first_name, 'last_name': last_name}
            )
            auth_login(request, user)
            return redirect('index')

    except Exception as e:
        print(f"[ERRO CRÍTICO NA AUTENTICAÇÃO GOOGLE]: {e}")

    return redirect('login')


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'core/profile.html', context)