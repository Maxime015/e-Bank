from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, Group, Permission 
from django.conf import settings
from django.utils import timezone
import random
from django.contrib.auth.models import User
import uuid
from django.conf import settings
import secrets
from django.contrib.auth import get_user_model
from django_countries.fields import CountryField
from decimal import Decimal


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=64, default='', blank=True)
    mfa_secret = models.CharField(max_length=64, blank=True, null=True)
    mfa_enabled = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.username} ({self.email})"



class OtpToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otps")
    otp_code = models.CharField(max_length=6, default=secrets.token_hex(3))
    otp_created_at = models.DateTimeField(auto_now_add=True)
    otp_expires_at = models.DateTimeField(default=timezone.now() + timezone.timedelta(minutes=5))  # Expiration automatique

    def __str__(self):
        return self.user.username



class Code(models.Model):
    number = models.CharField(max_length=6, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.number = str(random.randint(100000, 999999))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Code {self.number} for {self.user.username}"



class PasswordReset(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"
    
    
    

class CompteBancaire(models.Model):
    TYPE_COMPTE_CHOICES = [
        ('Basic', 'Basic'),
        ('Premium', 'Premium'),
        ('Luxe', 'Luxe'),
    ]
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    profession = models.CharField(max_length=100)
    type_compte = models.CharField(max_length=10, choices=TYPE_COMPTE_CHOICES)
    solde = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pays = CountryField(blank_label='Sélectionnez un pays')
    heure = models.TimeField(auto_now_add=True)  # Défini l'heure automatiquement à la création
    date = models.DateField(auto_now_add=True)  # Défini la date automatiquement à la création
    statut = models.CharField(max_length=100, editable=False)  # Champ non modifiable directement
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gestionnaire")

    def save(self, *args, **kwargs):
        # Mettre à jour le statut en fonction du solde
        if self.solde <= -275000:
            self.statut = "Surendetté"
        elif self.solde < -750:
            self.statut = "recouvrement"
        elif self.solde < 0:
            self.statut = "endetté"
        elif self.solde <= 2500:
            self.statut = "en alerte"
        elif self.solde <= 500:
            self.statut = "très faible"
        elif self.solde <= 7500:
            self.statut = "sur le fil"
        elif self.solde == 0:
            self.statut = "Nul"
        elif self.solde <= 75000:
            self.statut = "solvable"
        elif self.solde <= 150000:
            self.statut = "excédentaire"
        else:
            self.statut = "solvable"  # Par défaut
        
        # Appeler la méthode save parent
        super().save(*args, **kwargs)




    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.type_compte})"
    

    def debiter(self, montant):
        """Débiter le compte du montant spécifié."""
        if montant <= 0:
            raise ValueError("Montant invalide.")
        if montant > self.solde:
            raise ValueError("Fonds insuffisants.")
        self.solde -= montant
        self.save()

    def crediter(self, montant):
        """Créditer le compte du montant spécifié."""
        if montant <= 0:
            raise ValueError("Montant invalide.")
        self.solde += montant
        self.save()
    
    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.type_compte} - Solde: {self.solde} - {self.profession}"

class Transaction(models.Model):
    compte = models.ForeignKey('CompteBancaire', related_name='historique', on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    type_transaction = models.CharField(max_length=50)
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.type_transaction} - {self.montant} - {self.date}"

    @staticmethod
    def calculer_frais(montant, type_compte):
        """Calculer les frais en fonction du type de compte."""
        frais_map = {
            "Basic": Decimal("0.02"),
            "Premium": Decimal("0.03"),
            "Luxe": Decimal("0.05"),
        }
        return montant * frais_map.get(type_compte, Decimal("0"))


    def ajouter_frais(self, compte_id, id_destinataire, montant):
        """Ajouter des frais lors de la transaction entre deux comptes."""
        try:
            compte_source = CompteBancaire.objects.get(id=compte_id)
            compte_destinataire = CompteBancaire.objects.get(id=id_destinataire)

            frais = self.calculer_frais(montant, compte_source.type_compte)
            total_a_debiter = montant + frais

            # Vérifier les fonds avant de débiter
            if total_a_debiter > compte_source.solde:
                raise ValueError("Fonds insuffisants pour la transaction avec frais.")

            # Utilisation de la transaction atomique pour garantir l'intégrité des opérations
            with transaction.atomic():
                compte_source.debiter(total_a_debiter)
                compte_destinataire.crediter(montant)

                # Création des transactions
                Transaction.objects.create(compte=compte_source, montant=total_a_debiter, type_transaction="Débit avec frais")
                Transaction.objects.create(compte=compte_destinataire, montant=montant, type_transaction="Crédit")

            return True

        except CompteBancaire.DoesNotExist:
            raise ValueError("Un ou plusieurs comptes n'ont pas été trouvés.")
        except ValueError as e:
            raise e


#####################################################################################################################################################################################


class Expenses(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    heure = models.TimeField(auto_now_add=True)  # Défini l'heure automatiquement à la création
    date = models.DateField(auto_now_add=True)  # Défini la date automatiquement à la création
    account = models.ForeignKey('CompteBancaire', on_delete=models.CASCADE, related_name='expenses')

    def __str__(self):
        return f"Expenses {self.id} for Budget: {self.account.nom}"
