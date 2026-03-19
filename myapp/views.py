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
from .models import HomeData  # remplace HomeData par le nom exact si différent
from django.contrib.admin.models import LogEntry
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from .models import Programme  # Assure-toi que ton modèle s'appelle Programme
import os
from .models import Association , Evenement
from .models import Product, HomePage, HomeSlide, Commande 
from .forms import CommandeForm
from reportlab.lib.pagesizes import A4 ,landscape
from .models import Product, HomePage, HomeSlide, Commande ,Ecole 
from .forms import CommandeForm
from .forms import PreinscriptionForm ,InscriptionForm
from .models import Preinscription , InscriptionAssociation
from django.core.mail import send_mail
from django.contrib import messages
from reportlab.platypus import SimpleDocTemplate, Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Spacer
from .models import Certificat,Resultat
from .models import *
from .models import Formation , CycleIngenieur
from reportlab.platypus import Image
from reportlab.lib.units import mm
from reportlab.lib.units import cm  # <-- c'est ça qui manquait
import qrcode
import io
from datetime import datetime
import random
from io import BytesIO
# =================== HOME ===================

def home(request):

    if request.method == "POST":
        nom = request.POST.get("nom")
        prenom = request.POST.get("prenom")
        email = request.POST.get("email")
        telephone = request.POST.get("telephone")
        message_text = request.POST.get("message")

        Contact.objects.create(
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            message=message_text
        )

        messages.success(request, "Votre message a été envoyé avec succès !")
        return redirect('home')

    home_data = HomePage.objects.first()
    slides = HomeSlide.objects.all()
    query = request.GET.get('q')

    products = Product.objects.filter(quantity__gt=0)

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    ecoles = Ecole.objects.all()
    return render(request, 'home.html', {
        'home_data': home_data,
        'products': products,
        'slides': slides,
        'query': query,
        'ecoles': ecoles,
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


# def dashboard_view(self, request):
#     # 5 dernières commandes
#     if request.user.has_perm('myapp.view_commande'):
#         commandes = Commande.objects.order_by('-created_at')[:5]
#     else:
#         commandes = []
       
#     # Stats mensuelles
#     monthly_orders = (
#         Commande.objects
#         .annotate(month=TruncMonth("created_at"))
#         .values("month")
#         .annotate(
#             total=Count("id"),
#             delivered_count=Count("id", filter=Q(is_delivered=True)),
#             pending_count=Count("id", filter=Q(is_delivered=False)),
#         )
#         .order_by("month")
#     )
# # Statistiques globales
#     orders_pending_count = Commande.objects.filter(is_delivered=False).count()
#     orders_delivered_count = Commande.objects.filter(is_delivered=True).count()
#     context = dict(
#         self.each_context(request),
#         products_count=Product.objects.count(),
#         orders_pending=Commande.objects.filter(is_delivered=False).count(),
#         orders_delivered=Commande.objects.filter(is_delivered=True).count(),
#         commande=last_commands,
#         monthly_orders=monthly_orders,
#     )

#     return TemplateResponse(request, "admin/dashboard.html", context)
from django.shortcuts import render
from django.db.models import Count
from myapp.models import Preinscription
from django.db.models.functions import TruncMonth

def dashboard_view(request):
    """
    Vue pour le tableau de bord des étudiants
    """

    # 🔹 Statistiques globales
    total_etudiants = Preinscription.objects.count()
    total_formations = Preinscription.objects.values('formation').distinct().count()
    total_evenements = 5  # à remplacer par le vrai calcul
    total_certificats = 3  # à remplacer par le vrai calcul

    # 🔹 5 derniers étudiants inscrits
    derniers_etudiants = Preinscription.objects.order_by('-date_inscription')[:5]

    # 🔹 Nombre d'étudiants par formation
    etudiants_par_formation = (
        Preinscription.objects
        .values('formation')
        .annotate(total=Count('id'))
        .order_by('formation')
    )
    # convertir en dictionnaire pour le template
    etudiants_par_formation_dict = {item['formation']: item['total'] for item in etudiants_par_formation}

    # 🔹 Données pour le graphique mensuel (exemple : inscriptions par mois)
    monthly_inscriptions = (
        Preinscription.objects
        .annotate(month=TruncMonth('date_inscription'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    mois = [entry['month'].strftime("%b %Y") for entry in monthly_inscriptions]
    totals = [entry['total'] for entry in monthly_inscriptions]

    # 🔹 Contexte pour le template
    context = {
        'total_etudiants': total_etudiants,
        'total_formations': total_formations,
        'total_evenements': total_evenements,
        'total_certificats': total_certificats,
        'derniers_etudiants': derniers_etudiants,
        'etudiants_par_formation': etudiants_par_formation_dict,
        'mois': mois,
        'totals': totals,
    }

    return render(request, 'admin/dashboard.html', context)
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

#     home_data = {
#         'site_name': '',
#         'email': 'groupeexpertmetier@gmail.com',
#         'telephone': '+225 0150536686 / 2722204432'
#     }

#     # Pré-remplissage automatique de la formation si présent dans l'URL
#     initial_data = {}
#     if request.GET.get('formation'):
#         initial_data['formation'] = request.GET.get('formation')

#     if request.method == 'POST':
#         # ✅ IMPORTANT : ajouter request.FILES
#         form = PreinscriptionForm(request.POST, request.FILES)

#         if form.is_valid():
#             form.save()
#             messages.success(request, "Votre demande a été envoyée avec succès !")
#             return redirect('preinscription')

#         else:
#             messages.error(request, "Veuillez corriger les erreurs du formulaire.")

#     else:
#         form = PreinscriptionForm(initial=initial_data)

#     return render(request, 'preinscription.html', {
#         'form': form,
#         'home_data': home_data
#     })


def preinscription_view(request):
    if request.method == 'POST':
        form = PreinscriptionForm(request.POST, request.FILES)
        if form.is_valid():
            inscription = form.save()  # 🔥 ENREGISTREMENT

            # Redirection vers page succès avec ID
            return redirect('succes_preinscription', inscription_id=inscription.id)
    else:
        form = PreinscriptionForm()

    return render(request, 'preinscription.html', {'form': form})


def succes_preinscription(request, inscription_id):
    inscription = Preinscription.objects.get(id=inscription_id)

    return render(request, 'succes.html', {
        'inscription': inscription
    })

def telecharger_fiche(request, pk):
    # Récupérer l'inscription
    preinscrit = get_object_or_404(Preinscription, pk=pk)

    # Création de la réponse HTTP pour un PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fiche_preinscription_{preinscrit.nom}.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=140,   # marge pour header
        bottomMargin=60  # marge pour footer
    )

    elements = []
    styles = getSampleStyleSheet()

    # Titre principal
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>FICHE DE PRÉINSCRIPTION</b>", styles['Title']))
    elements.append(Spacer(1, 30))

    # Tableau des informations
    data = [
        ["Nom", preinscrit.nom],
        ["Prénom", preinscrit.prenom],
        ["Email", preinscrit.email],
        ["Téléphone", preinscrit.telephone],
        ["Date de naissance",
         preinscrit.date_naissance.strftime("%d/%m/%Y") if preinscrit.date_naissance else ""],
        ["Formation", preinscrit.formation],
        ["Commune", getattr(preinscrit, "commune", "")],
        ["Quartier", getattr(preinscrit, "quartier", "")],
        ["Message", preinscrit.message],
    ]

    table = Table(data, colWidths=[150, 330])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))

    elements.append(table)

    # Génération PDF avec header/footer
    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)

    return response

def header_footer(c, doc):
    c.saveState()
    width, height = A4

    # ===== HEADER =====
    logo_ecole = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    logo_ministere = os.path.join(settings.BASE_DIR, 'static', 'images', 'ministere.jpg')

    # Logos
    if os.path.exists(logo_ecole):
        c.drawImage(logo_ecole, 30, height - 100, width=60, height=60)

    if os.path.exists(logo_ministere):
        c.drawImage(logo_ministere, width - 90, height - 100, width=60, height=60)

    # Texte central
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 60, "RÉPUBLIQUE DE CÔTE D’IVOIRE")

    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 75, "Union – Discipline – Travail")

    # Ligne séparation
    c.line(30, height - 110, width - 30, height - 110)

    # ===== FOOTER =====
    c.line(30, 40, width - 30, 40)

    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 25,
        "Groupe Expert Métier (GEM) | www.gem.ci | +225 XX XX XX XX"
    )
    c.drawRightString(width - 30, 25, f"Page {doc.page}")

    c.restoreState()

