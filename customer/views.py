from email import policy
from multiprocessing.sharedctypes import Value
from typing import Type
from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required,user_passes_test
from django.shortcuts import get_object_or_404
from django.conf import settings
from coinbase_commerce.client import Client
from decimal import Decimal
from datetime import date, datetime
from django.utils.datastructures import MultiValueDictKeyError
import mimetypes
from django.db.models import Q
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from backoffice import models as CMODEL
from backoffice import forms as CFORM
from django.contrib.auth.models import User
from turtle import end_fill
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageDraw, ImageFont
import json
import os
import cv2
import numpy as np
from pytesseract import Output
import arabic_reshaper
import random
import math
from scipy.ndimage import interpolation as inter
import matplotlib.pyplot as plt
from ArabicOcr import arabicocr
from easyocr import Reader
import re
import pytesseract
import Levenshtein
from bidi.algorithm import get_display
from pyzbar.pyzbar import *
from glob import glob
import multiprocessing
import time
import subprocess
import string
import stripe
from django.http.response import JsonResponse
from .chat import get_response, predict_class
import fitz
from backoffice.models import Course

def auto_correction_word(bad_word,model_path,data_path):
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow import keras
    import numpy as np
    model = keras.models.load_model(model_path)
    tokenizer = Tokenizer()
    data = open(data_path, encoding="utf8").read()
    corpus = data.split("\n")
    for i in corpus:
        if i == "":
            corpus.remove('')
    corpus = corpus[1:-1]
    corpus_new = []
    for st in corpus:
        ch = " ".join(st)
        corpus_new.append(ch)
    tokenizer.fit_on_texts(corpus_new)
    total_words = len(tokenizer.word_index) + 1
    #############################################################################
    input_sequences = []
    for line in corpus_new:
        token_list = tokenizer.texts_to_sequences([line])[0]
        for i in range(1, len(token_list)):
            n_gram_sequence = token_list[:i + 1]
            input_sequences.append(n_gram_sequence)

    # pad sequences
    max_sequence_len = max([len(x) for x in input_sequences])
    input_sequences = np.array(pad_sequences(input_sequences, maxlen=max_sequence_len, padding='pre'))
    counter = len(bad_word)
    for i in range(counter):
        if (ord(bad_word[i]) in [i for i in range(285)]) == True:
            seed_text = " ".join(bad_word[:i])
            noTraited_text = " ".join(bad_word[i + 1:])
            next_words = 100

            for _ in range(next_words):
                token_list = tokenizer.texts_to_sequences([seed_text])[0]
                token_list = pad_sequences([token_list], maxlen=max_sequence_len - 1, padding='pre')
                #     predicted = model.predict_classes(token_list, verbose=0)
                predicted = np.argmax(model.predict(token_list), axis=1)
                output_word = ""
                for word, index in tokenizer.word_index.items():
                    if index == predicted:
                        output_word = word
                        break
            seed_text += " " + output_word + " " + noTraited_text
            bad_word = "".join(seed_text.split())
    return bad_word

def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# Réduction de bruits
def remove_noise(image):
    return cv2.medianBlur(image, 1)
# Seuillage
def thresholding(image):
    return cv2.threshold(image, 200, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]



def correct_ocr_order(results, pixels=25):
    text = []
    for i in range(len(results)):
        l = [[results[i][1],results[i][0][0][0]]]
        for j in range(len(results)):
            c=0
            if(i==j):
                continue
            for k in range(4):
                if abs(results[i][0][k][1]-results[j][0][k][1])<=pixels:
                    c+=1
            w = results[i][0][0][1]
            if(c>=3):
                l.append([results[j][1],results[j][0][0][0]])
                w = results[i][0][0][1]
                results[j][1]=''
        l = sorted(l,key=lambda x:round(x[1]),reverse=True)
        a=0
        for p in range(len(l)):
            if '' in l[p]:
                a+=1
        sentence = [l[i][0] for i in range(len(l))]
        phrase = ' '.join(sentence)
        if(a==0):
            text.append([phrase,w])
    text = sorted(text,key=lambda x:round(x[1]))
    return text

def correct_ocr_output(input):
    output=input
    output.replace('$','S')
    output.replace("()",'0')
    liste = [x for x in output]
    liste1 = ["" if x in set(string.punctuation) else x for x in liste]
    return "".join(liste1)

