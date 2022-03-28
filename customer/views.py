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
from datetime import date, timedelta
from django.utils.datastructures import MultiValueDictKeyError
import mimetypes
from django.db.models import Q
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from insurance import models as CMODEL
from insurance import forms as CFORM
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

def signature_add(input_file,signature_file,w,h,x1,x2):
    input_file = input_file
    signature_file = signature_file
    image_rectangle = fitz.Rect(w * x1 * -1 * 0.94, h * x2, w, h)
    file_handle = fitz.open(input_file)
    first_page = file_handle[0]
    first_page.insert_image(image_rectangle, filename=signature_file)
    file_handle.saveIncr()

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
        policy_record = CMODEL.PolicyRecord.objects.get(customer=customer,id=pk)
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
                        'name': policy_record.Policy.policy_name,
                        'quantity': 1,
                        'currency': 'eur',
                        'amount': int(policy_record.Policy.sum_assurance*106)
                    }
                ]
            )
        return redirect(checkout_session.url)
    return redirect('contracts')

@csrf_exempt
def process_payment(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policy_record = CMODEL.PolicyRecord.objects.get(customer=customer,id=pk)
    order_id = request.session.get('order_id')
    host = 'localhost:8000/customer/'
    paypal_dict = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': int(policy_record.Policy.sum_assurance*1.06),
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
        policy_record = CMODEL.PolicyRecord.objects.get(customer=customer,id=pk)
        domain_url = 'http://localhost:8000/customer/'
        client = Client(api_key=settings.COINBASE_COMMERCE_API_KEY)
        product = {
            'name': policy_record.Policy.policy_name,
            'description': 'A really good car insurance deal.',
            'local_price': {
                'amount': int(policy_record.Policy.sum_assurance*1.06),
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
        policy_record = CMODEL.PolicyRecord.objects.get(customer=customer,id=contract_id)
        policy_record.status="Approved"
        policy_record.save()
        user_dir = os.path.join(settings.MEDIA_ROOT, "customer_{}".format(customer_id))
        invoice_path = os.path.join(user_dir,"INV-{}{}.pdf".format(customer_id,policy_record.id))
        contract_path = os.path.join(user_dir,"contrat_{}_{}.pdf".format(customer_id,policy_record.id))
        signature_path = os.path.join(settings.BASE_DIR,"signature.png")
        signature_add(invoice_path,signature_path,3000,950,0.6,0.9) 
        signature_add(contract_path,signature_path,3100,1200,0.6,0.9) 
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
        'available_policy':CMODEL.Policy.objects.all().count(),
        'applied_policy':CMODEL.PolicyRecord.objects.all().filter(customer=models.Customer.objects.get(user_id=request.user.id)).count(),
        'total_category':CMODEL.Category.objects.all().count(),
        'total_question':CMODEL.Question.objects.all().filter(customer=models.Customer.objects.get(user_id=request.user.id)).count(),
        "segment":"customer-dashboard",

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
    policies = CMODEL.PolicyRecord.objects.all().filter(customer=customer)
    cards = CMODEL.Card.objects.all().filter(customer=customer)
    try:
        newest_card = CMODEL.Card.objects.filter(customer=customer).latest('creation_time')
    except:
        newest_card = None
    return render(request,'home/billing.html',{'segment':"billing",'policies':policies,'newest_card':newest_card,'cards':cards,'customer':customer}) 

@login_required(login_url='login')
def apply_policy_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policies = CMODEL.Policy.objects.all()
    return render(request,'home/generate_contract.html',{'policies':policies,'customer':customer,'segment':"apply-policy"})

@login_required(login_url='login')
def apply_view(request,pk):
    if request.method=='POST':
        customer = models.Customer.objects.get(user_id=request.user.id)
        policy = CMODEL.Policy.objects.get(id=pk)
        policyrecord = CMODEL.PolicyRecord()
        policyrecord.Policy = policy
        policyrecord.customer = customer
        user_dir = os.path.join(settings.MEDIA_ROOT, "customer_{}".format(request.user.id))
        os.makedirs(user_dir,exist_ok=True)
        try:
            file_path = os.path.join(r'C:\Users\MSI', 'Downloads') ##### change your path here
            cin_recto = request.FILES[u'cin_recto']
            cinrecto = cv2.imread(os.path.join(file_path, cin_recto._get_name()))
            cinrecto_path = os.path.join(user_dir,"cin_recto_{}.jpg".format(request.user.id))
            cv2.imwrite(cinrecto_path,cinrecto)
            cin_verso = request.FILES[u'cin_verso']
            cinverso = cv2.imread(os.path.join(file_path, cin_verso._get_name()))
            cinverso_path = os.path.join(user_dir,"cin_verso_{}.jpg".format(request.user.id))
            cv2.imwrite(cinverso_path,cinverso)
            carte_grise = request.FILES[u'carte_grise']
            cartegriserecto = cv2.imread(os.path.join(file_path, carte_grise._get_name()))
            cartegriserecto_path = os.path.join(user_dir,"carte_grise_recto_{}.jpg".format(request.user.id))
            cv2.imwrite(cartegriserecto_path,cartegriserecto)
            carte_grise_verso = request.FILES[u'carte_grise_verso']
            cartegriseverso = cv2.imread(os.path.join(file_path, carte_grise_verso._get_name()))
            cartegriseverso_path = os.path.join(user_dir,"carte_grise_verso_{}.jpg".format(request.user.id))
            cv2.imwrite(cartegriseverso_path,cartegriseverso)
        except MultiValueDictKeyError:
            try:
                cinrecto = cv2.imread(os.path.join(user_dir,"cin_recto_{}.jpg".format(request.user.id)))
                cinverso = cv2.imread(os.path.join(user_dir,"cin_verso_{}.jpg".format(request.user.id)))
                cartegriserecto = cv2.imread(os.path.join(user_dir,"carte_grise_recto_{}.jpg".format(request.user.id)))
                cartegriseverso = cv2.imread(os.path.join(user_dir,"carte_grise_verso_{}.jpg".format(request.user.id)))
                if cinrecto is None or cinverso is None or cartegriserecto is None or cartegriseverso is None:
                    raise FileNotFoundError
            except FileNotFoundError:
                return redirect('apply-policy')
        cinrecto_path = os.path.join(user_dir,"cin_recto_{}.jpg".format(request.user.id))
        cinverso_path = os.path.join(user_dir,"cin_verso_{}.jpg".format(request.user.id))
        cartegriserecto_path = os.path.join(user_dir,"carte_grise_recto_{}.jpg".format(request.user.id))
        cartegriseverso_path = os.path.join(user_dir,"carte_grise_verso_{}.jpg".format(request.user.id))
        angle, rotated = correct_orientation(cinrecto)
        cv2.imwrite('rotated.png', rotated)
        ### face detection and virtual contour
        try :
            subprocess.call('curl -H "apikey:K86104006488957" -o "processed.json" --form "detectOrientation=true" --form "file=@rotated.png" --form "language=ara" --form "isOverlayRequired=true" --form "isCreateSearchablePdf=true" --form "scale=true" "https://api.ocr.space/Parse/Image"',timeout=1,shell=True)
            with open('processed.json', encoding='utf-8') as f:
                data=json.load(f)
        except subprocess.TimeoutExpired :
            data = []
        # Load the cascade
        face_cascade = cv2.CascadeClassifier('haar.xml')
        # Read the input image
        img = cv2.imread('rotated.png')
        # Convert into grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        # Draw rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
        try :
            l = len(data['ParsedResults'][0]['TextOverlay']['Lines'])
            top = [int(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'][0]['Top']) for i in range(l)]
            left = [int(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'][0]['Left']) for i in range(l)]
        except (IndexError, KeyError, TypeError):
            print("Server not responding...\nTrying another method")
            results=arabicocr.arabic_ocr('rotated.png','arabicocr_output.png')
            top = [int(results[i][0][0][1]) for i in range(len(results))]
            left = [int(results[i][0][0][0]) for i in range(len(results))]
        max_top, max_left = max(top), max(left)
        img_arr = np.array(img)
        img_arr = img_arr[y-int(h/2)-10 : max_top+10, x+w : max_left]
        angle, img_arr = correct_orientation(img_arr)
        # Display the output
        cv2.imwrite('processed.png',img_arr)
        ### threshold
        imgFloat = img_arr.astype(np.float) / 255.
        kChannel = 1 - np.max(imgFloat, axis=2)
        kChannel = (255 * kChannel).astype(np.uint8)
        binaryThresh = 135
        _, binaryImage = cv2.threshold(kChannel, binaryThresh, 255, cv2.THRESH_BINARY)
        cv2.imwrite('binary.png',binaryImage)
        ### extract information
        try:
            subprocess.call('curl -H "apikey:K86104006488957" -o "processed.json" --form "detectOrientation=true" --form "file=@processed.png" --form "language=ara" --form "isOverlayRequired=true" --form "isCreateSearchablePdf=true" --form "scale=true" "https://api.ocr.space/Parse/Image"',timeout=1,shell=True)
            with open('processed.json', encoding='utf-8') as f:
                data=json.load(f)
        except subprocess.TimeoutExpired :
            data = []
        recto = []
        try :
            l = len(data['ParsedResults'][0]['TextOverlay']['Lines'])
            for i in range(l):
                line = data['ParsedResults'][0]['TextOverlay']['Lines'][i]['LineText']
                recto.append(line)
        except (IndexError, KeyError, TypeError) :
            print("Server not responding...\nTrying another method")
            results=arabicocr.arabic_ocr('binary.png','arabicocr_output.png')
            text = correct_ocr_order(results,18)
            recto = [text[i][0] for i in range(len(text))]
        cin = arabic_reshaper.reshape(correct_ocr_output(recto[0]))
        try:
            s = recto[2]
        except :
            _, binaryImage = cv2.threshold(kChannel, binaryThresh+20, 255, cv2.THRESH_BINARY)
            cv2.imwrite('binary.png',binaryImage)
            results=arabicocr.arabic_ocr('binary.png','arabicocr_output.png')
            text = correct_ocr_order(results)
            recto = [text[i][0] for i in range(len(text))]
        try:
            fname, lname = correct_ocr_output(recto[2].replace("ى","ي")), correct_ocr_output(recto[1].replace("ى","ي"))
            nom = arabic_reshaper.reshape(auto_correction_word(fname,'model_first_name','first_name.csv')) + ' ' + arabic_reshaper.reshape(auto_correction_word(lname,'model_last_name','last_name.csv'))
        except:
            nom = correct_ocr_output(recto[1].replace("ى","ي"))
            nom = arabic_reshaper.reshape(auto_correction_word(nom,'model_first_name','first_name.csv'))
        ######### CIN verso ###########
        angle, rotated = correct_orientation(cinverso)
        cv2.imwrite('rotated.png', rotated)
        img_arr = np.array(cinverso)
        ### virtual contour
        try:
            subprocess.call('curl -H "apikey:K86104006488957" -o "processed1.json" --form "detectOrientation=true" --form "file=@rotated.png" --form "language=ara" --form "isOverlayRequired=true" --form "isCreateSearchablePdf=true" --form "scale=true" "https://api.ocr.space/Parse/Image"',timeout=1,shell=True)
            with open('processed1.json', encoding='utf-8') as f:
                data=json.load(f)
        except subprocess.TimeoutExpired :
            data = []
        #gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        try :
            l = len(data['ParsedResults'][0]['TextOverlay']['Lines'])
            top = [int(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'][len(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'])-1]['Top']) for i in range(l)]
            left = [int(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'][len(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'])-1]['Left']) for i in range(l)]
        except :
                results=arabicocr.arabic_ocr(cinverso_path,'arabicocr_output.png')
                top, left = [], []
                for i in range(len(results)):
                    for j in range(4):
                        top.append(int(results[i][0][j][1]))
                        left.append(int(results[i][0][j][0]))
        max_top, max_left, min_top, min_left = max(top), max(left), min(top), min(left)
        img_arr = img_arr[min_top : max_top, min_left : max_left]
        # Display the output
        cv2.imwrite('processed1.jpg',img_arr)
        ### threshold
        imgFloat = img_arr.astype(np.float) / 255.
        kChannel = 1 - np.max(imgFloat, axis=2)
        kChannel = (255 * kChannel).astype(np.uint8)
        binaryThresh = 120
        _, binaryImage = cv2.threshold(kChannel, binaryThresh, 255, cv2.THRESH_BINARY)
        cv2.imwrite('binary1.jpg',binaryImage)
        ### extract information
        try:
            subprocess.call('curl -H "apikey:K86104006488957" -o "processed1.json" --form "detectOrientation=true" --form "file=@binary1.jpg" --form "language=ara" --form "isOverlayRequired=true" --form "isCreateSearchablePdf=true" --form "scale=true" "https://api.ocr.space/Parse/Image"',timeout=1,shell=True)
            with open('processed1.json', encoding='utf-8') as f:
                data=json.load(f)
        except subprocess.TimeoutExpired :
            data = []
        verso = []
        try :
            l = len(data['ParsedResults'][0]['TextOverlay']['Lines'])
            for i in range(l):
                line = data['ParsedResults'][0]['TextOverlay']['Lines'][i]['LineText']
                verso.append(line)
        except (IndexError, KeyError, TypeError) :
            results=arabicocr.arabic_ocr('binary1.jpg','arabicocr_output.png')
            text = correct_ocr_order(results)
            verso = [text[i][0] for i in range(len(text))]
            print(verso)
        profession = arabic_reshaper.reshape(auto_correction_word(verso[1],'model_job_name','job_name.csv'))
        try:
            adresse = arabic_reshaper.reshape(correct_ocr_output(verso[2])) + '\n' + arabic_reshaper.reshape(correct_ocr_output(verso[3]))
        except IndexError:
            adresse = arabic_reshaper.reshape(correct_ocr_output(verso[2]))
        print(profession+'\n'+adresse)
        ############ carte grise recto #############
###################################### CROPPING################################
        gr=cartegriserecto
        height, width, selected, flag_height = gr.shape[0], gr.shape[1], False, 0
        image = cv2.cvtColor(gr, cv2.COLOR_BGR2HSV)
        lower1, upper1, lower2, upper2 = np.array([0, 100, 20]), np.array([10, 255, 255]), np.array([160,100,20]), np.array([179,255,255])
        lower_mask, upper_mask = cv2.inRange(image, lower1, upper1), cv2.inRange(image, lower2, upper2)
        contours, hierarchy = cv2.findContours(lower_mask + upper_mask,cv2.RETR_TREE,  cv2.CHAIN_APPROX_SIMPLE)
        h, w = gr.shape[:2]
        thresh_area, list_contours = 0.001, []
        for c in contours:
            area = cv2.contourArea(c)
            if (area > thresh_area*h*w): 
                rect_page = cv2.minAreaRect(c)
                box_page = np.int0(cv2.boxPoints(rect_page))
                list_contours.append(box_page)		
        sorted_contours= sorted(list_contours, key=cv2.contourArea, reverse= True)
        for (i,c) in enumerate(sorted_contours):
            x,y,w,h= cv2.boundingRect(c)
            if(w>h)&(h*2>w)&(h<800)&(w<800)&(x>0)&(y>0)&(x+w<=width)&(y+h<=height)&(selected==False):
                cropped_contour= gr[y:y+h, x:x+w]
                pixels, n_colors, criteria, flags  = np.float32(cropped_contour.reshape(-1, 3)), 7, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1), cv2.KMEANS_RANDOM_CENTERS
                _, labels, palette = cv2.kmeans(pixels, n_colors, None, criteria, 10, flags)
                _, counts = np.unique(labels, return_counts=True)
                dominant = palette[np.argmax(counts)]
                if(dominant[1]*1.8<dominant[2]):
                    selected=True
                    Bottom, Top, flag_height = round(y+h*8.2), round(y-h*0.5), h
                    Top = 0 if Top<0 else Top
                    Bottom = height if Bottom>height else Bottom
                    if(x>width*3/4):
                        Left, Right = round(x-w*9), round(x-w*7.3)
                    else:
                        Left, Right = round(x-w*5.5), round(x-w*3.8)
                    Left = 0 if Left<0 else Left
                    Right = width if Right>width else Right	    
                    final_pic=gr[Top:Bottom,Left:Right]
        #################################ROTATING#########################
        rot = cv2.rotate(final_pic, cv2.cv2.ROTATE_90_CLOCKWISE)
        cv2.imwrite('rot90.jpg',rot)
        ################################### READING########################
        reader = Reader(['ar','en','fa'], gpu = False)
        bounds = reader.readtext('rot90.jpg')	
        ###################################
        tab, i, added = [[] for i in range (6)], 0, [1,1,1,1,1,1]
        for h in range(0,6,1):
            while (len(bounds)!=0) & (added[h]==1):
                added[h]=0
                p0, p1, p2, p3 = bounds[0][0]
                x0, y0 = math.floor(p0[0]), math.floor(p2[1])
                x, y, k, j = x0, y0, 0, 0
                while j<len(bounds):
                    pj0, pj1, pj2, pj3 = bounds[j][0]
                    xj0, yj0, yj0_t = math.floor(pj0[0]), math.floor(pj2[1]), math.floor(pj0[1])
                    if(y<=yj0):
                        k, y, x, y0 = j, yj0, xj0, yj0_t
                    j+=1
                if((len(tab[h])==0)& ((y-y0)>=(flag_height/2))):	
                    tab[h].append(bounds[k])
                    bounds.remove(bounds[k])
                    added[h]=1
                elif((len(tab[h])==0)):	
                    bounds.remove(bounds[k])
                    added[h]=1			
                else:
                    pk0, pk1, pk2, pk3 = tab[h][0][0]			
                    yk0=math.floor(pk2[1])
                    if ((y<=yk0+37) & (y>=yk0-37) & ((y-y0)>=(flag_height/2))):
                        tab[h].append(bounds[k])
                        bounds.remove(bounds[k])
                        added[h]=1	
        ########### SORTING##############			
            i, j = 0, 0
            while i < len(tab[h]):
                j=i+1
                p0, p1, p2, p3 = tab[h][i][0]
                x0=math.floor(p0[0])
                while j< len(tab[h]):
                    pj0, pj1, pj2, pj3 = tab[h][j][0]
                    xj0=math.floor(pj0[0])
                    if(x0>xj0):
                        t=tab[h][i]
                        tab[h][i]=tab[h][j]
                        tab[h][j]=t
                    j+=1
                i+=1	
        try:
            serie = str(int(tab[0][0][1])) + " TU " + str(int(tab[0][len(tab[0])-1][1]))
        except:
            serie=""
        gr = cartegriserecto
        height, width, selected = gr.shape[0], gr.shape[1], False
        image = cv2.cvtColor(gr, cv2.COLOR_BGR2HSV)
        lower1, upper1, lower2, upper2 = np.array([0, 100, 20]), np.array([10, 255, 255]), np.array([160, 100, 20]), np.array([179, 255, 255])
        lower_mask, upper_mask = cv2.inRange(image, lower1, upper1), cv2.inRange(image, lower2, upper2)
        contours, hierarchy = cv2.findContours(lower_mask+upper_mask, cv2.RETR_TREE,  cv2.CHAIN_APPROX_SIMPLE)
        h, w = gr.shape[:2]
        thresh_area, list_contours = 0.001, list()
        for c in contours:
            area = cv2.contourArea(c)
            if (area > thresh_area*h*w):
                rect_page = cv2.minAreaRect(c)
                box_page = np.int0(cv2.boxPoints(rect_page))
                list_contours.append(box_page)
        sorted_contours = sorted(list_contours, key=cv2.contourArea, reverse=True)
        for (i, c) in enumerate(sorted_contours):
            x, y, w, h = cv2.boundingRect(c)
            if(w > h) & (h*2 > w) & (h < 800) & (w < 800) & (x > 0) & (y > 0) & (x+w <= width) & (y+h <= height) & (selected == False):
                cropped_contour = gr[y:y+h, x:x+w]
                pixels = np.float32(cropped_contour.reshape(-1, 3))
                n_colors = 7
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
                _, labels, palette = cv2.kmeans(pixels, n_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
                _, counts = np.unique(labels, return_counts=True)
                dominant = palette[np.argmax(counts)]
                if(dominant[1]*1.8 < dominant[2]):
                    selected = True
                    Top = round(y+h*1.1)
                    Bottom = round(y+h*8.2)
                    Bottom = height if Bottom>height else Bottom
                    Left = round(x-w*4.3)
                    Left = 0 if Left<0 else Left
                    Right = round(x+w*4.5)
                    Right = width if Right>width else Right
                    final_pic = gr[Top:Bottom, Left:Right]
                    cv2.imwrite('zoomed_carte_grise.jpg', final_pic)
        img_arr = np.array(final_pic)
        try:
            subprocess.call('curl -H "apikey:K86104006488957" -o "processed2.json" --form "detectOrientation=true" --form "file=@zoomed_carte_grise.jpg" --form "language=ara" --form "isOverlayRequired=true" --form "isCreateSearchablePdf=true" --form "scale=true" "https://api.ocr.space/Parse/Image"',timeout=1,shell=True)
            with open('processed2.json', encoding='utf-8') as f:
                data=json.load(f)
        except subprocess.TimeoutExpired :
            data = []
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        try :
            l = len(data['ParsedResults'][0]['TextOverlay']['Lines'])
            top = [int(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'][len(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'])-1]['Top']) for i in range(l)]
            left = [int(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'][len(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'])-1]['Left']) for i in range(l)]
            max_top, max_left, min_top, min_left = max(top)+30, max(left), int(max(top)/2), min(left)-10
            img_arr = img_arr[min_top : max_top, min_left : max_left]
        except :
            print("Server did not respond")
            img_arr = img_arr[int(img_arr.shape[0]/2) : img_arr.shape[0], 0 : img_arr.shape[1]]
        # Display the output
        cv2.imwrite('processed1.jpg',img_arr)
        ### OCRing
        with open('brands.json','r', encoding='utf-8') as f:
            brands_json=json.load(f)
        f.close()
        brands = [[brands_json['RECORDS'][i]['id'],brands_json['RECORDS'][i]['name']] for i in range(len(brands_json['RECORDS']))]
        with open('automobiles.json','r', encoding='utf-8') as f:
            data=json.load(f)
        f.close()
        date_pattern = '^([0-9][0-9]|19[0-9][0-9]|20[0-9][0-9])(\.|-|/)([1-9]|0[1-9]|1[0-2])(\.|-|/)([1-9]|0[1-9]|1[0-9]|2[0-9]|3[0-1])$'
        serie_type, dpmc,constructeur,modele = '', '','',''
        langs = "ar,en".split(",")
        reader = Reader(langs, gpu=-1 > 0)
        results = reader.readtext(img_arr)
        for (bbox, text, prob) in results:
            if any(x.isalpha() for x in text) and any(x.isnumeric() for x in text) and len(text)>14 and len(text)<18:
                serie_type = correct_ocr_output(text)
            if re.match(date_pattern, text):
                dpmc = text
            for i in range(len(brands)):
                if Levenshtein.ratio(brands[i][1].lower(),correct_ocr_output(text).lower())>0.65:
                    constructeur=brands[i][1].upper()
                    id_marque = brands[i][0]
            autos = [data['RECORDS'][i] for i in range(len(data['RECORDS'])) if constructeur in data['RECORDS'][i]['name'].split(' ')]
            for i in range(len(autos)):
                try:
                    presse = autos[i]['press_release'].split(' ')
                except AttributeError:
                    continue
                for j in range(len(presse)):
                    if Levenshtein.ratio(presse[j].lower(),text.lower())>0.8 and Levenshtein.ratio(presse[j].upper(),constructeur)<0.5:
                        modele = presse[j].upper()
                if(modele==''):
                    try:
                        presse = autos[i]['description'].split(' ')
                    except AttributeError:
                        pass
                    for j in range(len(presse)):
                        if Levenshtein.ratio(presse[j].lower(),text.lower())>0.8 and Levenshtein.ratio(presse[j].upper(),constructeur)<0.5:
                            modele = correct_ocr_output(presse[j].upper())
        with open('car_brands.json','r', encoding='utf-8') as f:
            logos=json.load(f)
        f.close()
        for i in range(len(logos)):
            if logos[i]['name'].upper()==constructeur:
                logo = logos[i]['logo']
                break
        ######## carte grise verso #########
        img_arr=np.array(cartegriseverso)
        angle, img_arr = correct_orientation(img_arr)
        cv2.imwrite('carte_grise_verso.jpg',img_arr)
        try:
            subprocess.call('curl -H "apikey:K86104006488957" -o "processed3.json" --form "detectOrientation=true" --form "file=@carte_grise_verso.jpg" --form "language=ara" --form "isOverlayRequired=true" --form "isCreateSearchablePdf=true" --form "scale=true" "https://api.ocr.space/Parse/Image"',timeout=1,shell=True)
            with open('processed3.json', encoding='utf-8') as f:
                data=json.load(f)
        except subprocess.TimeoutExpired :
            data = []
        try :
            l = len(data['ParsedResults'][0]['TextOverlay']['Lines'])
            top = [int(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'][len(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'])-1]['Top']) for i in range(l)]
            left = [int(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'][len(data['ParsedResults'][0]['TextOverlay']['Lines'][i]['Words'])-1]['Left']) for i in range(l)]
            max_top, max_left, min_top, min_left = int(2*max(top)/3), max(left), min(top), min(left)
            img_arr = img_arr[min_top : max_top, min_left : max_left]
        except :
            print("Server did not respond")
            img_arr = img_arr[0 : int(2*img_arr.shape[0]/3), 0 : ]
        # Display the output
        angle, img_arr = correct_orientation(img_arr)
        img_arr = thresholding(remove_noise(grayscale(img_arr)))
        gauche = img_arr[0 : int(img_arr.shape[0]/4), 0 : int(img_arr.shape[1]/2)]
        droite = img_arr[0 : int(img_arr.shape[0]/2), int(2*img_arr.shape[1]/3) : ]
        cv2.imwrite('droite.jpg',droite)
        g_config, d_config = r'--oem 3 --psm 6', r'-l eng --oem 3 --psm 6'
        places,puissance_fiscale,energie=0,0,"بنزين"
        g = pytesseract.image_to_data(gauche, config=g_config, output_type=Output.DICT)
        for i in range(len(g['text'])):
            if re.match(r"[+-]?\d+(?:\.\d+)?",g['text'][i]):
                places = int(g['text'][i])
                break
        d = pytesseract.image_to_data(droite, config=d_config, output_type=Output.DICT)
        for i in range(len(d['text'])):
            if re.match(r"[+-]?\d+(?:\.\d+)?",d['text'][i]) and all(x.isdigit() for x in d['text'][i]) and int(d['text'][i])>3 and int(d['text'][i])<50:
                puissance_fiscale = int(d['text'][i])
                break
        results=arabicocr.arabic_ocr('droite.jpg','arabicocr_output.png')
        for i in range(len(results)):
            if Levenshtein.ratio(results[i][1],"غازوال")>0.6:
                energie="غازوال"
        if not CMODEL.Car.objects.all().filter(owner=customer,serie=serie):
            car = CMODEL.Car(owner=customer,serie=serie,brand=constructeur,name=modele,dpmc=dpmc.replace("/","-"),brand_logo=logo,nb_places=places,puissance_fiscale=puissance_fiscale,energie="Essence" if energie=="بنزين" else "Gasoil")
            car.save()
        else:
            CMODEL.Car.objects.all().filter(owner=customer,serie=serie).update(brand=constructeur,name=modele,dpmc=dpmc.replace("/","-"),brand_logo=logo,nb_places=places,puissance_fiscale=puissance_fiscale,energie="Essence" if energie=="بنزين" else "Gasoil")
        ######### contract #########
        if not CMODEL.PolicyRecord.objects.all().filter(customer=customer) or True:
            policyrecord.save()
            font2 = ImageFont.truetype("arial.ttf", 16, encoding="utf-8")
            font = ImageFont.truetype("arial.ttf", 20, encoding="utf-8")
            text_width, text_height = font.getsize(nom)
            canvas = Image.open(os.path.join(settings.BASE_DIR,"contrat.jpg"))
            canvas=canvas.convert('RGB')
            draw = ImageDraw.Draw(canvas)
            draw.text((400, 615), cin, 'black', font)
            draw.text((400, 745), cin, 'black', font)
            draw.text((400, 540), nom, 'black', font)
            draw.text((400, 570), adresse, 'black', font)
            draw.text((400, 703), adresse, 'black', font)
            draw.text((400, 770), profession, 'black', font)
            draw.text((400, 685), nom, 'black', font)
            draw.text((400, 865), serie_type, 'black', font2)
            draw.text((400, 981), dpmc, 'black', font2)
            draw.text((400, 829), constructeur, 'black', font2)
            draw.text((400, 848), modele, 'black', font2)
            draw.text((400, 895), serie, 'black', font2)
            draw.text((400, 928), "Essence" if energie=="بنزين" else "Gasoil", 'black', font2)
            draw.text((400, 945), str(puissance_fiscale), 'black', font2)
            draw.text((400, 962), str(places), 'black', font2)
            inv = Image.open(os.path.join(settings.BASE_DIR,"invoice.png"))
            inv=inv.convert('RGB')
            draw = ImageDraw.Draw(inv)
            draw.text((600, 450), "{} DT".format(policy.sum_assurance), 'black', font)
            draw.text((585, 740), "{} DT".format(policy.sum_assurance), 'black', font)
            draw.text((485, 315), request.user.first_name, 'black', font)
            draw.text((555, 315), request.user.last_name, 'black', font)
            draw.text((585, 768), "{:.2f} DT".format(0.06*policy.sum_assurance), 'black', font)
            draw.text((485, 340), customer.address, 'black', font)
            draw.text((150, 300), "INV-{}{}".format(request.user.id,policyrecord.id), 'black', font)
            draw.text((150, 320), str(policyrecord.creation_date), 'black', font)
            draw.text((145, 450), str(policy), 'black', font)
            draw.text((400, 450), "{} DT".format(policy.sum_assurance), 'black', font)
            draw.text((520, 450), "1", 'black', font)
            draw.text((585, 795), "{:.2f} DT".format(1.06*policy.sum_assurance), 'black', font)   
            contract_path = os.path.join(user_dir,"contrat_{}_{}.pdf".format(request.user.id,policyrecord.id))
            canvas.save(contract_path)
            invoice_path = os.path.join(user_dir,"INV-{}{}.pdf".format(request.user.id,policyrecord.id))
            inv.save(invoice_path)                              
            
    return redirect('contracts')

def delete_contract_view(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policy_record = CMODEL.PolicyRecord.objects.get(customer=customer,id=pk)
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
    policies = CMODEL.PolicyRecord.objects.all().filter(customer=customer)
    cars = CMODEL.Car.objects.all().filter(owner=customer)
    return render(request,'home/tables.html',{'cars':cars,'policies':policies,'customer':customer,'segment':"contracts"})

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
    return render(request,'home/my-questions.html',{'questionForm':questionForm,'questions':questions,'customer':customer,'segment':"question-history"})


def download_file(request,pk):
    filename = "contrat_{}_{}.pdf".format(request.user.id,pk)
    filepath = settings.BASE_DIR + '\\static\\' + "customer_{}\\".format(request.user.id) + filename
    fl = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filename)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

def download_invoice(request,pk):
    filename = "INV-{}{}.pdf".format(request.user.id,pk)
    filepath = settings.BASE_DIR + '\\static\\' + "customer_{}\\".format(request.user.id) + filename
    fl = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filename)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response