def contact_view(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        prenom = request.POST.get("prenom")
        email = request.POST.get("email")
        telephone = request.POST.get("telephone")
        message_text = request.POST.get("message")

        Contact.objects.create(
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            message=message_text
        )

        # messages.success(request, "Votre message a été envoyé avec succès !")
        return redirect('home')

    return render(request, 'home.html')



def programmes_view(request):
    home_data = HomeData.objects.first()  # récupère la première ligne de ton modèle HomeData
    programmes = Programme.objects.all()  # récupère tous les programmes

    context = {
        'home_data': home_data,
        'programmes': programmes
    }
    return render(request, 'programmes.html', context)

def vie_associative(request):
    associations = Association.objects.all()
    evenements = Evenement.objects.order_by('date_event')[:6]

    context = {
        'associations': associations,
        'evenements': evenements,
    }

    return render(request, 'vie_associative.html', context)

def certificats(request):
    certificats = Certificat.objects.all()
    home_data = HomeData.objects.first()
    return render(request, 'certificats.html', {'certificats': certificats, 'home_data': home_data})

# def passer_certificat(request, id):

#     certificat = get_object_or_404(Certificat, id=id)
#     questions = Question.objects.filter(certificat=certificat)

#     if request.method == "POST":
#         score = 0
#         total = questions.count()

#         for question in questions:
#             reponse = request.POST.get(str(question.id))
#             if reponse:
#                 choix = Choix.objects.get(id=reponse)
#                 if choix.est_correct:
#                     score += 1

#         Resultat.objects.create(
#             certificat=certificat,
#             nom_etudiant=request.POST.get("nom"),
#             score=score
#         )

#         return render(request, "resultat.html", {
#             "score": score,
#             "total": total
#         })

#     return render(request, "passer_certificat.html", {
#         "certificat": certificat,
#         "questions": questions
#     })


# from .models import Certificat, Question, Choix, Resultat

# def passer_certificat(request, id):
#     certificat = get_object_or_404(Certificat, id=id)
#     questions = Question.objects.filter(certificat=certificat)

#     if request.method == "POST":
#         score = 0
#         total = questions.count()
#         nom_etudiant = request.POST.get("nom", "Anonyme")  # valeur par défaut

#         for question in questions:
#             reponse = request.POST.get(f"question_{question.id}")  # correspond au template
#             if reponse:
#                 choix = get_object_or_404(Choix, id=reponse)
#                 if choix.est_correct:
#                     score += 1

#         # Enregistrer le résultat
#         Resultat.objects.create(
#             certificat=certificat,
#             nom_etudiant=nom_etudiant,
#             score=score
#         )

#         # Calcul du pourcentage
#         pourcentage = (score / total) * 100 if total > 0 else 0

#         return render(request, "resultat.html", {
#             "score": score,
#             "total": total,
#             "pourcentage": pourcentage,
#             "certificat": certificat,
#             "cert": certificat   # 👈 IMPORTANT
#         })

#     return render(request, "passer_certificat.html", {
#         "certificat": certificat,
#         "questions": questions
#     })


def passer_certificat(request, id):
    # Récupération du certificat
    certificat = get_object_or_404(Certificat, id=id)
    questions = Question.objects.filter(certificat=certificat)

    if request.method == "POST":
        score = 0
        total = questions.count()
        nom_etudiant = request.POST.get("nom", "Anonyme")  # valeur par défaut

        # Calcul du score
        for question in questions:
            reponse = request.POST.get(f"question_{question.id}")
            if reponse:
                choix = get_object_or_404(Choix, id=reponse)
                if choix.est_correct:
                    score += 1

        # Enregistrer le résultat
        resultat = Resultat.objects.create(
            certificat=certificat,
            nom_etudiant=nom_etudiant,
            score=score
        )

        # Option 1 : redirection directe vers le PDF du certificat
        return redirect('generer_certificat_pdf', certificat_id=certificat.id)

        # Option 2 : si tu veux afficher le résultat avant de générer le PDF, 
        # tu peux rendre le template "resultat.html" avec :
        """
        pourcentage = (score / total) * 100 if total > 0 else 0
        return render(request, "resultat.html", {
            "score": score,
            "total": total,
            "pourcentage": pourcentage,
            "certificat": certificat,
            "cert": certificat,
            "resultat": resultat
        })
        """

    # Si GET, afficher le formulaire pour passer le certificat
    return render(request, "passer_certificat.html", {
        "certificat": certificat,
        "questions": questions
    })


def inscription_association(request, association_id):
    association = Association.objects.get(id=association_id)

    if request.method == "POST":
        nom = request.POST.get("nom")
        email = request.POST.get("email")
        telephone = request.POST.get("telephone")

        InscriptionAssociation.objects.create(
            association=association,
            nom=nom,
            email=email,
            telephone=telephone
        )

        return redirect('vie_associative')

    return render(request, "inscription_association.html", {
        "association": association
    })

# def formations(request):
#     tertiaires = Formation.objects.filter(type_filiere='tertiaire')
#     industrielles = Formation.objects.filter(type_filiere='industrielle')

#     return render(request, 'formations.html', {
#         'tertiaires': tertiaires,
#         'industrielles': industrielles,
#     })

def formations(request):

    context = {
        'bts': Formation.objects.filter(type_filiere='bts'),
        'licence': Formation.objects.filter(type_filiere='licence'),
        'master': Formation.objects.filter(type_filiere='master'),
        'cycles': Formation.objects.filter(type_filiere='ingenieur'),
        'embs': Formation.objects.filter(type_filiere='business'),
        'preparatoire': Formation.objects.filter(type_filiere='preparatoire'),
    }

    return render(request, 'formations.html', context)







@staff_member_required
def admin_dashboard(request):

    total_preinscrits = Preinscription.objects.count()

    stats = (
        Preinscription.objects
        .values('formation__nom')
        .annotate(total=Count('id'))
        .order_by('formation__nom')
    )

    labels = [item['formation__nom'] for item in stats]
    data = [item['total'] for item in stats]

    context = {
        'total_preinscrits': total_preinscrits,
        'stats': stats,
        'labels': labels,
        'data': data,
    }

    return render(request, "admin/dashboard.html", context)

def evenements_view(request):
    # Trier les événements institutionnels par titre (ordre alphabétique)
    evenements = Evenement_inst.objects.all().order_by('titre')  
    return render(request, 'evenements.html', {'evenements': evenements})

# def e3m_school(request):
#     return render(request, 'e3m_school.html')

# def e3m_school(request):
#     slides = Slide.objects.all()
#     filieres = ['Génie Civil', 'Environnement Durable', 'IA & Big Data']
#     return render(request, 'e3m_school.html', {'slides': slides, 'filieres': filieres})
from .models import E3MSchool

def e3m_school(request):

    slides = Slide.objects.all()

    bts = E3MSchool.objects.filter(type_filiere='bts')
    licence = E3MSchool.objects.filter(type_filiere='licence')
    master = E3MSchool.objects.filter(type_filiere='master')
    ingenieur = E3MSchool.objects.filter(type_filiere='ingenieur')
    preparatoire = E3MSchool.objects.filter(type_filiere='preparatoire')

    context = {
        'slides': slides,
        'bts': bts,
        'licence': licence,
        'master': master,
        'ingenieur': ingenieur,
        'preparatoire': preparatoire
    }

    return render(request, 'e3m_school.html', context)
    
def procedure_admission(request):
    # Version temporaire juste pour tester
    return HttpResponse("Page procédure d'admission")

def frais_scolarite(request):
    # Version simple juste pour tester
    return HttpResponse("Page Frais de scolarité")

def admission_view(request):
    return render(request, "admission.html")

def preinscription(request):
    return render(request, "preinscription.html")

from django.shortcuts import render

def filiere_tertiaires(request):
    tertiaires = Formation.objects.filter(type_filiere='tertiaire')
    return render(request, 'filiere_tertiaires.html', {'tertiaires': tertiaires})

def filiere_industrielles(request):
    industrielles = Formation.objects.filter(type_filiere='industrielle')
    return render(request, 'filiere_industrielles.htm', {'industrielles': industrielles})

def prepa(request):
    preparatoire = Formation.objects.filter(type_filiere='preparatoire')
    return render(request, 'annee_prepa.html', {'preparatoire': preparatoire})



def licence(request):
    licences = CycleIngenieur.objects.filter(type_cycle='licence')
    return render(request, 'licence.html', {'licences': licences})




def masters1(request):
    master1_list = CycleIngenieur.objects.filter(type_cycle='master1')
    master2_list = CycleIngenieur.objects.filter(type_cycle='master2')
    return render(request, 'masters1.html', {
        'master1_list': master1_list,
        'master2_list': master2_list
    })



def embs(request):
    embs = Formation.objects.filter(type_filiere='embs')
    return render(request, 'filiere_embs.html', {'embs': embs})

def cycle_ingenieur(request):
    licences = CycleIngenieur.objects.filter(type_cycle='licence')
    master1s = CycleIngenieur.objects.filter(type_cycle='master1')
    master2s = CycleIngenieur.objects.filter(type_cycle='master2')

    context = {
        'licences': licences,
        'master1s': master1s,
        'master2s': master2s,
    }
    return render(request, 'licence.html', context)

# from django.shortcuts import render, redirect
# from .models import Preinscription  # ou un modèle Inscription si différent
# from django.utils import timezone

# def inscription_view(request):
#     if request.method == "POST":
#         form = InscriptionForm(request.POST, request.FILES)

#         if form.is_valid():
#             form.save()
#             messages.success(request, "Votre inscription a été envoyée avec succès !")
#             # return redirect('inscription_succes', pk=inscription.id)
#             return redirect('inscription')
#         else:
#            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
#     else:
#         form = InscriptionForm()

#     derniers_inscrits = Inscription.objects.order_by('-date_inscription')[:5]

#     context = {
#         'form': form,
#         'page_title': "Inscription en ligne",
#         'derniers_inscrits': derniers_inscrits,
#     }

#     return render(request, 'inscription.html', context)

def inscription_view(request):
    if request.method == "POST":
        form = InscriptionForm(request.POST, request.FILES)

        if form.is_valid():
            # ✅ Récupérer l'objet enregistré
            inscription = form.save()

            # messages.success(request, "Votre inscription a été envoyée avec succès !")

            # ✅ Redirection vers page succès avec ID
            return redirect('inscription_succes', pk=inscription.id)

        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = InscriptionForm()

    # ✅ Toujours exécuté si GET ou erreur
    derniers_inscrits = Inscription.objects.order_by('-date_inscription')[:5]

    context = {
        'form': form,
        'page_title': "Inscription en ligne",
        'derniers_inscrits': derniers_inscrits,
    }

    return render(request, 'inscription.html', context)

def inscription_succes(request, pk):
    inscription = Inscription.objects.get(id=pk)
    return render(request, 'inscription_succes.html', {
        'inscription': inscription
    })

from .models import Certificat, Question, Choix, Resultat

def passer_certificat(request, id):
    certificat = get_object_or_404(Certificat, id=id)
    questions = Question.objects.filter(certificat=certificat)

    if request.method == "POST":
        score = 0
        total = questions.count()
        nom_etudiant = request.POST.get("nom") or "Anonyme"

        # Calcul du score
        for question in questions:
            reponse = request.POST.get(f"question_{question.id}")
            if reponse:
                choix = get_object_or_404(Choix, id=reponse)
                if choix.est_correct:
                    score += 1

        # Enregistrer le résultat
        resultat = Resultat.objects.create(
            certificat=certificat,
            nom_etudiant=nom_etudiant,
            score=score
        )

        pourcentage = (score / total) * 100 if total > 0 else 0
        reussite = pourcentage >= 50  # condition de réussite

        # On rend le template résultat avec le résultat et certificat
        return render(request, "resultat.html", {
            "score": score,
            "total": total,
            "pourcentage": round(pourcentage, 2),
            "reussite": reussite,
            "certificat": certificat,
            "resultat": resultat  # 🔑 pour générer le PDF
        })

    return render(request, "passer_certificat.html", {
        "certificat": certificat,
        "questions": questions
    })
# def generer_certificat_pdf(request, resultat_id):
#     resultat = get_object_or_404(Resultat, id=resultat_id)
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="Certificat_{resultat.nom_etudiant}.pdf"'

#     buffer = BytesIO()
#     p = canvas.Canvas(buffer, pagesize=A4)
#     width, height = A4

#     # Fond et titre
#     p.setFont("Helvetica-Bold", 28)
#     p.drawCentredString(width / 2, height - 5*cm, "Certificat de Réussite")

#     p.setFont("Helvetica", 20)
#     p.drawCentredString(width / 2, height - 7*cm, f"Décerné à : {resultat.nom_etudiant}")

#     p.setFont("Helvetica", 18)
#     p.drawCentredString(width / 2, height - 9*cm, f"Pour avoir réussi : {resultat.certificat.titre}")

#     p.setFont("Helvetica", 16)
#     p.drawCentredString(width / 2, height - 11*cm, f"Score : {resultat.score} / {resultat.certificat.questions.count()}")

#     # Date
#     import datetime
#     date_str = datetime.date.today().strftime("%d/%m/%Y")
#     p.setFont("Helvetica-Oblique", 14)
#     p.drawCentredString(width / 2, height - 13*cm, f"Date : {date_str}")

#     p.showPage()
#     p.save()

#     pdf = buffer.getvalue()
#     buffer.close()
#     response.write(pdf)
#     return response

from datetime import date

def generer_certificat_pdf(request, certificat_id):

    certificat = Certificat.objects.get(id=certificat_id)

    utilisateur = request.user

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="certificat.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)

    width, height = A4

    # Bordure
    pdf.rect(1*cm, 1*cm, width-2*cm, height-2*cm)

    # Titre
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width/2, height-4*cm, "CERTIFICAT")

    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(width/2, height-6*cm, "Ce certificat est décerné à")

    # Nom utilisateur
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width/2, height-8*cm, utilisateur.username)

    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(width/2, height-10*cm, "Pour avoir réussi la certification")

    # Nom certification
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width/2, height-12*cm, certificat.titre)

    # Date
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        width/2,
        height-15*cm,
        f"Délivré le {date.today().strftime('%d/%m/%Y')}"
    )

    # Signature
    pdf.drawString(width-7*cm, 3*cm, "Signature")

    pdf.save()

    return response

