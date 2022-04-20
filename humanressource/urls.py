
from django.contrib import admin
from rest_framework import routers
from django.urls import path
from backoffice import views
from django.contrib.auth.views import LogoutView,LoginView
from django.urls import path,include

########Serialization des donnees:
rpolicy=routers.DefaultRouter()
rpolicy.register('',views.policy_list)

ruser=routers.DefaultRouter()
ruser.register('',views.user_list)
########Serialization des donnees:
rpolicyRecord=routers.DefaultRouter()
rpolicyRecord.register('',views.policyRecord_list)

rcategory=routers.DefaultRouter()
rcategory.register('',views.category_list)

########Serialization des donnees:
rquestion=routers.DefaultRouter()
rquestion.register('',views.question_list)

rpayment=routers.DefaultRouter()
rpayment.register('',views.payment_list)

urlpatterns = [
    path('admin/', admin.site.urls),


    path('customer/',include('customer.urls')),
    #path('',views.home_view,name=''),
    path('logout', LogoutView.as_view(template_name='index.html',next_page=""),name='logout'),
    path('aboutus', views.aboutus_view),
    path('contactus', views.contactus_view),
    path('afterlogin', views.afterlogin_view,name='afterlogin'),
    path('', views.landing_view,name=''),
    path('presentation', views.presentation_view,name='presentation'),
    
    #path('adminlogin', LoginView.as_view(template_name='backoffice/adminlogin.html'),name='adminlogin'),
    path('adminlogin', LoginView.as_view(template_name='backoffice/../templates/backoffice/login.html'), name='adminlogin'),
    path('admin-dashboard', views.admin_dashboard_view,name='admin-dashboard'),

    path('admin-view-customer', views.admin_view_customer_view,name='admin-view-customer'),
    path('update-customer/<int:pk>', views.update_customer_view,name='update-customer'),
    path('delete-customer/<int:pk>', views.delete_customer_view,name='delete-customer'),

    path('admin-category', views.admin_category_view,name='admin-category'),
    path('admin-view-category', views.admin_view_category_view,name='admin-view-category'),
    path('admin-update-category', views.admin_update_category_view,name='admin-update-category'),
    path('update-category/<int:pk>', views.update_category_view,name='update-category'),
    path('admin-add-category', views.admin_add_category_view,name='admin-add-category'),
    path('admin-delete-category', views.admin_delete_category_view,name='admin-delete-category'),
    path('delete-category/<int:pk>', views.delete_category_view,name='delete-category'),


    path('admin-policy', views.admin_policy_view,name='admin-policy'),
    path('admin-add-policy', views.admin_add_policy_view,name='admin-add-policy'),
    path('admin-view-policy', views.admin_view_policy_view,name='admin-view-policy'),
    path('admin-update-policy', views.admin_update_policy_view,name='admin-update-policy'),
    path('update-policy/<int:pk>', views.update_policy_view,name='update-policy'),
    path('admin-delete-policy', views.admin_delete_policy_view,name='admin-delete-policy'),
    path('delete-policy/<int:pk>', views.delete_policy_view,name='delete-policy'),

    path('admin-view-policy-holder', views.admin_view_policy_holder_view,name='admin-view-policy-holder'),
    path('admin-view-approved-policy-holder', views.admin_view_approved_policy_holder_view,name='admin-view-approved-policy-holder'),
    path('admin-view-disapproved-policy-holder', views.admin_view_disapproved_policy_holder_view,name='admin-view-disapproved-policy-holder'),
    path('admin-view-waiting-policy-holder', views.admin_view_waiting_policy_holder_view,name='admin-view-waiting-policy-holder'),
    path('approve-request/<int:pk>', views.approve_request_view,name='approve-request'),
    path('reject-request/<int:pk>', views.disapprove_request_view,name='reject-request'),

    path('admin-question', views.admin_question_view,name='admin-question'),
    path('update-question/<int:pk>', views.update_question_view,name='update-question'),
    path('chart/filter-options/', views.get_filter_options, name='chart-filter-options'),

    path('chart/spend-per-customer/<int:year>/', views.spend_per_customer_chart, name='chart-spend-per-customer'),

    path('statistics/', views.statistics_view, name='shop-statistics'),

    path('chart/sales/<int:year>/', views.get_sales_chart, name='chart-sales'),
#    path('chart/payment-success/<int:year>/', views.payment_success_chart, name='chart-payment-success'),

    path('chart/payment-method/<int:year>/', views.payment_method_chart, name='chart-payment-method'),



#    path('invoicelist/', views.InvoiceListView.as_view(), name="invoice-list"),
#    path('create/', views.createInvoice, name="invoice-create"),
#    path('invoice-detail/<id>', views.view_PDF, name='invoice-detail'),
    path('invoice-download/<id>', views.generate_PDF, name='invoice-download'),


    path('rpolicy/',include(rpolicy.urls),name='rpayment'),
    path('ruser/',include(ruser.urls)),
    path('rpolicyRecord/',include(rpolicyRecord.urls)),
    path('rcategory/',include(rcategory.urls)),
    path('rquestion/',include(rquestion.urls)),
    path('rpayment/',include(rpayment.urls)),

    path('tchart/filter-options/', views.get_filter_toptions, name='tchart-filter-options'),
    path('tchart/sales/<int:year>/', views.tget_purchases_chart, name='test-chart'),

#    path('tchart/payment-success/<int:year>/', views.tpayment_success_chart, name='tchart-payment-success'),

    path('tchart/spend-per-customer/<int:year>/', views.tspend_per_customer_chart, name='tchart-spend-per-customer'),
    path('tchart/payment-method/<int:year>/', views.tpayment_method_chart, name='tchart-payment-method'),
    path('statistics2/', views.statistics_view2, name='shop-statistics2'),

]
