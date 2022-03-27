from django.db import models
from django.contrib.auth.models import User
from customer.models import Customer
class Category(models.Model):
    category_name =models.CharField(max_length=20)
    creation_date =models.DateField(auto_now=True)
    def __str__(self):
        return self.category_name

class Policy(models.Model):
    category= models.ForeignKey('Category', on_delete=models.CASCADE)
    policy_name=models.CharField(max_length=200)
    sum_assurance=models.PositiveIntegerField()
    premium=models.PositiveIntegerField()
    tenure=models.PositiveIntegerField()
    creation_date =models.DateField(auto_now=True)
    def __str__(self):
        return self.policy_name
    class Meta:
        ordering = ['-creation_date']

class Purchase(models.Model):
    customer_full_name= models.ForeignKey(Customer, on_delete=models.CASCADE)

    policy = models.ForeignKey(to=Policy, on_delete=models.CASCADE)
    PAYMENT_METHODS = [

        ('DC', 'Stripe'),
        ('ET', 'Paypal'),
        ('BC', 'Ethereum'),
    ]
    payment_method = models.CharField(max_length=2, default='CC', choices=PAYMENT_METHODS)
    time = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)

    class Meta:
        ordering = ['-time']

    def __str__(self):
        return f'{self.customer_full_name}, {self.payment_method} ({self.policy.policy_name})'

class PolicyRecord(models.Model):
    customer= models.ForeignKey(Customer, on_delete=models.CASCADE)
    Policy= models.ForeignKey(Policy, on_delete=models.CASCADE)
    status = models.CharField(max_length=100,default='Pending')
    creation_date =models.DateField(auto_now=True)
    def __str__(self):
        return self.policy

class Question(models.Model):
    customer= models.ForeignKey(Customer, on_delete=models.CASCADE)
    description =models.CharField(max_length=500)
    admin_comment=models.CharField(max_length=200,default='')
    asked_date =models.DateField(auto_now=True)
    def __str__(self):
        return self.description

class Car(models.Model):
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE)
    brand = models.CharField(max_length=50)
    brand_logo = models.CharField(max_length=500,null=True)
    serie = models.CharField(max_length=20,null=True)
    name = models.CharField(max_length=50)
    puissance_fiscale = models.PositiveIntegerField(null=True)
    nb_places = models.PositiveIntegerField(null=True)
    dpmc = models.DateField()
    energie = models.CharField(max_length=20,null=True)
    def __str__(self):
        return self.brand + " " + self.name

class Card(models.Model):
    customer= models.ForeignKey(Customer, on_delete=models.CASCADE)
    holder = models.CharField(max_length=50,null=True)
    brand = models.CharField(max_length=20,null=True)
    last4 = models.PositiveIntegerField(null=True)
    exp_month = models.PositiveIntegerField(null=True)
    exp_year = models.PositiveIntegerField(null=True)
    creation_time =models.DateTimeField(auto_now=True)

# Create your models here.
class Invoice(models.Model):
    customer = models.CharField(max_length=100)
    customer_email = models.EmailField(null=True, blank=True)
    billing_address = models.TextField(null=True, blank=True)
    date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    message = models.TextField(default="this is a default message.")
    total_amount = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return str(self.customer)

    def get_status(self):
        return self.status

    # def save(self, *args, **kwargs):
    # if not self.id:
    #     self.due_date = datetime.datetime.now()+ datetime.timedelta(days=15)
    # return super(Invoice, self).save(*args, **kwargs)

#class Transaction(models.Model):
  #  amount = models.FloatField()
  #  seller = models.ForeignKey(User, related_name='sells', on_delete=models.CASCADE)
  #  buyer = models.ForeignKey(User, related_name='purchased', on_delete=models.CASCADE)
   # created_at_date = models.DateField(auto_now_add=True)
class InvoiceRecod(models.Model):
    customer = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    service = models.TextField()
    description = models.TextField()
    quantity = models.IntegerField()
    rate = models.DecimalField(max_digits=9, decimal_places=2)
    amount = models.DecimalField(max_digits=9, decimal_places=2)


    def __str__(self):
        return str(self.customer)