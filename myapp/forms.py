from django import forms
from .models import Commande
from .models import Preinscription

class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = [
            'quantity', 'payment', 'customer_name', 
            'customer_email', 'customer_phone', 'customer_address',
        ]
        
        labels = {
            'quantity': 'Quantité',
            'payment': 'Mode de paiement',
            'customer_name': 'Nom complet',
            'customer_email': 'Email',
            'customer_phone': 'Téléphone',
            'customer_address': 'Adresse',
        }
        
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Quantité'
            }),
            'payment': forms.Select(attrs={
                'class': 'form- '
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nom complet'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Email'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Téléphone'
            }),
            'customer_address': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Adresse'
            }),
        }
PAYMENT_CHOICES = [
    ('ORANGE', 'Orange Money'),
    ('MTN', 'MTN MoMo'),
    ('WAVE', 'Wave'),
]

payment = forms.ChoiceField(
    choices=PAYMENT_CHOICES,
    widget=forms.Select(attrs={'class': 'form-select'})
)


# class OrderForm(forms.ModelForm):
#     class Meta:
#         model = Order
#         fields = [
#             'customer_name',
#             'customer_phone',
#             'customer_email',
#             'customer_address',
#             'payment',
#         ]

# class PreinscriptionForm(forms.ModelForm):
#     class Meta:
#         model = Preinscription
#         fields = ['nom', 'prenom', 'email', 'telephone', 'date_naissance', 'formation',  'commune', 'quartier','message']
#         widgets = {
#             'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'nom': forms.TextInput(attrs={'class': 'form-control'}),
#             'prenom': forms.TextInput(attrs={'class': 'form-control'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control'}),
#             'telephone': forms.TextInput(attrs={'class': 'form-control'}),
#             'formation': forms.TextInput(attrs={'class': 'form-control'}),
#             'commune': forms.TextInput(attrs={'class': 'form-control'}),
#             'quartier': forms.TextInput(attrs={'class': 'form-control'}),
#             'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
#         }

class PreinscriptionForm(forms.ModelForm):
    class Meta:
        model = Preinscription
        fields = [
            'nom', 'prenom', 'email', 'telephone', 'date_naissance', 
            'formation', 'commune', 'quartier', 'message',

            # ✅ Nouveaux champs
            'nationalite',
            'etablissement_origine',
            'diplome',
            'annee_obtention',
            'nom_pere',
            'telephone_pere',
            'adresse_parents',
            'piece_recto',
            'piece_verso',
        ]

        widgets = {
            # ✅ Informations personnelles
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'formation': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),

            # ✅ Informations académiques
            'nationalite': forms.TextInput(attrs={'class': 'form-control'}),
            'etablissement_origine': forms.TextInput(attrs={'class': 'form-control'}),
            'diplome': forms.TextInput(attrs={'class': 'form-control'}),
            'annee_obtention': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1900,
                'max': 2100
            }),

            # ✅ Informations parentales
            'nom_pere': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_pere': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse_parents': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),

            # ✅ Upload fichiers
            'piece_recto': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'piece_verso': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }