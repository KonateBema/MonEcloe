# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from .models import Preinscription
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.db.models import Q

from django.contrib.admin.models import LogEntry
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

import os
from .models import Product, HomePage, HomeSlide, Commande 
from .forms import CommandeForm
from reportlab.lib.pagesizes import A4
from .models import Product, HomePage, HomeSlide, Commande ,Ecole 
from .forms import CommandeForm
from .forms import PreinscriptionForm
from .models import Preinscription
from django.core.mail import send_mail
from django.contrib import messages
from reportlab.platypus import SimpleDocTemplate, Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Spacer

# import weasyprint  # optionnel si tu veux un PDF
# =================== HOME ===================

def home(request):
    home_data = HomePage.objects.first()
    slides = HomeSlide.objects.all()

    query = request.GET.get('q')

    products = Product.objects.filter(quantity__gt=0)

    # Produits en stock
    products = Product.objects.filter(quantity__gt=0)
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    # Toutes les écoles
    ecoles = Ecole.objects.all()

    return render(request, 'home.html', {
        'home_data': home_data,
        'products': products,
        'slides': slides,
        'query': query,
         'ecoles': ecoles,  # ✅ passe la liste des écoles
    })

       
    
# =================== COMMANDE ===================
def commande(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = CommandeForm(request.POST)
        quantity = int(request.POST.get('quantity', 1))

        if form.is_valid():
            cmd = form.save(commit=False)
            cmd.product = product
            cmd.quantity = quantity
            cmd.total_amount = product.price * quantity
            cmd.save()

            messages.success(request, "Commande enregistrée avec succès !")
            return redirect('commande_confirmation', cmd.id)
    else:
        form = CommandeForm()

    return render(request, 'commande.html', {
        'product': product,
        'form': form
    })


def commande_confirmation(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    return render(request, 'commande_confirmation.html', {'commande': commande})


# =================== GENERATION PDF ===================
def generate_pdf(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="commande_{commande.id}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')
    if os.path.exists(logo_path):
        p.drawImage(ImageReader(logo_path), 50, height - 47, width=80, height=25)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, height - 50, f"Confirmation de Commande - #{commande.id}")

    p.line(50, height - 60, 550, height - 60)

    y = height - 100
    details = [
        ("Client", commande.customer_name),
        ("Produit", commande.product.name),
        ("Quantité", str(commande.quantity)),
        ("Adresse", commande.customer_address),
        ("Paiement", commande.payment),
        ("Date", commande.created_at.strftime("%d/%m/%Y %H:%M")),
        ("Total", f"{commande.total_amount} €"),
    ]

    for label, value in details:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, f"{label} :")
        p.setFont("Helvetica", 12)
        p.drawString(250, y, value)
        y -= 25

    p.drawString(100, y - 30, "Merci pour votre confiance 🚀")
    p.showPage()
    p.save()

    return response


def dashboard_view(self, request):
    # 5 dernières commandes
    if request.user.has_perm('myapp.view_commande'):
        commandes = Commande.objects.order_by('-created_at')[:5]
    else:
        commandes = []
       
    # Stats mensuelles
    monthly_orders = (
        Commande.objects
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            total=Count("id"),
            delivered_count=Count("id", filter=Q(is_delivered=True)),
            pending_count=Count("id", filter=Q(is_delivered=False)),
        )
        .order_by("month")
    )
# Statistiques globales
    orders_pending_count = Commande.objects.filter(is_delivered=False).count()
    orders_delivered_count = Commande.objects.filter(is_delivered=True).count()
    context = dict(
        self.each_context(request),
        products_count=Product.objects.count(),
        orders_pending=Commande.objects.filter(is_delivered=False).count(),
        orders_delivered=Commande.objects.filter(is_delivered=True).count(),
        commande=last_commands,
        monthly_orders=monthly_orders,
    )

    return TemplateResponse(request, "admin/dashboard.html", context)

# def product_detail(request, id):
#     product = get_object_or_404(Product, id=id)
   