# def telecharger_certificat(request, resultat_id):
#     # Récupérer le résultat et le certificat
#     resultat = get_object_or_404(Resultat, id=resultat_id)
#     certificat = resultat.certificat

#     # Créer la réponse PDF
#     response = HttpResponse(content_type='application/pdf')
#     filename = f"Certificat_{resultat.nom_etudiant}.pdf"
#     response['Content-Disposition'] = f'attachment; filename="{filename}"'

#     # Canvas
#     # c = canvas.Canvas(response, pagesize=A4)
#     # width, height = A4
#     # Canvas
#     c = canvas.Canvas(response, pagesize=landscape(A4))
#     width, height = landscape(A4)  # largeur et hauteur ajustées pour paysage
#     # -------------------------------
#     # Fond très léger
#     # -------------------------------
#     c.setFillColor(colors.HexColor("#fffaf0"))
#     c.rect(0, 0, width, height, fill=True, stroke=False)

#     # -------------------------------
#     # Bordure décorative dorée
#     # -------------------------------
#     c.setStrokeColor(colors.HexColor("#DAA520"))  # Gold
#     c.setLineWidth(5)
#     c.rect(1.5*cm, 1.5*cm, width - 3*cm, height - 3*cm)

#     c.setStrokeColor(colors.HexColor("#FFD700"))  # Light gold inner
#     c.setLineWidth(2)
#     c.rect(2*cm, 2*cm, width - 4*cm, height - 4*cm)
#     # -------------------------------
#     # Logo de l’école (à gauche)
#     # -------------------------------
#     logo_path = "static/images/logo.png"  # <-- ton logo
#     c.drawImage(
#         logo_path,
#         3*cm,                 # x : 2 cm du bord gauche
#         height - 4.5*cm,      # y : un peu en dessous du haut de la page
#         width=3*cm,           # largeur réduite
#         height=2*cm,          # hauteur réduite
#         mask='auto'
#     )

