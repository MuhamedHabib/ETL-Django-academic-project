from bokeh.embed import components
from bokeh.plotting import figure
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import ExtractYear, ExtractMonth
from django.shortcuts import render, redirect, reverse
from regex import F
from rest_framework import viewsets
from validators import Max

from . import forms, models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta, datetime
from django.db.models import Q
from django.core.mail import send_mail
from django.contrib.auth.models import User
from customer import models as CMODEL
from customer import forms as CFORM
from django.db.models import Count, F, Sum, Avg

from .charts import months, colorPrimary, colorSuccess, colorDanger, generate_color_palette, get_year_dict
from .json import jsonPolicy, json_user, jsonPolicyRecord, jsonCategory, jsonPayment, jsonQuestion
from .models import Vocation, Sales, LeaveRecord, Category, Question,Course

#from .models import InvoiceRecod, Invoice
#from .forms import InvoiceForm, LineItemFormset
import pdfkit
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.template.loader import get_template
from django.http import HttpResponse
#!
from django.views.decorators.csrf import csrf_exempt

def landing_view(request):
    return render(request,"index.html",context={"auth":"1" if request.user.is_authenticated else "0"})

def presentation_view(request):
    return render(request,"presentation.html")

def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')  
    return render(request, 'backoffice/index.html')


def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()


def afterlogin_view(request):
    if is_customer(request.user):      
        return redirect('customer/dashboard')
    else:
        return redirect('admin-dashboard')



def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    dict = {
        'totalcustomer': CMODEL.Customer.objects.all().count,

        'policies' : models.Vocation.objects.all(),
        #'total_amnt': models.Invoice.objects.all().aggregate(Avg('total_amount')),
        'total_user': CMODEL.Customer.objects.all().count(),
        'total_policy': models.Vocation.objects.all().count(),
        'total_category': models.Category.objects.all().count(),
        'total_question': models.Question.objects.all().count(),
        'total_questionthisweek': models.Question.objects.filter(asked_date=datetime.today()).count(),

        'total_policy_holder': models.LeaveRecord.objects.all().count(),
        'approved_policy_holder': models.LeaveRecord.objects.all().filter(status='Approved').count(),
        'disapproved_policy_holder': models.LeaveRecord.objects.all().filter(status='Disapproved').count(),
        'waiting_policy_holder': models.LeaveRecord.objects.all().filter(status='Pending').count(),
        'total_purchase': models.Sales.objects.all().filter(successful=True).count(),
       # 'total_Invoices': models.InvoiceRecod.objects.count(),
        #'purchases_month':Invoice.objects.filter(date__range=["2022-01-01", "2022-03-30"]).count(),
        'date_now':datetime.now(),
        #'last_payment':Invoice.objects.all()[:1],
       # 'tttt':Invoice.objects.filter(customer=F('customer'))[:1],
        'filt': Question.objects.filter(asked_date=F('customer'))[:1],
        #'etherum-purchases':models.Purchase.objects.filter(successful=True).annotate(method=Count('Ethereum')),
       # 'amounttotl':models.Invoice.objects.all().annotate(Sum('total_amount')),
        'Etherumpayment':models.Sales.objects.all().filter(payment_method={"Ethereum", "bitcoin"}).count()



    # 'total_purchasesum': models.Purchase.objects.all().filter(successful=True).sum(),

    }
    return render(request, 'backoffice/admin_dashboardV2.html', context=dict)



@login_required(login_url='adminlogin')
def admin_view_customer_view(request):
    customers= CMODEL.Customer.objects.all()
    return render(request, 'backoffice/admin_view_customerV2.html', {'customers':customers})



