from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import now
from django.core.mail import send_mail, EmailMessage
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from .forms import RegisterForm, CodeForm, CompteBancaireForm , EditForm
from .models import *
from django.http import JsonResponse
from .utils import send_sms
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
import secrets
from django.http import HttpResponse
from django.core.files.storage import (
    default_storage,
)  # optionnel, pour gérer le stockage des
import io
import base64
import pyotp
import qrcode
import json
from decimal import Decimal



def send_verification_email(user, otp):
    subject = "Your SMS Code"
    message = f"Hello {user.username}, your email verification code is: {otp.otp_code}"
    sender = "maximeananivi@gmail.com"
    receiver = [user.email]

    try:
        send_mail(subject, message, sender, receiver, fail_silently=False)
    except Exception as e:
        # Log or print the exception message for debugging (optional)
        print(f"Failed to send email: {e}")


def bank(request):
    comptes = CompteBancaire.objects.all()  # Récupérer tous les comptes
    if request.method == 'POST':
        form = CompteBancaireForm(request.POST)  # Correction du nom du formulaire
        if form.is_valid():
            compte = form.save(commit=False)  # Ne sauvegarde pas immédiatement dans la base de données
            compte.user = request.user  # Associe l'utilisateur connecté
            compte.save()  # Sauvegarde dans la base de données
            messages.success(request, 'Compte ajouté avec succès')
            return redirect('Tab')
    else:
        form = CompteBancaireForm()  # Formulaire vide pour les GET

    # Contexte unique pour la vue
    context = {
        'comptes': comptes,  # Liste des comptes
        'form': form,  # Formulaire
    }
    return render(request, "bank.html", context)





def update_account(request, account_id): 
    compte = get_object_or_404(CompteBancaire, id=account_id)
    if request.method == 'POST':
        form = EditForm(request.POST, instance=compte)
        if form.is_valid():
            form.save()
            messages.success(request, 'Compte mis à jour avec succès.')
            return redirect('Tab')  # Remplacez 'Tab' par le nom de votre vue principale
    else:
        form = EditForm(instance=compte)
    
    # Inclure le compte dans le contexte
    return render(request, 'update_account.html', {'form': form, 'compte': compte})



@csrf_protect
def signup(request):
    form = RegisterForm()
    if request.method == "POST":
        # Inclure `request.FILES` pour capturer l'image de profil
        form = RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            new_user = form.save()

            # Générer un nouvel OTP
            otp = OtpToken.objects.create(user=new_user)
            # Envoyer le code par email
            send_verification_email(new_user, otp)

            mail_subject = "Verify your email with OTP CODE"
            message = render_to_string(
                "emails/verification_email.html",
                {
                    "new_user": new_user,
                    "otp": otp,
                },
            )
            user_email = request.POST.get("email")
            email = EmailMessage(mail_subject, message, to=[user_email])
            email.content_subtype = "html"
            email.send()    

            print(message) 
            print(otp)

            messages.success(request, "Account created! An OTP has been sent to your phone and email !")
            return redirect("verify_sms", username=new_user.username)
        else:
            messages.error(
                request, "Failed to create account. Please check the form for errors."
            )

    context = {"form": form}
    return render(request, "signup.html", context)




def verify_email(request, username):
    user = get_object_or_404(get_user_model(), username=username)
    user_otp = OtpToken.objects.filter(user=user).last()

    if request.method == "POST":
        otp_code = request.POST.get("otp_code", "")
        if user_otp and user_otp.otp_code == otp_code:
            if user_otp.otp_expires_at > timezone.now():
                user.is_active = True
                user.save()
                
                # Spécifiez explicitement le backend pour éviter l'erreur ValueError
                backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user, backend=backend)
                
                messages.success(
                    request, "Account activated successfully! You can now log in."
                )
                return redirect("signin")
            else:
                messages.warning(
                    request, "The OTP has expired, please request a new one."
                )
                return redirect("resend_otp")
        else:
            messages.warning(request, "Invalid OTP entered, please try again.")
            return redirect("verify_email", username=username)

    return render(request, "verify_token.html")




