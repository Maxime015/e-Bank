# 💳 Projet Django : Application Bancaire Sécurisée

## 🧩 Description du projet

Ce projet est une application bancaire en ligne développée avec **Django**. Elle permet aux utilisateurs de :

- Créer un compte avec vérification OTP (par e-mail et SMS)
- Se connecter avec ou sans **authentification à deux facteurs (2FA)** via QR Code
- Gérer leurs comptes bancaires (ajout, édition, suppression)
- Effectuer des **transactions financières** (crédit, débit, transferts)
- Réinitialiser leur mot de passe de manière sécurisée
- Recevoir des notifications par e-mail et SMS

---

## 🔐 Fonctionnalités principales

### 🔧 Authentification & Sécurité

- ✅ Inscription utilisateur avec formulaire personnalisé (`RegisterForm`)
- ✅ Envoi d’un **OTP par e-mail** après inscription (vérification obligatoire)
- ✅ Vérification SMS avec formulaire de code
- ✅ Activation de l'utilisateur après validation de l'OTP
- ✅ Authentification classique + **2FA via QR Code & TOTP (Google Authenticator)**
- ✅ Désactivation possible du 2FA
- ✅ Connexion sécurisée avec gestion des erreurs

### 💰 Gestion bancaire

- ✅ Création de comptes bancaires personnalisés
- ✅ Consultation des comptes créés
- ✅ Modification des comptes via formulaire (`EditForm`)
- ✅ Transactions :
  - 💸 **Créditer** un compte
  - 💳 **Débiter** un compte
  - 🔁 **Transférer des fonds** entre comptes
- ✅ Journalisation automatique des transactions (`Transaction.objects.create()`)

### 🆘 Réinitialisation de mot de passe

- ✅ Formulaire de demande de réinitialisation avec e-mail
- ✅ Génération de lien temporaire (valable 10 minutes)
- ✅ Formulaire de définition d’un nouveau mot de passe sécurisé
- ✅ Notification par e-mail du succès de la réinitialisation

---

## 🛠️ Technologies utilisées

- **Python 3** / **Django**
- **Django ORM** (modèles personnalisés)
- **HTML/CSS** pour les templates
- **PyOTP** pour le TOTP 2FA
- **QRCode** pour la génération du QR Code
- **Base64** pour encodage des images QR
- **EmailMessage / send_mail** pour les notifications par e-mail
- **Messages Django** pour les retours utilisateur
- **JsonResponse** pour les opérations AJAX

---

## 📂 Structure du projet

```plaintext
📁 users/
├── views.py       # Logique métier
├── forms.py       # Formulaires personnalisés
├── models.py      # Modèles utilisateur, OTP, comptes, transactions
├── utils.py       # Fonctions utilitaires (SMS, OTP)
├── templates/
│   ├── signup.html
│   ├── login.html
│   ├── profile.html
│   └── emails/
│       ├── verification_email.html
│       ├── password_reset_request.html
│       └── password_reset_success.html
