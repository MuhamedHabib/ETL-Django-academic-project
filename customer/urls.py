from django.urls import path, include
from . import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('customerclick', views.customerclick_view,name='customerclick'),
    #path('customersignup1', views.customer_signup_view,name='customersignup1'),
    #path('customer-dashboard1', views.customer_dashboard_view,name='customer-dashboard1'),
    path('dashboard', views.customer_dashboard_view,name='customer-dashboard'),
    #path('customerlogin1', LoginView.as_view(template_name='backoffice/adminlogin.html'),name='customerlogin1'),
    path('login', LoginView.as_view(template_name='home/sign-in.html'),name='login'),
    path('register', views.customer_signup_view,name='register'),
    path('paypal', include('paypal.standard.ipn.urls')),
    path('profile', views.profile_view,name='profile'),
    path('virtual-reality', views.virtual_reality_view,name='virtual-reality'),
    path('rtl', views.rtl_view,name='rtl'),
    path('billing', views.billing_view,name='billing'),
    path('download-attendance', views.download_attendance,name='download-attendance'),
    path('download-payslip', views.download_payslip,name='download-payslip'),
    path('download-autorization/<int:pk>', views.download_autorization,name='download-autorization'),
    path('apply-policy', views.apply_policy_view,name='apply-policy'),
    path('apply/<int:pk>', views.apply_view,name='apply'),
    path('toggle-email', views.toggle_email_view,name='toggle-email'),
    path('toggle-sms', views.toggle_sms_view,name='toggle-sms'),
    path('toggle-call', views.toggle_call_view,name='toggle-call'),
    path('toggle-whatsapp', views.toggle_whatsapp_view,name='toggle-whatsapp'),
    path('contracts', views.history_view,name='contracts'),
    path('webhook', views.stripe_webhook,name='webhook'),
    path('chatbot', views.chatbot_view,name='chatbot'),
    path('predict', views.predict_view,name='predict'),
    path('delete-contract/<int:pk>', views.delete_contract_view,name='delete-contract'),
    path('delete-card/<int:pk>', views.delete_card_view,name='delete-card'),
    path('delete-car/<int:pk>', views.delete_car_view,name='delete-car'),
    path('delete-question/<int:pk>', views.delete_question_view,name='delete-question'),
    path('checkout/<int:pk>', views.checkout_view,name='checkout'),
    path('coinbase-checkout/<int:pk>', views.coinbase_checkout_view,name='coinbase-checkout'),
    #path('ask-question', views.ask_question_view,name='ask-question'),
    path('question-history', views.question_history_view,name='question-history'),
    path('history', views.history_view, name='history'),

    path(route='course', view=views.movie_recommendation_view, name='recommendations'),

]