#     # Numéro unique du certificat
#     # -------------------------------
#     # Numéro unique du certificat (aligné à droite du logo)
#     cert_number = f"E3M-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
#     c.setFont("Helvetica-Oblique", 12)
#     c.setFillColor(colors.gray)
#     c.drawRightString(width - 5*cm, height - 3.5*cm , f"Certificat N°: {cert_number}")

#     # -------------------------------
#     # Titre
#     # -------------------------------
#     c.setFont("Helvetica-Bold", 36)
#     c.setFillColor(colors.HexColor("#0d6efd"))
#     c.drawCentredString(width/2, height - 6.5*cm, "Certificat de Réussite")
#     # -------------------------------
#     # Nom de l’étudiant
#     # -------------------------------
#     c.setFont("Helvetica-Bold", 28)
#     c.setFillColor(colors.black)
#     c.drawCentredString(width/2, height - 10*cm, f"{resultat.nom_etudiant}")
#     # -------------------------------
#     # Message
#     # -------------------------------
#     c.setFont("Helvetica", 16)
#     c.drawCentredString(width/2, height - 12*cm, "A complété avec succès la certification :")

#     c.setFont("Helvetica-BoldOblique", 22)
#     c.setFillColor(colors.HexColor("#6610f2"))
#     c.drawCentredString(width/2, height - 14*cm, f"{certificat.titre}")
#     # -------------------------------
#     # Score et détails
#     # -------------------------------
#     c.setFont("Helvetica", 14)
#     total_questions = certificat.question_set.count()
#     c.drawCentredString(width/2, height - 16*cm, f"Score obtenu : {resultat.score} / {total_questions}")
#     # -------------------------------
#     # Signature de l'école (texte "GEM")
#     c.setFont("Helvetica-Bold", 16)
#     # c.drawString(3*cm, 4*cm, "Signature GEM")  # y = 4 cm au lieu de 3 cm
#     c.drawString(3*cm, 4*cm, "Signature GEM")
#     # -------------------------------
#     # Footer
#     # -------------------------------
#     c.setFont("Helvetica-Oblique", 10)
#     c.setFillColor(colors.gray)
#     c.drawCentredString(width/2, 3*cm, "Certificat généré automatiquement par E3M School")  # y = 3 cm au lieu de 2 cm
#     # Finaliser le PDF
#     c.showPage()
#     c.save()