def correct_orientation(image, delta=.1, limit=45):
    def determine_score(arr, angle):
        data = inter.rotate(arr, angle, reshape=False, order=0)
        histogram = np.sum(data, axis=1)
        score = np.sum((histogram[1:] - histogram[:-1]) ** 2)
        return histogram, score

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 3)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1] 

    scores = []
    angles = np.arange(-limit, limit + delta, delta)
    for angle in angles:
        histogram, score = determine_score(thresh, angle)
        scores.append(score)

    best_angle = angles[scores.index(max(scores))]

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, \
              borderMode=cv2.BORDER_REPLICATE)

    return best_angle, rotated

def customerclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('customer-dashboard')
    return redirect('login')

@csrf_exempt
def checkout_view(request,pk):
    if request.method=='GET':
        customer = models.Customer.objects.get(user_id=request.user.id)
        policy_record = CMODEL.LeaveRecord.objects.get(customer=customer, id=pk)
        domain_url = 'http://localhost:8000/customer/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
        checkout_session = stripe.checkout.Session.create(
        success_url=domain_url + 'contracts',
        cancel_url=domain_url + 'dashboard',
        payment_method_types=['card'],
        mode='payment',
        client_reference_id=str(pk)+'_'+str(request.user.id)+'_'+"payment",
        customer_email=customer.email,
        line_items=[
                    {
                        'name': policy_record.Vocation.policy_name,
                        'quantity': 1,
                        'currency': 'eur',
                        'amount': int(policy_record.Vocation.sum_assurance * 106)
                    }
                ]
            )
        return redirect(checkout_session.url)
    return redirect('contracts')

@csrf_exempt
def process_payment(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policy_record = CMODEL.LeaveRecord.objects.get(customer=customer, id=pk)
    order_id = request.session.get('order_id')
    host = 'localhost:8000/customer/'
    paypal_dict = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': int(policy_record.Vocation.sum_assurance * 1.06),
        'item_name': 'Order {}'.format(policy_record.id),
        'invoice': str(request.user.id)+" "+str(pk),
        'currency_code': 'USD',
        'notify_url': 'http://{}{}'.format(host,
                                           reverse('paypal-ipn')),
        'return_url': 'http://{}{}'.format(host,
                                           reverse('contracts')),
        'cancel_return': 'http://{}{}'.format(host,
                                              reverse('contracts')),
    }
    return redirect(paypal_dict['notify_url'])

@csrf_exempt
def coinbase_checkout_view(request,pk):
    if request.method=='GET':
        customer = models.Customer.objects.get(user_id=request.user.id)
        policy_record = CMODEL.LeaveRecord.objects.get(customer=customer, id=pk)
        domain_url = 'http://localhost:8000/customer/'
        client = Client(api_key=settings.COINBASE_COMMERCE_API_KEY)
        product = {
            'name': policy_record.Vocation.policy_name,
            'description': 'A really good car backoffice deal.',
            'local_price': {
                'amount': int(policy_record.Vocation.sum_assurance * 1.06),
                'currency': 'TND'
            },
            'pricing_type': 'fixed_price',
            'redirect_url': domain_url + 'contracts',
            'cancel_url': domain_url + 'dashboard',
        }
        charge = client.charge.create(**product)
        return redirect(charge.hosted_url)
    return redirect('contracts')

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_id = session.client_reference_id.split("_")[1]
        contract_id = session.client_reference_id.split("_")[0]
        customer = models.Customer.objects.get(user_id=customer_id)
        policy_record = CMODEL.LeaveRecord.objects.get(customer=customer, id=contract_id)
        policy_record.status="Approved"
        policy_record.save()
        user_dir = os.path.join(settings.MEDIA_ROOT, "customer_{}".format(customer_id))
        invoice_path = os.path.join(user_dir,"INV-{}{}.pdf".format(customer_id,policy_record.id))
        contract_path = os.path.join(user_dir,"contrat_{}_{}.pdf".format(customer_id,policy_record.id))
        signature_path = os.path.join(settings.BASE_DIR,"signature.png")
     #   signature_add(invoice_path,signature_path,3000,950,0.6,0.9)
      #  signature_add(contract_path,signature_path,3100,1200,0.6,0.9)
        if customer.email_notifications:
            message = get_template("mail.html").render({'context':""})
            email = EmailMessage(
        'Paiement effectué avec succès',
        message,
        'keycorpsolutions@gmail.com',
        [customer.email],
    )
            #user_dir = os.path.join(settings.MEDIA_ROOT, "customer_{}".format(customer_id))
            email.content_subtype="html"
            #email.attach_file(os.path.join(user_dir,"contrat_{}_{}.png".format(customer_id,policy_record.id)))
            email.send()
        if customer.sms_notifications:
            pass
        if customer.call_notifications:
            pass
        if customer.whatsapp_notifications:
            pass
        intent = stripe.PaymentIntent.retrieve(session.payment_intent)
        used_card = intent.charges.data[0].payment_method_details.card
        if not CMODEL.Card .objects.all().filter(customer=customer,last4=used_card.last4,brand=used_card.brand):
            card = CMODEL.Card(customer=customer,holder=intent.charges.data[0].billing_details.name,brand=used_card.brand,last4=used_card.last4,exp_month=used_card.exp_month,exp_year=used_card.exp_year % 100)
            card.save()
        else:
            CMODEL.Card.objects.all().filter(customer=customer,last4=used_card.last4,brand=used_card.brand).update(holder=intent.charges.data[0].billing_details.name,exp_month=used_card.exp_month,exp_year=used_card.exp_year % 100)
    #return HttpResponse(status=200)
    return redirect('contracts')


