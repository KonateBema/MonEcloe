from django.contrib.admin import AdminSite   # ✅ AJOUTE ÇA
from django.contrib import admin, messages
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.urls import path
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from .models import Product, Category, Supplier, SupplierDetail, HomePage, Commande ,Preinscription,Contact
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from .models import Slide, HomeSlide
from .models import Ecole, Certificat, Question, Choix, Resultat ,Association , Evenement, InscriptionAssociation
from django.db.models import Count
from .models import Formation  , CycleIngenieur# ajoute cette ligne si elle n'existe pas
from .models import Evenement_inst
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
import openpyxl
from reportlab.pdfgen import canvas
from .models import Inscription
# ==============================
#      PRODUCT ADMIN
# ==============================
@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        'image_tag', 'name', 'price', 'supplier', 'quantity', 'formatted_created_at',
        'stock_status', 'categories_list', 'short_description'
    )
    search_fields = ('name', 'price')
    list_filter = ('created_at', 'price', 'quantity')
    ordering = ('-created_at',)
    fields = ('name', 'price', 'quantity', 'description', 'supplier', 'created_at', 'categories', 'image', 'image_tag')
    readonly_fields = ('created_at', 'image_tag')
    list_per_page = 10
    list_editable = ('quantity',)
    date_hierarchy = 'created_at'
    actions = ['set_price_to_zero', 'duplicate_product', 'apply_discount']
    filter_horizontal = ('categories',)
    autocomplete_fields = ('categories',)

    def formatted_created_at(self, obj):
        return obj.created_at.strftime('%d-%m-%Y %H:%M:%S')
    formatted_created_at.short_description = 'Ajouté le'

    def short_description(self, obj):
        if obj.description:
            return obj.description[:40] + '...' if len(obj.description) > 40 else obj.description
        return 'Aucune description'
    short_description.short_description = 'Description'

    def set_price_to_zero(self, request, queryset):
        updated = queryset.update(price=0)
        self.message_user(request, f"{updated} produit(s) mis à 0.", messages.SUCCESS)
    set_price_to_zero.short_description = 'Mettre le prix à 0'

    def duplicate_product(self, request, queryset):
        count = 0
        for product in queryset:
            product.pk = None
            product.save()
            count += 1
        self.message_user(request, f"{count} produit(s) dupliqué(s).", messages.SUCCESS)
    duplicate_product.short_description = 'Dupliquer les produits'

    def apply_discount(self, request, queryset):
        from decimal import Decimal
        discount_percentage = Decimal("0.9")
        count = 0
        for product in queryset:
            if product.price:
                product.price = Decimal(product.price) * discount_percentage
                product.save()
                count += 1
        self.message_user(request, f"Remise de 10%% appliquée sur {count} produit(s).", messages.SUCCESS)
    apply_discount.short_description = "Appliquer une remise de 10%%"

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" style="border-radius:5px;" />', obj.image.url)
        return "Pas d'image"
    image_tag.short_description = 'Aperçu'


# ==============================
#      CATEGORY ADMIN
# ==============================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'products_count')
    search_fields = ('name',)
    list_filter = ('name',)
    ordering = ('name',)
    fields = ('name',)
    list_per_page = 10

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Nombre de produits'


# ==============================
#      SUPPLIER ADMIN
# ==============================
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    fields = ('name', 'phone')
    list_display = ('name', 'phone')
    search_fields = ('name',)


@admin.register(SupplierDetail)
class SupplierDetailAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'address', 'contact_email', 'website', 'contact_person')
    search_fields = ('contact_person',)
    list_filter = ('supplier',)
    fields = ('supplier', 'address', 'contact_email', 'website', 'contact_person', 'supplier_type', 
              'country', 'payment_terms', 'bank_account', 'region_served')
    list_per_page = 10