#     return render(request, 'product_detail.html', {
#         'product': product,
        
#     })
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
  
    # 🔁 Produits similaires (même catégorie)
    similar_products = Product.objects.filter(
       
    ).exclude(id=product.id)[:4]

    return render(request, 'product_detail.html', {
        'product': product,
       
        'similar_products': similar_products,
    })
   

def presentation_ecole(request):
    ecole = Ecole.objects.first()
    return render(request, "ecole.html", {"ecole": ecole})


def contact(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        objet = request.POST.get('objet')
        message = request.POST.get('message')
        consent = request.POST.get('consent')

        if not consent:
            messages.error(request, "Vous devez accepter le traitement des données.")
            return redirect('home')

        full_message = f"""
        Nom : {nom}
        Prénom : {prenom}
        Email : {email}
        Téléphone : {telephone}

        Message :
        {message}
        """

        # Envoi de l'email
        try:
            send_mail(
                subject=objet,
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],  # définir l'email de réception
            )
            messages.success(request, "Votre message a été envoyé avec succès !")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'envoi du message : {e}")

        return redirect('home')
    else:
        return redirect('home')

# def preinscription_view(request):
#     if request.method == 'POST':
#         form = PreinscriptionForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Votre préinscription a été envoyée avec succès !")
#             return redirect('preinscription')
#     else:
#         form = PreinscriptionForm()
#     return render(request, 'preinscription.html', {'form': form})

def preinscription_view(request):
    preinscrit = None

    if request.method == 'POST':
        form = PreinscriptionForm(request.POST)
        if form.is_valid():
            preinscrit = form.save()
            form = PreinscriptionForm()  # formulaire vidé après envoi
    else:
        form = PreinscriptionForm()

    return render(request, 'preinscription.html', {
        'form': form,
        'preinscrit': preinscrit
    })
# def preinscription_view(request):
#     if request.method == 'POST':
#         form = PreinscriptionForm(request.POST)
#         if form.is_valid():
#             preinscrit = form.save()  # on sauvegarde l'inscription
#             messages.success(request, "Votre préinscription a été envoyée avec succès !")

#             # On peut passer l'objet preinscrit au template pour impression
#             return render(request, 'preinscription.html', {
#                 'form': PreinscriptionForm(),  # un nouveau formulaire vide
#                 'preinscrit': preinscrit
#             })
#     else:
#         form = PreinscriptionForm()
#     return render(request, 'preinscription.html', {'form': form})

# def telecharger_fiche(request, pk):
#     preinscrit = get_object_or_404(Preinscription, pk=pk)

#     content = f"""
#     FICHE DE PRÉINSCRIPTION

#     Nom : {preinscrit.nom}
#     Prénom : {preinscrit.prenom}
#     Email : {preinscrit.email}
#     Téléphone : {preinscrit.telephone}
#     """

#     response = HttpResponse(content, content_type='text/plain')
#     response['Content-Disposition'] = f'attachment; filename="fiche_{preinscrit.pk}.txt"'

#     return response

# def telecharger_fiche(request, pk):
#     preinscrit = get_object_or_404(Preinscription, pk=pk)

#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="fiche_{pk}.pdf"'

#     doc = SimpleDocTemplate(response)
#     elements = []

#     styles = getSampleStyleSheet()
#     elements.append(Paragraph("FICHE DE PRÉINSCRIPTION", styles['Heading1']))
#     elements.append(Spacer(1, 12))

#     elements.append(Paragraph(f"Nom : {preinscrit.nom}", styles['Normal']))
#     elements.append(Paragraph(f"Prénom : {preinscrit.prenom}", styles['Normal']))
#     elements.append(Paragraph(f"Email : {preinscrit.email}", styles['Normal']))
#     elements.append(Paragraph(f"Téléphone : {preinscrit.telephone}", styles['Normal']))

#     doc.build(elements)
#     return response