def customer_signup_view(request):
    userForm=forms.CustomerUserForm()
    customerForm=forms.CustomerForm()
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST)
        customerForm=forms.CustomerForm(request.POST,request.FILES)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customer=customerForm.save(commit=False)
            customer.user=user
            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)
        return HttpResponseRedirect('login')
    return render(request,'home/sign-up.html',context=mydict)

def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()

def chatbot_view(request):
    if request.method=='GET':
        return render(request,'base.html')
    pass
    
@csrf_exempt
def predict_view(request):
    if request.method=='POST':
        text=json.load(request)['message']
        ints=predict_class(text)
        intents = json.loads(open('intents.json').read())
        response =get_response(ints,intents)
        message={'answer':response}
        return JsonResponse(message)
    return render(request,'customer/index.html')

def presentation_view(request):
    return render(request,'presentation.html') 

def rtl_view(request):
    dict={"segment":"rtl"}
    return render(request,'home/rtl.html',context=dict) 

def virtual_reality_view(request):
    dict={"segment":"virtual"}
    return render(request,'home/virtual-reality.html',context=dict)   

@login_required(login_url='login')
def customer_dashboard_view(request):

    dict={
        'customer':models.Customer.objects.get(user_id=request.user.id),
        'available_policy':CMODEL.Vocation.objects.all().count(),
        'applied_policy':CMODEL.LeaveRecord.objects.all().filter(customer=models.Customer.objects.get(user_id=request.user.id)).count(),
        'total_category':CMODEL.Category.objects.all().count(),
        'total_question':CMODEL.Question.objects.all().filter(customer=models.Customer.objects.get(user_id=request.user.id)).count(),
        "segment":"customer-dashboard",
        'course':CMODEL.Course.objects.all().count(),


        'courses' :CMODEL.Course.objects.filter(paid=True)


    }


    return render(request,'home/index.html',context=dict)

def toggle_email_view(request):
    w = models.Customer.objects.get(id=request.POST['id'])
    w.email_notifications = request.POST['email_check'] == 'true'
    w.save()
    return HttpResponse('success')

def toggle_sms_view(request):
    w = models.Customer.objects.get(id=request.POST['id'])
    w.sms_notifications = request.POST['sms_check'] == 'true'
    w.save()
    return HttpResponse('success')

def toggle_call_view(request):
    w = models.Customer.objects.get(id=request.POST['id'])
    w.call_notifications = request.POST['call_check'] == 'true'
    w.save()
    return HttpResponse('success')

def toggle_whatsapp_view(request):
    w = models.Customer.objects.get(id=request.POST['id'])
    w.whatsapp_notifications = request.POST['whatsapp_check'] == 'true'
    w.save()
    return HttpResponse('success')


@login_required(login_url='login')
def profile_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    dict={'customer':customer,"segment":"profile"}
    return render(request,'home/profile.html',context=dict)   

@login_required(login_url='login')
def billing_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policies = CMODEL.LeaveRecord.objects.all().filter(customer=customer)
    cards = CMODEL.Card.objects.all().filter(customer=customer)
    gross = customer.rate * customer.hrs
    net = gross * 0.9
    try:
        newest_card = CMODEL.Card.objects.filter(customer=customer).latest('creation_time')
    except:
        newest_card = None
    return render(request,'home/billing.html',{'segment':"billing",'policies':policies,'newest_card':newest_card,'cards':cards,'customer':customer,'gross':gross,'net':net})