# ==============================
#      HOMEPAGE ADMIN
# ==============================
@admin.register(HomePage)
class HomePageAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'logo_tag', 'formatted_welcome_message', 'action1_message', 'action1_lien', 
                    'action2_message', 'action2_lien', 'formatted_contact_message', 'formatted_about_message',
                    'formatted_footer_message', 'footer_bouton_message')
    fields = ('logo_tag', 'logo', 'site_name', 'welcome_titre', 'welcome_message',
              'action1_message', 'action1_lien', 'action2_message', 'action2_lien',
              'contact_message', 'about_message', 'footer_message', 'footer_bouton_message')
    readonly_fields = ('logo_tag',)

    def logo_tag(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="100px" style="border-radius:5px;" />', obj.logo.url)
        return "Pas d'image"
    logo_tag.short_description = 'Logo'

    def formatted_welcome_message(self, obj):
        return format_html(obj.welcome_message)
    formatted_welcome_message.short_description = 'Message de bienvenue'

    def formatted_contact_message(self, obj):
        return format_html(obj.contact_message)
    formatted_contact_message.short_description = 'Message de contact'

    def formatted_about_message(self, obj):
        return format_html(obj.about_message)
    formatted_about_message.short_description = 'Message à propos'

    def formatted_footer_message(self, obj):
        return format_html(obj.footer_message)
    formatted_footer_message.short_description = 'Message du pied de page'

    def has_add_permission(self, request):
        return not HomePage.objects.exists()


# ==============================
#      COMMANDE ADMIN
# ==============================
@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'quantity', 'total_commande', 'customer_name', 'status_colored',
        'customer_email', 'customer_phone', 'created_at', 'payment', 'is_delivered'
    )
    list_editable = ('is_delivered',)
    search_fields = ('customer_name', 'customer_email', 'customer_phone', 'customer_address')
    list_filter = ('payment', 'is_delivered')
    fields = ('product', 'quantity', 'customer_name', 'customer_email', 'customer_phone',
              'customer_address', 'payment', 'is_delivered')
    list_per_page = 5

    def total_commande(self, obj):
        if obj.product and obj.product.price:
            return obj.quantity * obj.product.price
        return 0
    total_commande.short_description = 'Total (€)'

    def status_colored(self, obj):
        color = 'green' if obj.is_delivered else 'red'
        text = 'Livrée' if obj.is_delivered else 'En attente'
        return format_html('<strong style="color:{};">{}</strong>', color, text)
    status_colored.short_description = 'Statut'


# ==============================
#      ADMIN PERSONNALISÉ
# ==============================

# class MyAdminSite(admin.AdminSite):

#     def get_urls(self):
#         from django.urls import path
#         urls = super().get_urls()
#         custom_urls = [
#             path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
#         ]
#         return custom_urls + urls

#     def dashboard_view(self, request):
#         # --- Total d'étudiants préinscrits ---
#         total_preinscrits = Preinscription.objects.count()

#         # --- Nombre d'étudiants par formation ---
#         preinscrits_par_formation_qs = (
#             Preinscription.objects
#             .values('formation__nom')  # suppose que ton modèle Formation a un champ "nom"
#             .annotate(nombre=Count('id'))
#             .order_by('-nombre')
#         )

#         # Préparer une liste pour le tableau HTML et graphique
#         preinscrits_par_formation = []
#         formations_labels = []
#         formations_counts = []

#         for item in preinscrits_par_formation_qs:
#             formation = item['formation__nom'] or "Non défini"
#             nombre = item['nombre']

#             # Tableau HTML
#             preinscrits_par_formation.append(
#                 f"<tr><td>{formation}</td><td>{nombre}</td></tr>"
#             )

#             # Graphique
#             formations_labels.append(formation)
#             formations_counts.append(nombre)

#         context = dict(
#             self.each_context(request),
#             total_preinscrits=total_preinscrits,
#             preinscrits_par_formation=preinscrits_par_formation,
#             formations_labels=formations_labels,
#             formations_counts=formations_counts,
#         )

#         return TemplateResponse(request, "/dashboard.html", context)
# def index(self, request, extra_context=None):
    # extra_context = extra_context or {}

    # extra_context.update({
    #     'total_etudiants': Preinscription.objects.count(),
    #     'total_formations': Formation.objects.count(),
    #     'total_evenements': Evenement.objects.count(),
    #     'total_certificats': Certificat.objects.count(),
    # })

    # context = {
    #     **self.each_context(request),   # ⭐ OBLIGATOIRE POUR LA SIDEBAR
    #     **extra_context,
    # }

    # return TemplateResponse(request, "admin/dashboard.html", context)
