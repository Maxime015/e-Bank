from django.conf import settings
from twilio.rest import Client
import os


# Récupérer les informations depuis settings.py
account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN

client = Client(account_sid, auth_token)

def send_sms(user_code, phone_number, username):
    try:
        message = client.messages.create(
            body=f'Hi! {username}, your user verification code is: {user_code}',
            from_='+15733045812',  # Remplacez par votre numéro Twilio
            to=phone_number
        )
        print(f"Message sent with SID: {message.sid}")  # Affiche l'ID du message pour confirmation
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")  # Gérer les erreurs d'envoi de SMS

# Exemple d'utilisation
# send_sms('123456', '+1234567890', 'User123')  # Appelez la fonction avec le code utilisateur, numéro de téléphone et nom d'utilisateur
