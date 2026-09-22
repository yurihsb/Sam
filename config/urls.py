from core import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from core import views
from django.urls import path

urlpatterns = [
    # 1. TELA DE LOGIN (Página inicial)[cite: 2]
    path('', views.login_view, name='login'),
    # 2. ROTA QUE REDIRECIONA PARA O GOOGLE[cite: 2]
    path('google-login/', views.google_login, name='google_login'),
    # 3. ROTA QUE RECEBE OS DADOS DO GOOGLE (Callback)[cite: 2]
    path('google-callback/', views.google_callback, name='google_callback'),
    # 4. O SEU JARDIM DE IDEIAS PRINCIPAL (index.html)[cite: 2]
    path('jardim/', views.index, name='index'),
    # 5. ROTA DO PERFIL[cite: 2]
    path('profile/', views.profile_view, name='profile'),
    # Rota para o chat do Assistente Sam[cite: 2]
    path('chat-sam/', views.conversar_com_sam, name='chat_sam'),
    # Rota para deletar/retirar a ideia do banco[cite: 2]
    path('deletar/<int:pk>/', views.deletar_ideia, name='deletar_ideia'),
    # Rota para editar as ideias do banco[cite: 2]
    path('editar/<int:pk>/', views.editar_ideia, name='editar_ideia'),
    # Rota para download da planilha gerada pelo Sam[cite: 2]
    path('gerar-excel/', views.gerar_excel_ia, name='gerar_excel_ia'),
]
# Configuração para servir arquivos de mídia (imagens e documentos de upload) em desenvolvimento
if settings.DEBUG:
  urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
