# otp_app/urls.py

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path("", views.signin, name="signin"),
    path('bank/', views.bank, name='bank'),
    path('graphe/', views.graphe, name='graphe'),
    path('graphe2/', views.graphe2, name='graphe2'),
    path('signup/', views.signup, name='signup'),
    path('verify-email/<str:username>/', views.verify_email, name='verify_email'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('verify-sms/<str:username>/', views.verify_sms, name='verify_sms'), 
    path('logout/', views.LogoutView, name='logout'),
    path('forgot-password/', views.ForgotPassword, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.PasswordResetSent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.ResetPassword, name='reset-password'),
    path('profile/', views.profile_view, name='profile'),
    path('verify_mfa/', views.verify_mfa, name='verify_mfa'),
    path('disable-2fa/', views.disable_2fa, name='disable_2fa'),   
    path('Tab/', views.Tab, name='Tab'),
    path('crediter/<int:compte_id>/', views.crediter, name='crediter'),
    path('debiter/<int:compte_id>/<str:montant>/', views.debiter, name='debiter'),
    path('Tab/<int:compte_id>/', views.transfert_fonds, name='Transfert'),
    path('supprimer-compte/<int:compte_id>/', views.supprimer_compte, name='supprimer_compte'),
    path('update/<int:account_id>/', views.update_account, name='update'),
    path('export/historique/', views.export_historique, name='export_historique'),
    path('budget_detail/<int:account_id>/', views.budget_detail, name='budget_detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('supprimer-expense/<int:expense_id>/', views.supprimer_expense, name='supprimer_expense'),
    path('graphe3/', views.graphe3, name='graphe3'),
    path('graphe4/', views.graphe4, name='graphe4'),
    path('graphe5/', views.graphe5, name='graphe5'),
    path('graphe6/', views.graphe6, name='graphe6'),
    path('transactions/', views.transactions, name='transactions'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