class MyAdminSite(AdminSite):
    site_header = "GEM ADMIN"
    site_title = "GEM"
    index_title = "Tableau de bord"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}

        extra_context.update({
            'total_etudiants': Preinscription.objects.count(),
            'total_formations': Formation.objects.count(),
            'total_evenements': Evenement.objects.count(),
            'total_certificats': Certificat.objects.count(),
        })

        context = {
            **self.each_context(request),
            **extra_context,
        }

        return TemplateResponse(request, "admin/dashboard.html", context)

@admin.register(HomeSlide)
class HomeSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "image")

@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("title", "image")


@admin.register(Ecole)
class EcoleAdmin(admin.ModelAdmin):

    fieldsets = (

        ("Informations générales", {
            "fields": ("nom", "description", "image")
        }),

        ("Salles de classe", {
            "fields": ("image_classes", "description_classes")
        }),

        ("Cour de l’école", {
            "fields": ("image_cour", "description_cour")
        }),

        ("Salle des professeurs", {
            "fields": ("image_profs", "description_profs")
        }),
    )


# Pour Excel
@admin.register(Preinscription)
class PreinscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'nom', 'prenom', 'email', 'telephone', 'formation', 
        'commune', 'quartier','date_naissance','nationalite',
        'etablissement_origine','diplome','annee_obtention',
        'nom_pere','telephone_pere','adresse_parents','date_inscription'
    )
    list_filter = ('formation', 'date_inscription')
    search_fields = ('nom', 'prenom', 'email', 'telephone', 'formation')
    ordering = ('-date_inscription',)
    readonly_fields = ('date_inscription',)

    actions = ['export_excel', 'export_pdf']

    # ---------------- EXPORT EXCEL ----------------
    def export_excel(self, request, queryset):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Préinscriptions"

        headers = [
            "Nom", "Prénom", "Email", "Téléphone", "Formation",
            "Commune", "Quartier", "Date de naissance", "Nationalité",
            "Établissement", "Diplôme", "Année d'obtention",
            "Nom père", "Téléphone père", "Adresse parents", "Message", "Date inscription"
        ]
        sheet.append(headers)

        for obj in queryset:
            sheet.append([
                obj.nom, obj.prenom, obj.email, obj.telephone, obj.formation,
                obj.commune, obj.quartier, obj.date_naissance, obj.nationalite,
                obj.etablissement_origine, obj.diplome, obj.annee_obtention,
                obj.nom_pere, obj.telephone_pere, obj.adresse_parents,
                obj.message, obj.date_inscription.strftime("%Y-%m-%d %H:%M")
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=preinscriptions.xlsx'
        workbook.save(response)
        return response

    export_excel.short_description = "Exporter sélection en Excel"

    # ---------------- EXPORT PDF ----------------
    def export_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="preinscriptions.pdf"'

        pdf = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        page_num = 1
        numero_etudiant = 1

        for obj in queryset:
            y = height - 60  # marge du haut

            # ---------------- HEADER ----------------
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(50, y, f"Préinscription Étudiant n° {numero_etudiant}")
            y -= 30

            # Photo de l'étudiant
            if obj.photo:
                try:
                    img = ImageReader(obj.photo.path)
                    pdf.drawImage(img, width - 120, height - 100, width=80, height=80, preserveAspectRatio=True)
                except Exception as e:
                    print("Erreur chargement photo PDF:", e)

            # ---------------- INFORMATIONS PERSONNELLES ----------------
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, y, "Informations Personnelles")
            y -= 20

            def ligne_deux_colonnes(label1, val1, label2, val2):
                nonlocal y
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50, y, f"{label1}:")
                pdf.drawString(300, y, f"{label2}:")
                pdf.setFont("Helvetica", 12)
                pdf.drawString(120, y, val1 or "-")
                pdf.drawString(380, y, val2 or "-")
                y -= 18

            ligne_deux_colonnes("Nom", obj.nom, "Prénom", obj.prenom)
            ligne_deux_colonnes("Email", obj.email, "Téléphone", obj.telephone)
            ligne_deux_colonnes("Formation", obj.formation, "Commune", obj.commune)
            ligne_deux_colonnes("Quartier", obj.quartier, "Date Naiss", str(obj.date_naissance))

            # ---------------- INFORMATIONS ACADÉMIQUES ----------------
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, y, "Informations Académiques")
            y -= 20
            ligne_deux_colonnes("Nationalité", obj.nationalite, "école", obj.etablissement_origine)
            ligne_deux_colonnes("Diplôme", obj.diplome, "Année ", str(obj.annee_obtention))

            # ---------------- INFORMATIONS PARENTALES ----------------
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, y, "Informations Parentales")
            y -= 20
            ligne_deux_colonnes("Nom père", obj.nom_pere, "Tél père", obj.telephone_pere)
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(50, y, "Adresse parents:")
            pdf.setFont("Helvetica", 12)
            text = pdf.beginText(160, y)
            for line in (obj.adresse_parents or "-").splitlines():
                text.textLine(line)
                y -= 15
            pdf.drawText(text)
            y -= 10

            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(50, y, "Message:")
            pdf.setFont("Helvetica", 12)
            text = pdf.beginText(120, y)
            for line in (obj.message or "-").splitlines():
                text.textLine(line)
                y -= 15
            pdf.drawText(text)
            y -= 30

            # ---------------- FOOTER ----------------
            pdf.setLineWidth(0.5)
            pdf.line(30, 40, width - 30, 40)
            pdf.setFont("Helvetica", 10)
            pdf.drawString(50, 30, "Groupe Expert Métier (GEM) | www.gem.ci | +225 0150536686")
            pdf.drawRightString(width - 50, 30, f"Page {page_num}")

            pdf.showPage()
            page_num += 1
            numero_etudiant += 1

        pdf.save()
        return response

    export_pdf.short_description = "Exporter sélection en PDF"
