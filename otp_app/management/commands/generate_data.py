import os
import random
from decimal import Decimal
from faker import Faker
import django
from django.core.management.base import BaseCommand
from django.db import transaction
from otp_app.models import CustomUser, CompteBancaire, Transaction, Expenses

# Initialiser l'environnement Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "otp_validation.settings")
django.setup()

# Initialisation de Faker
fake = Faker()
BATCH_SIZE = 1000

def generate_unique_username(base_username):
    """Générer un nom d'utilisateur unique."""
    username = base_username
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base_username}{random.randint(1, 10000)}"
    return username

def create_users(n=1000):
    """Créer des utilisateurs uniques."""
    users = []
    for _ in range(n):
        username = generate_unique_username(fake.user_name())
        users.append(CustomUser(
            username=username,
            email=fake.unique.email(),
            phone_number=fake.phone_number(),
            password=fake.password()  # Vous pouvez hasher ce mot de passe si nécessaire
        ))

    CustomUser.objects.bulk_create(users, batch_size=BATCH_SIZE)
    print(f"✅ {n} utilisateurs créés.")

def create_accounts(n=5000):
    """Créer des comptes bancaires avec des utilisateurs valides."""
    users = CustomUser.objects.all()
    if not users.exists():
        print("❌ Aucun utilisateur trouvé.")
        return

    accounts = []
    for _ in range(n):
        user = random.choice(users)
        accounts.append(CompteBancaire(
            nom=fake.last_name(),
            prenom=fake.first_name(),
            profession=fake.job(),
            type_compte=random.choice(['Basic', 'Premium', 'Luxe']),
            solde=Decimal(random.uniform(-500000, 500000)).quantize(Decimal('0.01')),
            pays=fake.country_code(),
            user=user
        ))

    CompteBancaire.objects.bulk_create(accounts, batch_size=BATCH_SIZE)
    print(f"✅ {n} comptes bancaires créés.")

def create_transactions(n=10000):
    """Créer des transactions associées à des comptes bancaires existants."""
    accounts = CompteBancaire.objects.all()
    if not accounts.exists():
        print("❌ Aucun compte trouvé.")
        return

    transactions = []
    for _ in range(n):
        account = random.choice(accounts)
        type_transaction = random.choice(["Débit", "Crédit"])
        montant = Decimal(random.uniform(500, 50000)).quantize(Decimal("0.01"))

        if type_transaction == "Débit" and account.solde < montant:
            continue

        if type_transaction == "Débit":
            account.solde -= montant
        else:
            account.solde += montant

        transactions.append(Transaction(
            compte=account,
            montant=montant,
            type_transaction=type_transaction
        ))

    Transaction.objects.bulk_create(transactions, batch_size=BATCH_SIZE)
    print(f"✅ {n} transactions créées.")

def create_expenses(n=5000):
    """Créer des dépenses associées à des comptes bancaires existants."""
    accounts = CompteBancaire.objects.filter(solde__gt=0)
    if not accounts.exists():
        print("❌ Aucun compte trouvé avec des fonds suffisants.")
        return

    expenses = []
    for _ in range(n):
        account = random.choice(accounts)
        max_amount = min(Decimal("200000.00"), account.solde)
        if max_amount <= Decimal("5000.00"):
            continue

        amount = Decimal(random.uniform(5000, float(max_amount))).quantize(Decimal("0.01"))
        account.solde -= amount
        expenses.append(Expenses(
            amount=amount,
            description=fake.sentence(),
            account=account
        ))

    Expenses.objects.bulk_create(expenses, batch_size=BATCH_SIZE)
    print(f"✅ {len(expenses)} dépenses créées.")

class Command(BaseCommand):
    help = "Génère des données massives aléatoires pour les tests."

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=1000, help="Nombre d'utilisateurs à générer.")
        parser.add_argument('--accounts', type=int, default=5000, help="Nombre de comptes bancaires à générer.")
        parser.add_argument('--transactions', type=int, default=10000, help="Nombre de transactions à générer.")
        parser.add_argument('--expenses', type=int, default=5000, help="Nombre de dépenses à générer.")

    def handle(self, *args, **options):
        print("🔄 Début de la génération des données...")

        with transaction.atomic():
            create_users(options['users'])
            if CustomUser.objects.exists():
                create_accounts(options['accounts'])

            if CompteBancaire.objects.exists():
                create_transactions(options['transactions'])
                create_expenses(options['expenses'])

        print("✅ Génération des données terminée.")