def telecharger_fiche(request, pk):
    # Récupérer l'inscription
    preinscrit = get_object_or_404(Preinscription, pk=pk)

    # Création de la réponse HTTP pour un PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fiche_preinscription_{preinscrit.id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=60, bottomMargin=60)

    elements = []
    styles = getSampleStyleSheet()
    styleH = styles['Heading1']
    styleN = styles['Normal']

    # --- LOGO du site ---
    logo_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'logo.png')  # chemin vers ton logo statique
    if os.path.exists(logo_path):
        logo = Image(logo_path)
        logo.drawHeight = 1*inch
        logo.drawWidth = 2*inch
        elements.append(logo)
        elements.append(Spacer(1, 12))

    # --- TITRE ---
    elements.append(Paragraph("Fiche de Préinscription", styleH))
    elements.append(Spacer(1, 20))

    # --- TABLEAU DES INFORMATIONS ---
    data = [
        ["Nom", preinscrit.nom],
        ["Prénom", preinscrit.prenom],
        ["Email", preinscrit.email],
        ["Téléphone", preinscrit.telephone],
        ["Date de naissance", preinscrit.date_naissance.strftime("%d/%m/%Y")],
        ["Formation", preinscrit.formation],
        ["Message", preinscrit.message],
    ]

    table = Table(data, colWidths=[120, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 50))

    # --- PIED DE PAGE ---
    footer_text = Paragraph("CONSULTATION EN LIGNE DES DOSSIERS 2025-2026 https://inscription.mesrs-ci.net/", styleN)
    elements.append(footer_text)

    # Génération du PDF
    doc.build(elements)

    return response
    # Récupérer l'inscription
    preinscrit = get_object_or_404(Preinscription, pk=pk)

    # Création de la réponse HTTP pour un PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fiche_preinscription_{preinscrit.id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=60, bottomMargin=60)

    elements = []
    styles = getSampleStyleSheet()
    styleH = styles['Heading1']
    styleN = styles['Normal']

    # --- LOGO en haut ---
    if preinscrit.logo:  # si tu as ajouté un champ logo à Preinscription ou sinon tu peux mettre home_data.logo
        logo_path = preinscrit.logo.path  # ou mettre chemin statique: "myapp/static/logo.png"
        logo = Image(logo_path)
        logo.drawHeight = 1*inch
        logo.drawWidth = 2*inch
        elements.append(logo)
        elements.append(Spacer(1, 12))

    # --- TITRE ---
    elements.append(Paragraph("Fiche de Préinscription", styleH))
    elements.append(Spacer(1, 20))

    # --- TABLEAU DES INFORMATIONS ---
    data = [
        ["Nom", preinscrit.nom],
        ["Prénom", preinscrit.prenom],
        ["Email", preinscrit.email],
        ["Téléphone", preinscrit.telephone],
        ["Date de naissance", preinscrit.date_naissance.strftime("%d/%m/%Y")],
        ["Formation", preinscrit.formation],
        ["Message", preinscrit.message],
    ]

    table = Table(data, colWidths=[120, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 50))

    # --- PIED DE PAGE ---
    footer_text = Paragraph("BANQUE DE L’UNION-COTE D’IVOIRE – BDU-CI | www.bdu-ci.ci", styleN)
    elements.append(footer_text)

    # Génération du PDF
    doc.build(elements)

    return response
    # preinscrit = Preinscrit.objects.get(pk=pk)
    preinscrit = get_object_or_404(Preinscription, pk=pk)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fiche_preinscription_{preinscrit.nom}.pdf"'

    doc = SimpleDocTemplate(response)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("<b>FICHE DE PRÉINSCRIPTION</b>", styles['Title']))
    elements.append(Spacer(1, 0.5 * inch))

    data = [
        ["Nom", preinscrit.nom],
        ["Prénom", preinscrit.prenom],
        ["Email", preinscrit.email],
        ["Téléphone", preinscrit.telephone],
        ["Date de naissance", str(preinscrit.date_naissance)],
        ["Formation", preinscrit.formation],
        ["Message", preinscrit.message],
    ]

    table = Table(data, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))

    elements.append(table)

    doc.build(elements)
    return response