@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'responsable', 'contact', 'image_preview')
    search_fields = ('nom', 'responsable')
    list_per_page = 10
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="70" style="border-radius:8px;" />',
                obj.image.url
            )
        return "Pas d’image"

    image_preview.short_description = "Aperçu"

class EvenementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'association', 'date_event')
    list_filter = ('association', 'date_event')
    search_fields = ('titre',)

class InscriptionAssociationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'association', 'email', 'date_inscription')
    list_filter = ('association',)
    search_fields = ('nom', 'email')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'email', 'telephone','message' ,'date_envoi')
    search_fields = ('nom', 'prenom', 'email')
    list_filter = ('date_envoi',)

# @admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_filiere','description','details' ,'image')
    list_filter = ('type_filiere',)
    search_fields = ('titre',)

# Définition des choix pour le type de filière

def dashboard_callback(request, context):
    context.update({

        "total_etudiants": Etudiant.objects.count(),
        "total_formations": Formation.objects.count(),
        "total_evenements": Evenement.objects.count(),
        "total_certificats": Certificat.objects.count(),

        "derniers_etudiants": Etudiant.objects.order_by("-id")[:5],

        "mois": ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin"],
        "totals": [12, 19, 7, 15, 22, 30],
    })

    return context

@admin.register(Evenement_inst)
class Evenement_instAdmin(admin.ModelAdmin):
    list_display = ('titre', 'image_preview', 'video_preview')
    fields = ('titre', 'image', 'video')
    readonly_fields = ('image_preview', 'video_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image'

    def video_preview(self, obj):
        if obj.video:
            return format_html(
                '<video width="100" height="50" controls>'
                '<source src="{}" type="video/mp4">'
                'Votre navigateur ne supporte pas la vidéo.'
                '</video>', obj.video.url)
        return "-"
    video_preview.short_description = 'Vidéo'
# ==============================
# Option avec personnalisation
@admin.register(CycleIngenieur)
class CycleIngenieurAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_cycle', 'description')  # colonnes affichées
    list_filter = ('type_cycle',)  # filtre par type
    search_fields = ('titre', 'description')  # barre de recherche
#      INSTANTIATION DE L'ADMIN PERSONNALISÉ

@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'nom', 'prenom', 'email', 'telephone', 'formation', 
        'commune', 'quartier','date_naissance','nationalite',
        'etablissement_origine','diplome','annee_obtention',
        'nom_pere','telephone_pere','adresse_parents','date_inscription'
    )
    list_filter = ('formation', 'date_inscription')
    search_fields = ('nom', 'prenom', 'email', 'telephone', 'formation')
    ordering = ('-date_inscription',)
    readonly_fields = ('date_inscription',)

    actions = ['export_excel', 'export_pdf']

    # ---------------- EXPORT EXCEL ----------------
    def export_excel(self, request, queryset):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Inscriptions"

        headers = [
            "Nom", "Prénom", "Email", "Téléphone", "Formation",
            "Commune", "Quartier", "Date de naissance", "Nationalité",
            "Établissement", "Diplôme", "Année d'obtention",
            "Nom père", "Téléphone père", "Adresse parents", "Date inscription"
        ]
        sheet.append(headers)

        for obj in queryset:
            sheet.append([
                obj.nom, obj.prenom, obj.email, obj.telephone, obj.formation,
                obj.commune, obj.quartier, obj.date_naissance, obj.nationalite,
                obj.etablissement_origine, obj.diplome, obj.annee_obtention,
                obj.nom_pere, obj.telephone_pere, obj.adresse_parents,
                obj.date_inscription.strftime("%Y-%m-%d %H:%M")
            ])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=inscriptions.xlsx'
        workbook.save(response)
        return response

    export_excel.short_description = "Exporter sélection en Excel"

    # ---------------- EXPORT PDF ----------------
    def export_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="inscriptions.pdf"'

        pdf = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        y = height - 50

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, y, "Liste des Inscriptions")
        y -= 30

        pdf.setFont("Helvetica", 10)

        for i, obj in enumerate(queryset, start=1):
            # Numérotation
            pdf.drawString(50, y, f"{i}. {obj.nom} {obj.prenom}")
            y -= 15

            # Infos principales
            lines = [
                f"Email: {obj.email}  Téléphone: {obj.telephone}",
                f"Formation: {obj.formation}  Commune: {obj.commune}  Quartier: {obj.quartier}",
                f"Date naissance: {obj.date_naissance}  Nationalité: {obj.nationalite}",
                f"Établissement: {obj.etablissement_origine}  Diplôme: {obj.diplome}  Année obtention: {obj.annee_obtention}",
                f"Nom père: {obj.nom_pere}  Téléphone père: {obj.telephone_pere}",
                f"Adresse parents: {obj.adresse_parents}",
            ]

            for line in lines:
                pdf.drawString(60, y, line)
                y -= 15

            # Photo si disponible
            if obj.photo:
                try:
                    pdf.drawImage(obj.photo.path, 400, y + 15, width=80, height=80)
                except Exception as e:
                    print("Erreur chargement photo PDF:", e)

            y -= 90  # espace entre les étudiants

            if y < 50:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 10)

        pdf.save()
        return response

    export_pdf.short_description = "Exporter sélection en PDF"
# ==============================
# admin_site = MyAdminSite(name='admin')  # remplace l'admin standard
# admin_site = MyAdminSite(name='admin')
admin_site = MyAdminSite(name='myadmin')

# Enregistrer les modèles sur l'admin personnalisé
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
admin_site.register(Formation)
admin_site.register(CycleIngenieur)
# admin_site.register(Formation, FormationAdmin)
admin_site.register(HomePage, HomePageAdmin)
admin_site.register(Contact, ContactAdmin)
# admin_site.register(Slide)
admin_site.register(Evenement_inst, Evenement_instAdmin)
admin_site.register(Certificat)
admin_site.register(Question)
admin_site.register(Choix)
admin_site.register(Resultat)
admin_site.register(Association, AssociationAdmin)
admin_site.register(HomeSlide, HomeSlideAdmin)  # <-- nouveau modèle
# Enregistrer Ecole sur l'admin personnalisé
admin_site.register(Ecole, EcoleAdmin)
admin_site.register(Preinscription, PreinscriptionAdmin)
admin_site.register(Inscription, InscriptionAdmin)
admin_site.register(Evenement, EvenementAdmin)
admin_site.register(InscriptionAssociation, InscriptionAssociationAdmin)