#     return response

def telecharger_certificat(request, resultat_id):

    # Récupérer résultat
    resultat = get_object_or_404(Resultat, id=resultat_id)
    certificat = resultat.certificat

    # Réponse PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f"Certificat_{resultat.nom_etudiant}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Page paysage
    c = canvas.Canvas(response, pagesize=landscape(A4))
    width, height = landscape(A4)

    # -------------------------------
    # Fond
    # -------------------------------
    c.setFillColor(colors.HexColor("#fffaf0"))
    c.rect(0, 0, width, height, fill=True, stroke=False)

    # -------------------------------
    # Bordure dorée
    # -------------------------------
    c.setStrokeColor(colors.HexColor("#DAA520"))
    c.setLineWidth(5)
    c.rect(1.5*cm, 1.5*cm, width - 3*cm, height - 3*cm)

    c.setStrokeColor(colors.HexColor("#FFD700"))
    c.setLineWidth(2)
    c.rect(2*cm, 2*cm, width - 4*cm, height - 4*cm)

    # -------------------------------
    # Logo à gauche
    # -------------------------------
    logo_path = "static/images/logo.png"

    c.drawImage(
        logo_path,
        3*cm,
        height - 4.5*cm, 
        width=3*cm,  
        height=2*cm, 
        mask='auto'
    )

    # logo_path = "static/images/logo.png"  # <-- ton logo
