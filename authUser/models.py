from django.db import models

# Create your models here.
from django.contrib.auth.models import (

			AbstractBaseUser,
			PermissionsMixin,
			BaseUserManager,
	)
from django.forms import ValidationError
import random
import uuid
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):

	def create_user(self,phone,password=None,is_internal=False):
		if phone is not None:
			user = self.model(phone=phone)
		else:
			raise ValidationError("Phone number required.")

		if password is not None:
			user.set_password(password)
		if is_internal:
			user.is_internal=True


		user.save(using=self._db)
		return user

	def create_superuser(self,phone,password=None,is_internal=True):
		user = self.create_user(phone,password,is_internal=True)
		user.is_superuser = True
		user.is_staff = True
		user.is_active = True
		user.save(using=self._db)
		return user



class Users(AbstractBaseUser,PermissionsMixin):
	# uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
	uid = models.CharField(max_length=255,unique=True,default=uuid.uuid4,db_index=True)
	email = models.EmailField(max_length=225,null=True)
	phone = models.CharField(max_length=12,unique=True)
	otp_code = models.CharField(max_length=6,null=True)
	otp_expiration_time = models.DateTimeField(null=True)
	phone_verified = models.BooleanField(default=False)
	email_verified = models.BooleanField(default=False)
	# is_completed = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	is_internal = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	objects = UserManager()

	USERNAME_FIELD = "phone"

	def return_future_time(self):
		now = timezone.now()
		return now + timedelta(minutes=3)

	def save(self,*args,**kwargs):
		code = []
		for i in range(6):
			code.append(random.choice(range(1,9)))

		self.otp_code = "".join([str(x) for x in code])
		self.otp_expiration_time = self.return_future_time()
		super().save(*args,**kwargs)


	class Meta:
		verbose_name_plural = 'Users'


	def __str__(self):
		return f'{self.email}--{self.phone}'



class User_Signups(models.Model):
	phone = models.CharField(max_length=12,unique=True)
	otp_code = models.CharField(max_length=6,null=True)
	otp_expiration_time = models.DateTimeField(null=True)
	verified = models.BooleanField(default=False)

	def return_future_time(self):
		now = timezone.now()
		return now + timedelta(minutes=3)


	def save(self,*args,**kwargs):
		code = []
		for i in range(6):
			code.append(random.choice(range(1,9)))

		self.otp_code = "".join([str(x) for x in code])
		self.otp_expiration_time = self.return_future_time()
		super().save(*args,**kwargs)

	class Meta:
		verbose_name_plural = "User Sign Ups"

	def __str__(self):
		return f'{self.phone}-{self.otp_expiration_time}'


class Person_Interests_List(models.Model):
	name = models.CharField(max_length=255,unique=True)

	class Meta:
		verbose_name_plural = "Person Intersts List"

	def __str__(self):
		return f'{self.name}'