@login_required(login_url='login')
def apply_policy_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policies = CMODEL.Vocation.objects.all()
    return render(request,'home/generate_contract.html',{'policies':policies,'customer':customer,'segment':"apply-policy"})

def apply_view(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policy = CMODEL.Vocation.objects.get(id=pk)
    policyrecord = CMODEL.LeaveRecord()
    policyrecord.Policy = policy
    policyrecord.customer = customer
    policyrecord.save()
    email = EmailMessage(
        'Demande de congé en cours de traitement',
        "Votre demande de congé de numéro {}{} créée le {} a été envoyée avec succès et est en cours de traitement.".format(request.user.id,policyrecord.id,policyrecord.creation_date),
        'proxymartstore@gmail.com',
        ["driverprodigy@gmail.com",customer.email],
    )
    email.send()
    return redirect('history')

def history_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policies = CMODEL.LeaveRecord.objects.all().filter(customer=customer)
    return render(request,'customer/history.html',{'policies':policies,'customer':customer})


def delete_contract_view(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policy_record = CMODEL.LeaveRecord.objects.get(customer=customer, id=pk)
    policy_record.delete()
    return redirect('contracts')

def delete_card_view(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    card = CMODEL.Card.objects.get(customer=customer,id=pk)
    card.delete()
    return redirect('billing')

def delete_car_view(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    car = CMODEL.Car.objects.get(owner=customer,id=pk)
    car.delete()
    return redirect('contracts')

@login_required(login_url='login')
def history_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    vocations = CMODEL.LeaveRecord.objects.all().filter(customer=customer)
    cars = CMODEL.Car.objects.all().filter(owner=customer)
    return render(request,'home/tables.html',{'cars':cars,'vocations':vocations,'customer':customer,'segment':"contracts"})

def delete_question_view(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    question = CMODEL.Question.objects.get(customer=customer,id=pk)
    question.delete()
    return redirect('question-history')

def question_history_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    questions = CMODEL.Question.objects.all().filter(customer=customer)
    questionForm=CFORM.QuestionForm() 
    if request.method=='POST':
        questionForm=CFORM.QuestionForm(request.POST)
        if questionForm.is_valid():
            question = questionForm.save(commit=False)
            question.customer=customer
            question.save()
            return redirect('question-history')
    return render(request,'home/my-questions.html',{'questionForm':questionForm,'questions':questions,'customer':customer,
                                                    'segment' : "question-history"})


def download_attendance(request):
    e = models.Customer.objects.get(user_id=request.user.id)
    employee_dir = os.path.join(settings.MEDIA_ROOT, "employee_{}".format(request.user.id))
    os.makedirs(employee_dir,exist_ok=True)
    filename = "attendance_{}.pdf".format(request.user.id)
    font = ImageFont.truetype("arial.ttf", 35, encoding="utf-8")
    font1 = ImageFont.truetype("arial.ttf", 15, encoding="utf-8")
    canvas = Image.open('attendance.png')
    canvas=canvas.convert('RGB')
    draw = ImageDraw.Draw(canvas)
    draw.text((430, 420), str(request.user.first_name)+" "+str(request.user.last_name), 'black', font)
    draw.text((530, 580), "{}    {}      {}".format(datetime.now().day,datetime.now().month,datetime.now().year), 'black', font1)
    canvas.save(os.path.join(employee_dir,filename))
    #signature_add(os.path.join(employee_dir,filename),'signature.png',3000,750,0.6,0.9)
    filepath = settings.BASE_DIR + '\\static\\' + "employee_{}\\".format(request.user.id) + filename
    fl = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filename)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    email = EmailMessage(
    'Certificat de présence',
    "Veuillez trouver ci-joint votre certificat de présence, attribuée suite à votre demande.",
    'proxymartstore@gmail.com',
    ["driverprodigy@gmail.com",e.email],
)
    email.attach_file(os.path.join(employee_dir,filename))
    email.send()
    return response

def download_payslip(request):
    e = models.Customer.objects.get(user_id=request.user.id)
    employee_dir = os.path.join(settings.MEDIA_ROOT, "employee_{}".format(request.user.id))
    os.makedirs(employee_dir,exist_ok=True)
    filename = "payslip_{}_{}_{}.pdf".format(request.user.id,datetime.now().month,datetime.now().year)
    font2 = ImageFont.truetype("arial.ttf", 15, encoding="utf-8")
    font = ImageFont.truetype("arial.ttf", 20, encoding="utf-8")
    canvas = Image.open('payslip.png')
    canvas=canvas.convert('RGB')
    draw = ImageDraw.Draw(canvas)
    draw.text((550, 300), "{} H".format(e.hrs), 'black', font)
    draw.text((620, 305), "{} DT/H".format(e.rate), 'black', font2)
    draw.text((700, 305), "{} DT".format(e.hrs*e.rate), 'black', font2)
    draw.text((700, 340), "{} DT".format(e.hrs*e.rate), 'black', font2)
    draw.text((700, 370), "{} DT".format(e.hrs*e.rate*0.1), 'black', font2)
    draw.text((700, 400), "{} DT".format(e.hrs*e.rate*0.9), 'black', font2)
    draw.text((700, 430), "{} DT".format(e.hrs*e.rate*0.9*0.02), 'black', font2)
    draw.text((530, 200), "{}/{}/{}".format(datetime.now().day,datetime.now().month,datetime.now().year), 'black', font2)
    draw.text((40, 170), "{} {}".format(request.user.first_name,request.user.last_name), 'black', font2)
    draw.text((40, 200), "{}".format(e.address), 'black', font2)
    canvas.save(os.path.join(employee_dir,filename))
   # signature_add(os.path.join(employee_dir,filename),'signature.png',450,450,0.6,0.9)
    filepath = settings.BASE_DIR + '\\static\\' + "employee_{}\\".format(request.user.id) + filename
    fl = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filename)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    email = EmailMessage(
    'Bulletin de paie',
    "Veuillez trouver ci-joint votre bulletin de paie pour le mois {}/{}.".format(datetime.now().month,datetime.now().year),
    'proxymartstore@gmail.com',
    ["driverprodigy@gmail.com",e.email],
)
    email.attach_file(os.path.join(employee_dir,filename))
    email.send()
    return response

def download_autorization(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    leave_record = CMODEL.LeaveRecord.objects.get(customer=customer,id=pk)
    if leave_record.status != "Approved":
        return redirect('contracts')
    employee_dir = os.path.join(settings.MEDIA_ROOT, "employee_{}".format(request.user.id))
    os.makedirs(employee_dir,exist_ok=True)
    filename = "autorization_{}_{}.pdf".format(request.user.id,pk)
    font = ImageFont.truetype("arial.ttf", 35, encoding="utf-8")
    font1 = ImageFont.truetype("arial.ttf", 25, encoding="utf-8")
    canvas = Image.open('autorization.jpg')
    canvas=canvas.convert('RGB')
    draw = ImageDraw.Draw(canvas)
    draw.text((100, 410), "{} {}".format(request.user.first_name,request.user.last_name), 'black', font)
    draw.text((180, 470), "{}".format(leave_record.creation_date), 'black', font)
    draw.text((670, 570), "{}{}".format(request.user.id,pk), 'black', font)
    draw.text((335, 595), "{}".format(leave_record.creation_date), 'black', font1)
    canvas.save(os.path.join(employee_dir,filename))
  #  signature_add(os.path.join(employee_dir,filename),'signature.png',5000,600,0.6,0.9)
    filepath = settings.BASE_DIR + '\\static\\' + "employee_{}\\".format(request.user.id) + filename
    fl = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filename)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response


def movie_recommendation_view(request):
    if request.method == "GET":
      # The context/data to be presented in the HTML template
      context = generate_movies_context()
      # Render a HTML page with specified template and context
      return render(request, 'customer/movie_list.html', context)

def generate_movies_context():
    context = {}
    # Show only movies in recommendation list
    # Sorted by vote_average in desc
    # Get recommended movie counts
    recommended_count = Course.objects.filter(
        recommended=True
    ).count()
    # If there are no recommended movies
    if recommended_count == 0:
        # Just return the top voted and unwatched movies as popular ones
        courses = Course.objects.filter(
            watched=False
        ).order_by('-vote_count')[:30]
    else:
        # Get the top voted, unwatched, and recommended movies
        courses = Course.objects.filter(
            watched=False
        ).filter(
            recommended=True
        ).order_by('-vote_count')[:30]
    context['movie_list'] = courses

    return context