def resend_otp(request):
    if request.method == 'POST':
        user_email = request.POST.get("otp_email")
        
        if get_user_model().objects.filter(email=user_email).exists():
            user = get_user_model().objects.get(email=user_email)
            otp = OtpToken.objects.create(user=user, otp_expires_at=timezone.now() + timezone.timedelta(minutes=10))
            
            # Préparation et envoi de l'email
            current_site = get_current_site(request)
            mail_subject = "Verify your email with new OTP CODE"
            message = render_to_string("emails/resend_otp.html", {
                "user": user,
                "otp": otp,
                "domain": current_site.domain,
            })

            email = EmailMessage(mail_subject, message, to=[user_email])
            email.content_subtype = "html"
            email.send()
            
            messages.success(request, "A new OTP has been sent to your email address")
            return redirect("verify_email", username=user.username)  # Utilisation du nom correct

        else:
            messages.warning(request, "This email doesn't exist in the database")
            return redirect("resend-otp")
        
    context = {}
    return render(request, "resend_otp.html", context)




def signin(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                if user.mfa_enabled:
                    return render(request, "otp_verify.html", {"user_id": user.id})
                else:
                    login(request, user)
                    messages.success(request, f"Hi {user.username}, you are now logged in.")
                    return redirect("profile")
            else:
                messages.warning(
                    request, "Your account is not activated. Please verify your email."
                )
                return redirect("verify_email", username=user.username)
        else:
            messages.warning(request, "Invalid credentials. Please try again.")
            return redirect("signin")

    return render(request, "login.html")



def verify_sms(request, username):
    user = get_object_or_404(get_user_model(), username=username)
    user_code = Code.objects.filter(user=user).last()

    if request.method == "GET" and user_code:
        try:
            # Envoyer le code SMS
            send_sms(user_code.number, user.phone_number, user.username)
            print(user_code)
            print(user_code.number)
        except Exception as e:
            # Si l'envoi de SMS échoue, envoyer un e-mail
            send_verification_email(user, user_code)

            current_site = get_current_site(request)
            mail_subject = "Verify your email with OTP CODE"
            message = render_to_string(
                "emails/verification_email.html",
                {
                    "user": user,  # Pass the user object
                    "user_code": user_code,  # Pass the OTP object
                },
            )
            to_email = form.cleaned_data.get("email")
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.content_subtype = "html"
            email.send()

            messages.warning(
                request, "Failed to send SMS, so we sent the code via email."
            )

    form = CodeForm()
    if request.method == "POST":
        form = CodeForm(request.POST)
        if form.is_valid():
            if user_code and user_code.number == form.cleaned_data["number"]:
                messages.success(
                    request, "Good! Now activate your account with OTP Code."
                )
                return redirect("verify_email", username=username)
            else:
                messages.warning(request, "Invalid SMS code entered, please try again.")
                return redirect("verify_sms", username=username)

    context = {"form": form}
    return render(request, "verify_sms.html", context)



def LogoutView(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect("signin")



def ForgotPassword(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = CustomUser.objects.get(email=email)

            # Create a password reset object
            new_password_reset = PasswordReset(user=user)
            new_password_reset.save()

            # Generate the password reset URL
            password_reset_url = reverse(
                "reset-password", kwargs={"reset_id": new_password_reset.reset_id}
            )

            full_password_reset_url = (
                f"{request.scheme}://{request.get_host()}{password_reset_url}"
            )

            # Create email body
            email_body = f"Reset your password using the link below:\n\n{full_password_reset_url}"

            # Send the plain text email
            email_message = EmailMessage(
                "Reset your password",  # Email subject
                email_body,
                settings.EMAIL_HOST_USER,  # Email sender
                [email],  # Email receiver
            )
            email_message.fail_silently = True
            email_message.send()

            # Prepare the HTML email
            current_site = get_current_site(request)
            mail_subject = "Reset your password"
            message = render_to_string(
                "emails/password_reset_request.html",
                {
                    "user": user,  # Corrected this line
                    "full_password_reset_url": full_password_reset_url,
                },
            )
            email = EmailMessage(
                mail_subject, message, to=[email]
            )  # Use the same email variable
            email.content_subtype = "html"
            email.send()

            return redirect("password-reset-sent", reset_id=new_password_reset.reset_id)

        except CustomUser.DoesNotExist:
            messages.error(request, f"No user with email '{email}' found")
            return redirect("forgot-password")

    return render(request, "forgot_password.html")




def PasswordResetSent(request, reset_id):
    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, "password_reset_sent.html")

    else:
        # redirection vers la page de réinitialisation si l'ID est invalide
        messages.error(request, "Invalid reset id")
        return redirect("forgot-password")




def ResetPassword(request, reset_id):
    # Supprimer les anciennes demandes de réinitialisation expirées
    PasswordReset.objects.filter(
        created_when__lte=timezone.now() - timezone.timedelta(minutes=10)
    ).delete()

    try:
        # Chercher la demande de réinitialisation par son reset_id
        password_reset_request = PasswordReset.objects.get(reset_id=reset_id)

        if request.method == "POST":
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")
            passwords_have_error = False

            # Vérifier que les mots de passe correspondent
            if password != confirm_password:
                passwords_have_error = True
                messages.error(request, "Passwords do not match")

            # Vérifier que le mot de passe est suffisamment long
            if len(password) < 8:
                passwords_have_error = True
                messages.error(request, "Password must be at least 8 characters long")

            # Vérifier si le lien de réinitialisation a expiré
            expiration_time = password_reset_request.created_when + timezone.timedelta(
                minutes=10
            )
            if timezone.now() > expiration_time:
                passwords_have_error = True
                messages.error(request, "Reset link has expired")
                password_reset_request.delete()

            if not passwords_have_error:
                # Si tout est correct, réinitialiser le mot de passe de l'utilisateur
                user = password_reset_request.user
                user.set_password(password)
                user.save()

                # Supprimer la demande de réinitialisation après usage
                password_reset_request.delete()

                messages.success(
                    request, "Password reset successfully. You may now log in."
                )

                # Envoyer un email de confirmation de réinitialisation
                current_site = get_current_site(request)
                mail_subject = "PASSWORD RESET SUCCESSFUL"
                message = render_to_string(
                    "emails/password_reset_success.html",
                    {
                        "user": user,
                        "domain": current_site.domain,
                    },
                )

                # Utilisation de l'e-mail de l'utilisateur associé à la demande de réinitialisation
                user_email = user.email
                email = EmailMessage(mail_subject, message, to=[user_email])
                email.content_subtype = "html"
                email.send()

                return redirect("signin")

    except PasswordReset.DoesNotExist:
        # Si l'identifiant de réinitialisation est invalide
        messages.error(request, "Invalid reset ID")
        return redirect("forgot-password")

    return render(request, "reset_password.html")



########################################################################################################################

CustomUser = get_user_model()


def verify_2fa_otp(user, otp):
    totp = pyotp.TOTP(user.mfa_secret)
    if totp.verify(otp):
        user.mfa_enabled = True
        user.save()
        return True
    return False




def profile_view(request):
    user = request.user
    if not user.mfa_secret:
        user.mfa_secret = pyotp.random_base32(length=64)
        user.save()

    otp_uri = pyotp.totp.TOTP(user.mfa_secret).provisioning_uri(
        name=user.email, issuer_name="e-Bank"
    )

    qr = qrcode.make(otp_uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")

    buffer.seek(0)
    qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")

    qr_code_data_uri = f"data:image/png;base64,{qr_code}"
    return render(request, "profile.html", {"qrcode": qr_code_data_uri})



from django.contrib.auth import login, get_backends
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser  # Replace with your actual model

def verify_mfa(request):
    if request.method == "POST":
        otp = request.POST.get("otp_code")
        user_id = request.POST.get("user_id")
        
        if not user_id:
            messages.error(request, "Invalid user ID. Please try again.")
            return render(request, "otp_verify.html", {"user_id": user_id})

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found. Please try again.")
            return render(request, "otp_verify.html", {"user_id": user_id})

        if verify_2fa_otp(user, otp):
            if request.user.is_authenticated:
                messages.success(request, "2FA enabled successfully!")
                return redirect("profile")

            # Ensure the backend attribute is set for the user
            backends = get_backends()
            for backend in backends:
                if hasattr(backend, "get_user") and user.is_authenticated:
                    user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
                    break

            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("profile")
        else:
            messages.error(request, "Invalid OTP code. Please try again.")
            return render(request, "otp_verify.html", {"user_id": user_id})

    return render(request, "otp_verify.html", {"user_id": None})





def disable_2fa(request):
    user = request.user
    if user.mfa_enabled:
        user.mfa_enabled = False
        user.save()
        messages.success(request, "Two-Factor Authentication has been disabled.")
        return redirect("profile")
    else:
        messages.info(request, "2FA is already disabled.")
    return redirect("profile")


########################################################################################################################

from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt


@login_required
@csrf_exempt  # Assurez-vous d'avoir configuré CSRF correctement si nécessaire
def crediter(request, compte_id):
    if request.method == 'POST':
        try:
            montant = Decimal(request.POST.get('montant', '0'))
            if montant <= 0:
                return JsonResponse({'status': 'error', 'message': 'Montant invalide.'}, status=400)

            compte = get_object_or_404(CompteBancaire, id=compte_id)
            compte.crediter(montant)
            Transaction.objects.create(compte=compte, montant=montant, type_transaction='Crédit')

            return JsonResponse({'status': 'success', 'new_balance': str(compte.solde)})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Requête non autorisée.'}, status=405)




@login_required
def debiter(request, compte_id, montant):
    # Convertir 'montant' de string à Decimal
    montant = Decimal(montant)
    
    compte = get_object_or_404(CompteBancaire, id=compte_id)
    if compte.solde >= montant:
        compte.debiter(montant)  # Débiter le compte
        Transaction.objects.create(compte=compte, montant=montant, type_transaction='Débit')
        return JsonResponse({'status': 'success', 'new_balance': compte.solde})
    else:
        return JsonResponse({'status': 'error', 'message': 'Fonds insuffisants'})




from django.http import JsonResponse
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt


@login_required
@csrf_exempt
def transfert_fonds(request, compte_id):
    try:
        compte_source = CompteBancaire.objects.get(id=compte_id)

        if request.method == "POST":
            data = json.loads(request.body)
            montant = Decimal(data.get('montant'))
            id_destinataire = int(data.get('id_destinataire'))
            compte_destinataire = CompteBancaire.objects.get(id=id_destinataire)

            frais = Transaction.calculer_frais(montant, compte_source.type_compte)
            total_a_debiter = montant + frais

            if compte_source.solde >= total_a_debiter:
                with transaction.atomic():
                    compte_source.debiter(total_a_debiter)
                    compte_destinataire.crediter(montant)

                    Transaction.objects.create(compte=compte_source, montant=total_a_debiter, type_transaction="Débit avec frais")
                    Transaction.objects.create(compte=compte_destinataire, montant=montant, type_transaction="Crédit")

                return JsonResponse({"success": True, "message": f"Transfert de {montant} $ effectué avec succès."})
            else:
                return JsonResponse({"success": False, "message": "Fonds insuffisants pour effectuer le transfert."})

    except CompteBancaire.DoesNotExist:
        return JsonResponse({"success": False, "message": "Compte source ou destinataire introuvable."})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


@login_required
def supprimer_compte(request, compte_id):
    compte = get_object_or_404(CompteBancaire, id=compte_id)
    compte.delete()
    return redirect('Tab')



from openpyxl import Workbook
from django.http import HttpResponse
from datetime import datetime


@login_required
def export_historique(request):
    comptes = CompteBancaire.objects.all()
    transactions = []

    # Préparation des données
    for compte in comptes:
        for trans in compte.historique.all():  # Assurez-vous que `historique` est une relation correcte
            # Retirer la timezone et formater la date et l'heure
            if isinstance(trans.date, datetime):
                trans_date = trans.date.replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')  # Format: YYYY-MM-DD HH:MM:SS
            else:
                trans_date = trans.date

            transactions.append([
                compte.id,
                compte.nom,
                compte.prenom,
                compte.profession,
                compte.type_compte,
                trans.type_transaction,
                trans.montant,
                trans_date  # Utilisation de la date et heure sans timezone
            ])

    # Création du fichier Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Historique des Transactions"

    # Ajout de l'en-tête
    headers = ['ID', 'Nom', 'Prénom', 'Profession', 'Type de Compte', 'Type de Transaction', 'Montant', 'Date et Heure']
    ws.append(headers)

    # Ajout des données
    for transaction in transactions:
        ws.append(transaction)

    # Réponse HTTP avec le fichier Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="historique_transactions.xlsx"'
    wb.save(response)
    return response



########################################################################################################################




@login_required
def Tab(request):
    comptes = CompteBancaire.objects.all()  # Récupérer tous les comptes

    # Contexte unique pour la vue
    context = {
        'comptes': comptes,  # Liste des comptes
    }
    return render(request, "Tab.html", context)



@login_required
def graphe2(request):
    comptes = CompteBancaire.objects.all()
    labels = [compte.nom for compte in comptes]
    data = [float(compte.solde) for compte in comptes]  # Convertir Decimal en float

    context = {
        'labels': json.dumps(labels),  # Convertir en JSON
        'data': json.dumps(data),      # Convertir en JSON
    }
    return render(request, "grapho.html", context)



#####################################################################################################################################################################################
from decimal import Decimal, InvalidOperation
from django.db.models import Sum, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import CompteBancaire, Expenses  # Importez vos modèles

@transaction.atomic
@login_required
def budget_detail(request, account_id):
    # Récupération du compte bancaire
    account = get_object_or_404(CompteBancaire, id=account_id, user=request.user)
    expenses = account.expenses.all()
   

    # Calcul des données financières
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    solde = Decimal(account.solde)
    reste = solde - total_expenses

    # Calcul du pourcentage utilisé (évite division par zéro)
    progress_percentage = (total_expenses / solde * 100) if solde > 0 else 0
    progress_percentage = min(round(progress_percentage, 2), 100)

    # Compte des dépenses
    nbre_expenses = expenses.count()

    # Calcul du nombre de comptes où le solde est égal au total des dépenses
    comptes_egaux = CompteBancaire.objects.filter(user=request.user).annotate(
        total_expenses=Sum('expenses__amount')
    ).filter(solde=F('total_expenses')).count()

    if request.method == "POST":
        # Gestion des données de la requête
        amount = request.POST.get('amount')
        description = request.POST.get('description', '').strip()

        try:
            amount = Decimal(amount)

            if amount <= 0:
                messages.warning(request, "Le montant doit être supérieur à 0 !")
            elif total_expenses + amount > solde:
                messages.error(request, "Le montant de la dépense dépasse ou est égal à votre solde bancaire !")
            else:
                # Vérification de l'existence de la dépense
                expense_exists = Expenses.objects.filter(
                    amount=amount, description=description, account=account
                ).exists()

                if not expense_exists:
                    Expenses.objects.create(amount=amount, description=description, account=account)

                    # Recalcul des données après ajout
                    total_expenses = account.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                    reste = solde - total_expenses
                    progress_percentage = (total_expenses / solde * 100) if solde > 0 else 0
                    progress_percentage = min(round(progress_percentage, 2), 100)

                    messages.success(request, f"Dépense ajoutée avec succès. Progression : {progress_percentage}%. Reste : {reste} €. Total des dépenses : {total_expenses} €.")
                    return JsonResponse({
                        'success': "Dépense ajoutée avec succès.",
                        'progress_percentage': progress_percentage,
                        'reste': str(reste),
                        'total_expenses': str(total_expenses),
                    })
        except (ValueError, InvalidOperation):
            messages.error(request, "Format de montant invalide. Veuillez entrer un nombre valide !")

    # Contexte à transmettre au template pour une requête normale (non AJAX)
    context = {
        'account': account,
        'expenses': expenses,
        'total_expenses': total_expenses,
        'solde': solde,
        'reste': reste,
        'progress_percentage': progress_percentage,
        'nbre_expenses': nbre_expenses,
        'comptes_egaux': comptes_egaux,
    }

    return render(request, 'budget_detail.html', context)





@login_required
def supprimer_expense(request, expense_id):
    expense = get_object_or_404(Expenses, id=expense_id)  # Assurez-vous que c'est bien `Expenses` et non `Expense`
    expense.delete()
    return redirect('budget_detail', account_id=expense.account.id)


@login_required
def dashboard(request):
    budgets = CompteBancaire.objects.all()
    budgets_data = []
    for account in budgets:
        expenses = account.expenses.all()
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        solde = Decimal(account.solde)
        reste = solde - total_expenses
        progress_percentage = (total_expenses / solde * 100) if solde > 0 else 0
        progress_percentage = min(round(progress_percentage, 2), 100)
        nbre_expenses = expenses.count()

        budgets_data.append({
            'account': account,
            'nbre_expenses': nbre_expenses,
            'total_expenses': total_expenses,
            'reste': reste,
            'progress_percentage': progress_percentage,
        })

    return render(request, 'dashboard.html', {'budgets': budgets_data})


import json
from django.shortcuts import render
from django.db.models import Sum
from decimal import Decimal

@login_required
def graphe3(request):
    budgets = CompteBancaire.objects.all()
    budgets_data = []
    for account in budgets:
        expenses = account.expenses.all()
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        solde = Decimal(account.solde)

        budgets_data.append({
            'name': account.nom,  # Utiliser le champ correct ici
            'total_expenses': float(total_expenses),
            'solde': float(solde),
        })

    # Convertir budgets_data en JSON
    budgets_data_json = json.dumps(budgets_data)

    return render(request, 'graphe3.html', {'budgets_data_json': budgets_data_json})





from django.db.models import Sum, F

@login_required
def graphe(request):
    comptes = CompteBancaire.objects.all()

    # Préparer les données pour le graphique
    labels = [compte.nom for compte in comptes]
    data = [float(compte.solde) for compte in comptes]  # Convertir Decimal en float

    # Calcul des statistiques
    solvable_accounts = [compte for compte in comptes if compte.solde > 0]
    nbre_solvable_accounts = len(solvable_accounts)

    decrease_accounts = [compte for compte in comptes if compte.solde < 0]
    nbre_decrease_accounts = len(decrease_accounts)

    nbre_accounts = len(comptes)

    # Calcul du nombre de comptes où le solde est égal au total des dépenses
    comptes_egaux = comptes.annotate(
        total_expenses=Sum('expenses__amount')
    ).filter(solde=F('total_expenses')).count()

    # Contexte pour le template
    context = {
        'labels': json.dumps(labels),  # Convertir en JSON
        'data': json.dumps(data),      # Convertir en JSON
        'nbre_solvable_accounts': nbre_solvable_accounts,
        'nbre_decrease_accounts': nbre_decrease_accounts,
        'nbre_accounts': nbre_accounts,
        'comptes_egaux': comptes_egaux,  # Ajout de la variable au contexte
    }
    return render(request, "graphe.html", context)



from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal
import json
from django.shortcuts import render

@login_required
def graphe4(request):
    budgets = CompteBancaire.objects.all()

    labels = []
    data = []

    for account in budgets:
        expenses = account.expenses.all()
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        labels.append(account.nom)  # Remplacer `nom` par le bon champ du modèle
        data.append(float(total_expenses))

    # Passer les labels et les data au contexte
    return render(request, 'graphe4.html', {
        'labels': json.dumps(labels),
        'data': json.dumps(data),
    })




@login_required
def graphe5(request):
    # Récupérer les comptes bancaires liés à l'utilisateur connecté
    budgets = CompteBancaire.objects.all()

    budgets_data = []
    for account in budgets:
        # Calcul des dépenses totales associées au compte
        expenses = account.expenses.all()
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        solde = Decimal(account.solde)
        reste = solde - total_expenses

        budgets_data.append({
            'name': account.nom,  # Assurez-vous que 'nom' est bien le champ correct dans votre modèle
            'total_expenses': float(total_expenses),
            'solde': float(solde),
            'reste': float(reste),  # Conversion en float pour JSON
        })

    # Conversion des données en JSON
    budgets_data_json = json.dumps(budgets_data)

    # Rendu de la page avec les données JSON injectées
    return render(request, 'graphe5.html', {'budgets_data_json': budgets_data_json})






@login_required
def graphe6(request):
    # Récupérer les comptes bancaires liés à l'utilisateur connecté
    budgets = CompteBancaire.objects.all()

    budgets_data = []
    for account in budgets:
        # Calcul des dépenses totales associées au compte
        expenses = account.expenses.all()
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        solde = Decimal(account.solde)
        reste = solde - total_expenses

        budgets_data.append({
            'name': account.nom,  # Assurez-vous que 'nom' est bien le champ correct dans votre modèle
            'total_expenses': float(total_expenses),
            'solde': float(solde),
            'reste': float(reste),  # Conversion en float pour JSON
        })

    # Conversion des données en JSON
    budgets_data_json = json.dumps(budgets_data)

    # Rendu de la page avec les données JSON injectées
    return render(request, 'graphe6.html', {'budgets_data_json': budgets_data_json})




@login_required
def transactions(request):
    transactions = Transaction.objects.all()  # Récupérer toutes transactions
    # Contexte unique pour la vue
    context = {
        'transactions': transactions,  # Liste des comptes
    }
    return render(request, "story.html", context)