#     c.drawImage(
#         logo_path,
#         3*cm,                 # x : 2 cm du bord gauche
#         height - 4.5*cm,      # y : un peu en dessous du haut de la page
#         width=3*cm,           # largeur réduite
#         height=2*cm,          # hauteur réduite
#         mask='auto'
#     )


    # -------------------------------
    # Numéro certificat à droite
    # -------------------------------
    cert_number = f"E3M-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"

    c.setFont("Helvetica-Oblique", 12)
    c.setFillColor(colors.gray)

    c.drawRightString(
        width - 3*cm,
        height - 3*cm,
        f"Certificat N°: {cert_number}"
    )

    # -------------------------------
    # Titre
    # -------------------------------
    c.setFont("Helvetica-Bold", 40)
    c.setFillColor(colors.HexColor("#0d6efd"))

    c.drawCentredString(
        width/2,
        height - 7*cm,
        "CERTIFICAT DE RÉUSSITE"
    )

    # -------------------------------
    # Nom étudiant
    # -------------------------------
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(colors.black)

    c.drawCentredString(
        width/2,
        height - 10*cm,
        resultat.nom_etudiant
    )

    # -------------------------------
    # Message
    # -------------------------------
    c.setFont("Helvetica", 18)

    c.drawCentredString(
        width/2,
        height - 12*cm,
        "A complété avec succès la certification :"
    )

    # -------------------------------
    # Nom certification
    # -------------------------------
    c.setFont("Helvetica-BoldOblique", 24)
    c.setFillColor(colors.HexColor("#6610f2"))

    c.drawCentredString(
        width/2,
        height - 14*cm,
        certificat.titre
    )

    # -------------------------------
    # Score
    # -------------------------------
    total_questions = certificat.question_set.count()

    c.setFont("Helvetica", 16)
    c.setFillColor(colors.black)

    c.drawCentredString(
        width/2,
        height - 16*cm,
        f"Score obtenu : {resultat.score} / {total_questions}"
    )
