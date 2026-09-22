import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Tenta importar o convert_from_path do pdf2image
try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None


class Ideia(models.Model):
    TIPO_CHOICES = [
        ("ideia", "Ideia"),
        ("insight", "Insight"),
        ("tarefa", "Tarefa"),
        ("pergunta", "Pergunta"),
        ("reflexao", "Reflexão"),
        ("texto", "Texto Simples"),
        ("markdown", "Markdown"),
        ("arquivo", "Documento/Planilha"),
    ]

    titulo = models.CharField(max_length=200)
    conteudo = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="ideia")
    tags = models.CharField(
        max_length=200, blank=True, help_text="Separadas por vírgula"
    )
    fixado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    imagem = models.ImageField(upload_to="jardim_midia/", blank=True, null=True)

    def __str__(self):
        return self.titulo


class ArquivoIdeia(models.Model):
    ideia = models.ForeignKey(
        Ideia, on_delete=models.CASCADE, related_name="arquivos"
    )
    arquivo = models.FileField(upload_to="cards_documentos/")
    miniatura = models.ImageField(upload_to="cards_miniaturas/", blank=True, null=True)
    enviado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.arquivo and self.arquivo.name:
            return os.path.basename(self.arquivo.name)
        return "Arquivo"

    @property
    def nome_arquivo(self):
        if self.arquivo and self.arquivo.name:
            return os.path.basename(self.arquivo.name)
        return ""

    @property
    def eh_imagem(self):
        if not self.arquivo or not self.arquivo.name:
            return False
        extensoes_imagem = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
        return any(self.arquivo.name.lower().endswith(ext) for ext in extensoes_imagem)

    def save(self, *args, **kwargs):
        # Salva o arquivo primeiro para garantir que ele existe no disco
        super().save(*args, **kwargs)

        # Se for um PDF, tem arquivo físico e ainda não gerou miniatura
        # Se for um PDF, tem arquivo físico e ainda não gerou miniatura
        # Se for um PDF, tem arquivo físico e ainda não gerou miniatura
        if self.arquivo and self.arquivo.name.lower().endswith('.pdf') and not self.miniatura:
            if convert_from_path is not None:
                try:
                    # Deixando como None, ele busca diretamente no PATH do Windows que configuramos
                    caminho_poppler = None

                    imagens = convert_from_path(
                        self.arquivo.path,
                        first_page=1,
                        last_page=1,
                        dpi=80,
                        poppler_path=caminho_poppler
                    )

                    if imagens:
                        img_io = BytesIO()
                        imagens[0].save(img_io, format='JPEG', quality=80)
                        img_io.seek(0)

                        nome_base = os.path.splitext(os.path.basename(self.arquivo.name))[0]

                        self.miniatura.save(f"{nome_base}_thumb.jpg", ContentFile(img_io.read()), save=False)
                        ArquivoIdeia.objects.filter(pk=self.pk).update(miniatura=self.miniatura.name)

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"Erro detalhado ao gerar miniatura do PDF: {e}")

class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(blank=True, null=True, max_length=500)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


@receiver(post_save, sender=User)
def criar_ou_salvar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, "profile"):
            instance.profile.save()