@login_required(login_url='adminlogin')
def update_customer_view(request,pk):
    customer=CMODEL.Customer.objects.get(id=pk)
    user=CMODEL.User.objects.get(id=customer.user_id)
    userForm=CFORM.CustomerUserForm(instance=user)
    customerForm=CFORM.CustomerForm(request.FILES,instance=customer)
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=CFORM.CustomerUserForm(request.POST,instance=user)
        customerForm=CFORM.CustomerForm(request.POST,request.FILES,instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return redirect('admin-view-customer')
    return render(request, 'backoffice/update_customer.html', context=mydict)



@login_required(login_url='adminlogin')
def delete_customer_view(request,pk):
    customer=CMODEL.Customer.objects.get(id=pk)
    user=User.objects.get(id=customer.user_id)
    user.delete()
    customer.delete()
    return HttpResponseRedirect('/admin-view-customer')



def admin_category_view(request):
    return render(request, 'backoffice/admin_categoryV2.html')

def admin_add_category_view(request):
    categoryForm=forms.CategoryForm() 
    if request.method=='POST':
        categoryForm=forms.CategoryForm(request.POST)
        if categoryForm.is_valid():
            categoryForm.save()
            return redirect('admin-view-category')
    return render(request, 'backoffice/admin_add_categoryV2.html', {'categoryForm':categoryForm})

def admin_view_category_view(request):
    categories = models.Category.objects.all()
    return render(request, 'backoffice/admin_view_categoryV2.html', {'categories':categories})

def admin_delete_category_view(request):
    categories = models.Category.objects.all()
    return render(request, 'backoffice/admin_delete_categoryV2.html', {'categories':categories})
    
def delete_category_view(request,pk):
    category = models.Category.objects.get(id=pk)
    category.delete()
    return redirect('admin-delete-category')

def admin_update_category_view(request):
    categories = models.Category.objects.all()
    return render(request, 'backoffice/admin_update_categoryV2.html', {'categories':categories})

@login_required(login_url='adminlogin')
def update_category_view(request,pk):
    category = models.Category.objects.get(id=pk)
    categoryForm=forms.CategoryForm(instance=category)
    
    if request.method=='POST':
        categoryForm=forms.CategoryForm(request.POST,instance=category)
        
        if categoryForm.is_valid():

            categoryForm.save()
            return redirect('admin-update-category')
    return render(request, 'backoffice/update_category.html', {'categoryForm':categoryForm})
  
  

def admin_policy_view(request):
    return render(request, 'backoffice/admin_policyV2.html')


def admin_add_policy_view(request):
    policyForm=forms.PolicyForm() 
    
    if request.method=='POST':
        policyForm=forms.PolicyForm(request.POST)
        if policyForm.is_valid():
            categoryid = request.POST.get('category')
            category = models.Category.objects.get(id=categoryid)
            
            policy = policyForm.save(commit=False)
            policy.category=category
            policy.save()
            return redirect('admin-view-policy')
    return render(request, 'backoffice/admin_add_policy.html', {'policyForm':policyForm})

def admin_view_policy_view(request):
    policies = models.Vocation.objects.all()
    return render(request, 'backoffice/admin_view_policy__V2.html', {'policies':policies})



def admin_update_policy_view(request):
    policies = models.Vocation.objects.all()
    return render(request, 'backoffice/admin_update_policyV2.html', {'policies':policies})

@login_required(login_url='adminlogin')
def update_policy_view(request,pk):
    policy = models.Vocation.objects.get(id=pk)
    policyForm=forms.PolicyForm(instance=policy)
    
    if request.method=='POST':
        policyForm=forms.PolicyForm(request.POST,instance=policy)
        
        if policyForm.is_valid():

            categoryid = request.POST.get('category')
            category = models.Category.objects.get(id=categoryid)
            
            policy = policyForm.save(commit=False)
            policy.category=category
            policy.save()
           
            return redirect('admin-update-policy')
    return render(request, 'backoffice/update_policy.html', {'policyForm':policyForm})
  
  
def admin_delete_policy_view(request):
    policies = models.Vocation.objects.all()
    return render(request, 'backoffice/admin_delete_policyV2.html', {'policies':policies})
    
def delete_policy_view(request,pk):
    policy = models.Vocation.objects.get(id=pk)
    policy.delete()
    return redirect('admin-delete-policy')

def admin_view_policy_holder_view(request):
    policyrecords = models.LeaveRecord.objects.all()
    return render(request, 'backoffice/admin_view_policy_holderV2.html', {'policyrecords':policyrecords})

def admin_view_approved_policy_holder_view(request):
    policyrecords = models.LeaveRecord.objects.all().filter(status='Approved')
    return render(request, 'backoffice/admin_view_approved_policy_holderV2.html', {'policyrecords':policyrecords})

def admin_view_disapproved_policy_holder_view(request):
    policyrecords = models.LeaveRecord.objects.all().filter(status='Disapproved')
    return render(request, 'backoffice/admin_view_disapproved_policy_holderV2.html', {'policyrecords':policyrecords})

def admin_view_waiting_policy_holder_view(request):
    policyrecords = models.LeaveRecord.objects.all().filter(status='Pending')
    return render(request, 'backoffice/admin_view_waiting_policy_holderV2.html', {'policyrecords':policyrecords})

def approve_request_view(request,pk):
    policyrecords = models.LeaveRecord.objects.get(id=pk)
    policyrecords.status='Approved'
    policyrecords.save()
    return redirect('admin-view-policy-holder')

def disapprove_request_view(request,pk):
    policyrecords = models.LeaveRecord.objects.get(id=pk)
    policyrecords.status='Disapproved'
    policyrecords.save()
    return redirect('admin-view-policy-holder')


def admin_question_view(request):
    questions = models.Question.objects.all()
    return render(request, 'backoffice/admin_questionV2.html', {'questions':questions})

def update_question_view(request,pk):
    question = models.Question.objects.get(id=pk)
    questionForm=forms.QuestionForm(instance=question)
    
    if request.method=='POST':
        questionForm=forms.QuestionForm(request.POST,instance=question)
        
        if questionForm.is_valid():

            admin_comment = request.POST.get('admin_comment')
            
            
            question = questionForm.save(commit=False)
            question.admin_comment=admin_comment
            question.save()
           
            return redirect('admin-question')
    return render(request, 'backoffice/update_question.html', {'questionForm':questionForm})


def aboutus_view(request):
    return render(request, 'backoffice/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'backoffice/contactussuccess.html')
    return render(request, 'backoffice/contactus.html', {'form':sub})


def products(request):
    delle2009wt = 2
    Dell17 = 2
    none = 2
    counts = []
    items = ["pn1", "pn2", "pn3"]
    prod = Vocation.policy_name.values()

    for i in prod:
        if "pn1" in i.values():
            delle2009wt += 1
        elif ('pn2"' in i.values()):
            Dell17 += 1
        elif ("pn3" in i.values()):
            none += 1
    counts.extend([delle2009wt, Dell17, none])

    plot = figure(x_range=items, plot_height=170, plot_width=200, title="FIS-Products",
                  toolbar_location="right", tools="pan,wheel_zoom,box_zoom,reset, hover, tap, crosshair")
    plot.title.text_font_size = '20pt'

    plot.xaxis.major_label_text_font_size = "14pt"
    plot.vbar(items, top=counts, width=.4, color="dodgerblue", legend="Product Counts")
    plot.legend.label_text_font_size = '14pt'

    script, div = components(plot)

    return render(request, 'backoffice/admin_dashboardV2.html', {'script': script, 'div': div})


#################
# filter methde for charts
# @staff_member_required
def get_filter_options(request):
    grouped_purchases = Vocation.objects.annotate(year=ExtractYear('creation_date')).values('year').order_by(
        '-year').distinct()
    options = [purchase['year'] for purchase in grouped_purchases]

    return JsonResponse({
        'options': options,
    })


# 1st chart
def get_sales_chart(request, year):
    purchases = Vocation.objects.filter(creation_date__year=year)
    grouped_purchases = purchases.annotate(price=F('sum_assurance')).annotate(month=ExtractMonth('creation_date')) \
        .values('month').annotate(average=Sum('sum_assurance')).values('month', 'average').order_by('month')

    sales_dict = get_year_dict()

    for group in grouped_purchases:
        sales_dict[months[group['month'] - 1]] = round(group['average'], 2)

    return JsonResponse({
        'title': f'Sales in {year}',
        'data': {
            'labels': list(sales_dict.keys()),
            'datasets': [{
                'label': 'Amount ($)',
                'backgroundColor': colorPrimary,
                'borderColor': colorPrimary,
                'data': list(sales_dict.values()),
            }]
        },
    })


# 2nd chart
def spend_per_customer_chart(request, year):
    purchases = Vocation.objects.filter(creation_date__year=year)
    grouped_purchases = purchases.annotate(price=F('sum_assurance')).annotate(month=ExtractMonth('creation_date')) \
        .values('month').annotate(average=Avg('sum_assurance')).values('month', 'average').order_by('month')

    spend_per_customer_dict = get_year_dict()

    for group in grouped_purchases:
        spend_per_customer_dict[months[group['month'] - 1]] = round(group['average'], 2)

    return JsonResponse({
        'title': f'Spend per customer in {year}',
        'data': {
            'labels': list(spend_per_customer_dict.keys()),
            'datasets': [{
                'label': 'Amount ($)',
                'backgroundColor': colorPrimary,
                'borderColor': colorPrimary,
                'data': list(spend_per_customer_dict.values()),
            }]
        },
    })


#def payment_success_chart(request, year):
   # purchases = Invoice.objects.filter(date__year=year)

   # return JsonResponse({
      #  'title': f'Invoices Status {year}',
       # 'data': {
        #    'labels': ['paid', 'not paid'],
         #   'datasets': [{
          #      'label': 'Amount ($)',
            #    'backgroundColor': [colorSuccess, colorDanger],
             #   'borderColor': [colorSuccess, colorDanger],
             #   'data': [
             #       purchases.filter(status=True).count(),
          #          purchases.filter(status=False).count(),
         #       ],
         #   }]
       # },
  #  })


#########Invoices########



def generate_PDF(request, id):
    # Use False instead of output path to save pdf to a variable
    pdf = pdfkit.from_url(request.build_absolute_uri(reverse('backoffice:invoice-detail', args=[id])), False)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

    return response






def change_status(request):
    return redirect('backoffice:invoice-list')


def view_404(request, *args, **kwargs):
    return redirect('backoffice:invoice-list')


############Admin Charts############################Admin Charts################
############Admin Charts############################Admin Charts################

@staff_member_required
def payment_method_chart(request, year):
    purchases = Sales.objects.filter(time__year=year)
    grouped_purchases = purchases.values('payment_method').annotate(count=Count('id')) \
        .values('payment_method', 'count').order_by('payment_method')

    payment_method_dict = dict()

    for payment_method in Sales.PAYMENT_METHODS:
        payment_method_dict[payment_method[1]] = 0

    for group in grouped_purchases:
        payment_method_dict[dict(Sales.PAYMENT_METHODS)[group['payment_method']]] = group['count']

    return JsonResponse({
        'title': f'Payment method rate in {year}',
        'data': {
            'labels': list(payment_method_dict.keys()),
            'datasets': [{
                'label': 'Amount ($)',
                'backgroundColor': generate_color_palette(len(payment_method_dict)),
                'borderColor': generate_color_palette(len(payment_method_dict)),
                'data': list(payment_method_dict.values()),
            }]
        },
    })


############Admin Charts############################Admin Charts################
############Admin Charts############################Admin Charts################

# affiche charts dans un template
def statistics_view(request):
    return render(request, 'statistics.html', {})


def get_filter_toptions(request):
    grouped_purchases = Vocation.objects.annotate(year=ExtractYear('creation_date')).values('year').order_by(
        '-year').distinct()
    options = [purchase['year'] for purchase in grouped_purchases]

    return JsonResponse({
        'options': options,
    })


@staff_member_required
def tpayment_method_chart(request, year):
    purchases = Sales.objects.filter(time__year=year)
    grouped_purchases = purchases.values('payment_method').annotate(count=Count('id')) \
        .values('payment_method', 'count').order_by('payment_method')

    payment_method_dict = dict()

    for payment_method in Sales.PAYMENT_METHODS:
        payment_method_dict[payment_method[1]] = 0

    for group in grouped_purchases:
        payment_method_dict[dict(Sales.PAYMENT_METHODS)[group['payment_method']]] = group['count']

    return JsonResponse({
        'title': f'Payment method rate in {year}',
        'data': {
            'labels': list(payment_method_dict.keys()),
            'datasets': [{
                'label': 'Amount ($)',
                'backgroundColor': generate_color_palette(len(payment_method_dict)),
                'borderColor': generate_color_palette(len(payment_method_dict)),
                'data': list(payment_method_dict.values()),
            }]
        },
    })


#def tpayment_success_chart(request, year):
  #  purchases = Sales.objects.filter(time__year=year)

   # return JsonResponse({
    #    'title': f'Payment success rate in {year}',
     #   'data': {
      #      'labels': ['Successful', 'Unsuccessful'],
       #     'datasets': [{
        #        'label': 'Amount ($)',
         #       'backgroundColor': [colorSuccess, colorDanger],
          #      'borderColor': [colorSuccess, colorDanger],
           #     'data': [
            #        purchases.filter(successful=True).count(),
             #       purchases.filter(successful=False).count(),
              #  ],
       #     }]
        #},
    #})


def tspend_per_customer_chart(request, year):
    purchases = Vocation.objects.filter(creation_date__year=year)
    grouped_purchases = purchases.annotate(price=F('sum_assurance')).annotate(month=ExtractMonth('creation_date')) \
        .values('month').annotate(average=Avg('sum_assurance')).values('month', 'average').order_by('month')

    spend_per_customer_dict = get_year_dict()

    for group in grouped_purchases:
        spend_per_customer_dict[months[group['month'] - 1]] = round(group['average'], 2)

    return JsonResponse({
        'title': f'Total Amount in {year}',
        'data': {
            'labels': list(spend_per_customer_dict.keys()),
            'datasets': [{
                'label': 'Amount ($)',
                'backgroundColor': colorPrimary,
                'borderColor': colorPrimary,
                'data': list(spend_per_customer_dict.values()),
            }]
        },
    })


def tget_purchases_chart(request, year):
    purchases = Invoice.objects.filter(date__year=year)
    grouped_purchases = purchases.annotate(price=F('total_amount')).annotate(month=ExtractMonth('date')) \
        .values('month').annotate(average=Sum('total_amount')).values('month', 'average').order_by('month')

    sales_dict = get_year_dict()

    for group in grouped_purchases:
        sales_dict[months[group['month'] - 1]] = round(group['average'], 2)

    return JsonResponse({
        'title': f'Purchases in {year}',
        'data': {
            'labels': list(sales_dict.keys()),
            'datasets': [{
                'label': 'Total Amount ($)',
                'backgroundColor': colorPrimary,
                'borderColor': colorPrimary,
                'data': list(sales_dict.values()),
            }]
        },
    })


def statistics_view2(request):
    dict = {
        'activeuser':User.objects.filter(is_active=True).count(),
        'total_user': CMODEL.Customer.objects.all().count(),
        'total_policy': models.Vocation.objects.all().count(),
        'total_category': models.Category.objects.all().count(),
        'total_question': models.Question.objects.all().count(),
        'total_policy_holder': models.LeaveRecord.objects.all().count(),
        'approved_policy_holder': models.LeaveRecord.objects.all().filter(status='Approved').count(),
        'disapproved_policy_holder': models.LeaveRecord.objects.all().filter(status='Disapproved').count(),
        'waiting_policy_holder': models.LeaveRecord.objects.all().filter(status='Pending').count(),
        'total_purchase': models.Sales.objects.all().filter(successful=True).count(),
       # 'total_Invoices': models.InvoiceRecod.objects.count(),
        'total_Purchases': models.Sales.objects.count(),
        #'total_Paid': models.InvoiceRecod.objects.count(),
        'stripe': models.Sales.objects.all().filter(payment_method="Stripe").count(),
      #  'total_amount2': models.Invoice.objects.all().aggregate(Avg('total_amount')),
        'etherum': models.Sales.objects.all().filter(payment_method="Etherum").count(),
        'paypal': models.Sales.objects.all().filter(payment_method="Paypal").count(),
        'totpayment': models.Sales.objects.all().filter().count(),

      #  'purchases_month': Invoice.objects.filter(date__range=["2022-01-01", "2022-03-30"]).count(),

        # 'total_purchasesum': models.Purchase.objects.all().filter(successful=True).sum(),

    }

    return render(request, 'backoffice/test-chart.html', context=dict)


#############API

class policy_list(viewsets.ModelViewSet):
    queryset = Vocation.objects.all()
    serializer_class = jsonPolicy


#############API(method 2 sur les laptops)

#############API users#############
class user_list(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = json_user


class policyRecord_list(viewsets.ModelViewSet):
    queryset = LeaveRecord.objects.all()
    serializer_class = jsonPolicyRecord


#############API users#############
class category_list(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = jsonCategory


#############API users#############
class payment_list(viewsets.ModelViewSet):
    queryset = Sales.objects.all()
    serializer_class = jsonPayment


#############API users#############
class question_list(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = jsonQuestion