# -------------------------------
# QR CODE de vérification
# -------------------------------

    verification_url = f"http://127.0.0.1:8000/verifier-certificat/{resultat.id}/"

    qr = qrcode.make(verification_url)

    buffer = BytesIO()
    qr.save(buffer)

    qr_image = ImageReader(buffer)

    c.drawImage(
    qr_image,
    width - 6*cm,
    4*cm,
    width=3*cm,
    height=3*cm
  )

    c.setFont("Helvetica", 9)
    c.drawRightString(width - 3*cm, 3.5*cm, "Scanner pour vérifier")
    # -------------------------------
    # Signature GEM
    # -------------------------------
    c.setFont("Helvetica-Bold", 16)

    c.drawString(
        6*cm,
        5*cm,
        "Signature GEM"
    )

    # -------------------------------
    # Footer
    # -------------------------------
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(colors.gray)

    c.drawCentredString(
        width/2,
        3*cm,
        "Certificat généré automatiquement par E3M School"
    )

    # Finaliser
    c.showPage()
    c.save()

    return response
def pdf_certificats(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="certificats.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 3*cm

    pdf.setFont("Helvetica-Bold", 24)
    pdf.setFillColor(colors.HexColor("#0d6efd"))
    pdf.drawCentredString(width/2, y, "Liste des Certifications")
    y -= 2*cm

    certificats = Certificat.objects.all()

    for cert in certificats:

        pdf.setFont("Helvetica-Bold", 16)
        pdf.setFillColor(colors.HexColor("#6610f2"))
        pdf.drawString(3*cm, y, cert.titre)
        y -= 1*cm

        pdf.setFont("Helvetica", 12)
        pdf.setFillColor(colors.black)

        description = cert.description[:200] + ("..." if len(cert.description) > 200 else "")
        pdf.drawString(3*cm, y, description)
        y -= 1*cm

        if cert.lien_passage:
            pdf.setFont("Helvetica-Oblique", 11)
            pdf.setFillColor(colors.darkgray)
            pdf.drawString(3*cm, y, f"Lien : {cert.lien_passage}")
            y -= 1*cm

        y -= 1*cm

        if y < 4*cm:
            pdf.showPage()
            y = height - 3*cm

    pdf.save()

    return response




def generer_recu_pdf(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recu_{inscription.identifiant}.pdf"'

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()

    elements = []

    # ================= LOGO =================
    logo_path = os.path.join('static/images/logo.png')
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=100, height=50))

    elements.append(Spacer(1, 20))

    # ================= TITRE =================
    elements.append(Paragraph("<b>FICHE D'INSCRIPTION</b>", styles['Title']))
    elements.append(Spacer(1, 20))

    # ================= PHOTO =================
    if inscription.photo:
        photo_path = inscription.photo.path
        if os.path.exists(photo_path):
            elements.append(Image(photo_path, width=100, height=120))
            elements.append(Spacer(1, 20))

    # ================= TABLE =================
    data = [
        ["Identifiant", inscription.identifiant],
        ["Nom", inscription.nom],
        ["Prénom", inscription.prenom],
        ["Email", inscription.email],
        ["Téléphone", inscription.telephone],
        ["Formation", inscription.formation],
        ["Commune", inscription.commune],
        ["Quartier", inscription.quartier],
    ]

    table = Table(data)
    table.setStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ])

    elements.append(table)

    elements.append(Spacer(1, 30))

    # ================= SIGNATURE =================
    elements.append(Paragraph("Signature étudiant ____________________", styles['Normal']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Signature administration ____________________", styles['Normal']))

    doc.build(elements)

    return response