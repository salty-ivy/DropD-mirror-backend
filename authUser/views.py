from django.shortcuts import render,redirect

# Create your views here.
from authUser.models import *
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.decorators import api_view , authentication_classes ,permission_classes
from rest_framework.authentication import TokenAuthentication

## JWT ###
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.backends import TokenBackend

from authUser.serializers import *
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from neoUserModel.models import *
from rest_framework import status
from django.utils import timezone
from datetime import timedelta , datetime
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.mail import send_mail
import re
from .cypher_queries_utility import *

from .helper import *
# import asyncio
from django.contrib.auth import login,logout
from django.contrib.auth.decorators import login_required
from uuid import uuid4


class SignUp(APIView):
	def post(self,request,*args,**kwargs):
		phone = request.data.get('phone')
		if phone is None:
			return Response({
					'status':'Error',
					'message':'Phone number required.'
				})
		if User_Signups.objects.filter(phone=phone).exists():
			phone = User_Signups.objects.get(phone=phone)
			if not phone.verified:
				phone.save()
				formatted_phone_number = "+"+str(phone.phone)
				msg = f"DropD signup OTP {phone.otp_code}"
				sendSMS(formatted_phone_number,msg)
				return Response({
						'status':'success',
						'message':f'OTP sent to {phone.phone}.',
					},status=status.HTTP_200_OK)
		if Users.objects.filter(phone=phone).exists():
			user = Users.objects.get(phone=phone)
			if user.phone_verified:
				if user.email_verified:
					if user.is_completed:
						return Response({
								'status':'error',
								'message':'User already exists.',
							},status=status.HTTP_226_IM_USED)
					return Response({
							'success':'error',
							'message':'User already exists.',
							'profile_completed':False,
						},status=status.HTTP_406_NOT_ACCEPTABLE)

				return Response({
						'status':'error',
						'message':'User already exists.',
						'email_verified':False,
					},status=status.HTTP_406_NOT_ACCEPTABLE)
			return Response({
					'status':'error',
					'message':'User already exists.',
					'phone_verified':False,
				},status=status.HTTP_406_NOT_ACCEPTABLE)

		phoneObject = User_Signups.objects.create(phone=phone)
		formatted_phone_number = "+"+str(phoneObject.phone)
		msg = f"DropD signup OTP {phoneObject.otp_code}"
		sendSMS(formatted_phone_number,msg)
		return Response({
				'status':'success',
				'message':f'OTP sent to {phoneObject.phone}.',
			},status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
def signupVerification(request):
	otp = request.data.get('otp')
	phone = request.data.get('phone')

	if otp is None:
		return Response({
				'status':'error',
				'message':'OTP required.',
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	if phone is None:
		return Response({
				'status':'error',
				'message':'Phone number required'
			},status=status.HTTP_406_NOT_ACCEPTABLE)

	try:
		phoneObject = User_Signups.objects.get(phone=phone)
	except:
		if Users.objects.filter(phone=phone).exists():
			return Response({
					'status':'error',
					'message':'User already exits.'
				},status=status.HTTP_226_IM_USED)
		else:
			return Response({
					'status':'error',
					'message':'Wrong phone number.'
				},status=status.HTTP_406_NOT_ACCEPTABLE)

	if timezone.now() <= phoneObject.otp_expiration_time:
		if phoneObject.otp_code == otp:
			phoneObject.verified = True
			phoneObject.save()
			user = Users.objects.create(phone=phoneObject.phone)
			user.phone_verified = True
			user.save()
			token = Token.objects.get(user=user).key
			phoneObject.delete()
			return Response({
					'status':'success',
					'message':'User created.',
					'token':token,
				},status=status.HTTP_201_CREATED)
		return Response({
				'status':'error',
				'message':'Incorrect otp.',
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	return Response({
			'status':'error',
			'message':'OTP expired.',
		},status=status.HTTP_406_NOT_ACCEPTABLE)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def RegisterEmail(request):
	if Users.objects.filter(id=request.user.id).exists():
		if not Users.objects.get(id=request.user.id).email_verified:
			email = request.data.get('email')
			if email is None:
				return Response({
						'status':'error',
						'message':'Email required.'
					},status=status.HTTP_406_NOT_ACCEPTABLE)
			if Users.objects.filter(email = email,email_verified=True).exists():
				return Response({
						'status':'error',
						'message':'User with this email already exists.'
					},status=status.HTTP_226_IM_USED)

			try:
				validate_email(email)

			except ValidationError as error:
				return Response({
						'status':'error',
						'message':'Invalid email.',
					},status=status.HTTP_406_NOT_ACCEPTABLE)
			else:
				user = Users.objects.get(id=request.user.id)
				user.email = email
				user.save()
				try:
					if send_mail("DropD - signup email verification OTP",f"Your DropD email verification OTP is {user.otp_code}","noreply@dropd.network",[f'{user.email}'],fail_silently=False):
						return Response({
								'status':'success',
								'message':f'OTP sent at {user.email}'
							})
				except:
					return Response({
							'status':'success',
							'message':f' OTP sent at {user.email}, DUMMY SENT.'
						},status=status.HTTP_202_ACCEPTED)
		return Response({
				'status':'error',
				'message':'Email already verified.'
			},status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def emailVerification(request):
	otp = request.data.get('otp')
	email = request.data.get('email')
	if otp is None:
		return Response({
				'status':'error',
				'message':'OTP required.'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	if email is None:
		return Response({
				'status':'error',
				'message':'Email required.'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	try:
		if Users.objects.filter(id=request.user.id).exists():
			user = Users.objects.get(id=request.user.id,email=email)
	except:
		return Response({
				'status':'error',
				'message':'Incorrect email.'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	if user:
		if timezone.now() <= user.otp_expiration_time:
			if user.otp_code == otp:
				user.email_verified = True
				user.save()
				return Response({
						'status':'success',
						'message':'Email verified.',
					},status=status.HTTP_200_OK)
			return Response({
					'status':'error',
					'message':'Incorrect otp.',
				},status=status.HTTP_406_NOT_ACCEPTABLE)
		return Response({
				'status':'error',
				'message':'OTP expired.',
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	return Response({
			'status':'error',
			'message':'User does not exists.',
		},status=status.HTTP_406_NOT_ACCEPTABLE)




@api_view(['POST'])
def Login(request):
	email = request.data.get('email')
	phone = request.data.get('phone')
	if email:
		try:
			user = Users.objects.get(email=email)
		except:
			user = None
		if user is not None:
			user.save()
			try:
				if send_mail("DropD - login OTP",f"Your DropD login OTP is {user.otp_code}","noreply@dropd.network",[f'{user.email}'],fail_silently=False):
					return Response({
							'status':'success',
							'message':f'OTP sent at {user.email}'
						})
			except:
				return Response({
					'status':'success',
					'message':f'OTP sent at {email}, DUMMY SENT',
				},status=status.HTTP_200_OK)
		return Response({
				'status':'error',
				'message':'User of this email does not exists',
			},status=status.HTTP_406_NOT_ACCEPTABLE)

	elif phone:
		try:
			user = Users.objects.get(phone=phone)
		except:
			user = None
		if user is not None:
			user.save()
			formatted_phone_number = "+"+str(user.phone)
			msg = f"DropD login OTP {user.otp_code}"
			sendSMS(formatted_phone_number,msg)
			return Response({
				'status':'success',
				'message':f'OTP sent to {phone}',
			},status=status.HTTP_200_OK)
		return Response({
				'status':'error',
				'message':'User of this phone number does not exists.',
			},status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['POST'])
def LoginOtpVerification(request):
	otp = request.data.get('otp')
	if request.data.get('email'):
		try:
			user = Users.objects.get(email=request.data.get('email'))
		except Exception as error:
			return Response({
					'status':'error',
					'message':'User of this email does not exists.',
				},status=status.HTTP_404_NOT_FOUND)

	elif request.data.get('phone'):
		try:
			user = Users.objects.get(phone=request.data.get('phone'))
		except Exception as error:
			return Response({
					'status':'error',
					'message':'User of this phone number does not exists.',
				},status=status.HTTP_404_NOT_FOUND)

	else:
		return Response({
				'status':'error',
				'message':'Email or phone missing.'
			},status=status.HTTP_406_NOT_ACCEPTABLE)

	if timezone.now() <= user.otp_expiration_time:
		if user.otp_code == otp:
			user.save()
			token = Token.objects.get(user=user).key
			person = Person.nodes.get(did=user.id)
			is_complete_check = person.completeCheck()


			if not user.email_verified:
				context = {
					'status':'success',
					'message':'Login successful.',
					'token':token,
					'email_verified':False,
				}
				if is_complete_check ==True:
					context['is_profile_complete'] = True
				else:
					context['is_profile_complete'] = False
					context['incomplete_profile_label'] = is_complete_check
				return Response(context,status=status.HTTP_202_ACCEPTED)
			if is_complete_check != True:
				context = {
					'status':'success',
					'token':token,
					'message':'Login successful.',
					'perofile_completed':False,
				}
				context['is_profile_complete'] = False
				context['incomplete_profile_label'] = is_complete_check
				return Response(context,status=status.HTTP_202_ACCEPTED)

			return Response({
					'status':'success',
					'token':token,
					'message':'Login successful.',
					'is_profile_complete':True,
					'incomplete_profile_label':None,
					'profile_completed':True,
				},status=status.HTTP_202_ACCEPTED)
		return Response({
				'status':'error',
				'message':'Incorrect OTP.',
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	return Response({
			'status':'error',
			'message':'OTP expired.',
		},status=status.HTTP_406_NOT_ACCEPTABLE)



@api_view(['GET','POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def UpdateNickname(request):
	if request.method == 'POST':
		nick_name = request.data.get('nick_name')
		if len(nick_name)>=3:
			if re.fullmatch(r'[a-zA-Z]\w+',nick_name) == None:
				return Response({
						'status':'error',
						'message':'Invalid Nickname'
					},status=status.HTTP_406_NOT_ACCEPTABLE)
		else:
			return Response({
					'status':'error',
					'message':'Nickname must be atleast 3 characters long'
				},status=status.HTTP_406_NOT_ACCEPTABLE)

		if nick_name:
			try:
				checkPerson = Person.nodes.get(nick_name=nick_name)
			except:
				checkPerson = None

			if checkPerson is not None and checkPerson.did!=request.user.id:
				return Response({
						'status':'error',
						'message':'This nickname is already taken.',
					},status=status.HTTP_406_NOT_ACCEPTABLE)
			else:
				person = Person.nodes.get(did=request.user.id)
				if person is not None:
					person.nick_name = nick_name
					person.save()
					is_complete_check = person.completeCheck()
					return Response({
							'status':'success',
							'message':'Nick name saved',
							'is_profile_complete':is_complete_check if is_complete_check==True else False,
							'incomplete_profile_label' : is_complete_check if is_complete_check!=True else None
							# 'profile_completed':False,
						},status=status.HTTP_202_ACCEPTED)
				else:
					return Response({
							'status':'error',
							'message':'User Does not exists.',
						},status=status.HTTP_404_NOT_FOUND)

	elif request.method == 'GET':
		person = Person.nodes.get(did=request.user.id)
		if person is not None:
			if person.nick_name:
				return Response({
						'status':'success',
						'nick_name':person.nick_name,
					},status=status.HTTP_200_OK)
			return Response({
					'status':'error',
					'nick_name':None,
				},status=status.HTTP_200_OK)
		return Response({
				'status':'error',
				'message':'User does not exists.',
			},status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def checkNickname(request):
	nick_name = request.data.get('nick_name')
	if len(nick_name)>=3:
		if re.fullmatch(r'[a-zA-Z]\w+',nick_name) == None:
			return Response({
					'status':'error',
					'message':'Invalid Nickname'
				},status=status.HTTP_406_NOT_ACCEPTABLE)
		else:
			try:
				person = Person.nodes.get(nick_name=nick_name)
			except:
				return Response({
						'status':'success',
						'message':'Available'
					},status=status.HTTP_200_OK)
			else:
				return Response({
						'status':'success',
						'message':'Nickname already taken.'
					},status=status.HTTP_226_IM_USED)
	else:
		return Response({
				'status':'error',
				'message':'Nickname must be atleast 3 characters long'
			},status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['GET','POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def UpdateProfileImages(request):
	if request.method == "POST":
		if not custom_file_validator(request.FILES):
			return Response({
					'status':'error',
					'message':'Invalid file type.'
				},status=status.HTTP_406_NOT_ACCEPTABLE)
		try:
			person = Person.nodes.get(did=request.user.id)
		except:
			person = None
		if person is not None:
			profile_pics = request.FILES
			if profile_pics:
				if delete_media_files(person.profile_pics):
					urls=handle_profile_upload(profile_pics,person.did)
					person.profile_pics = urls
					person.save()
					return Response({
							'status':'success',
							'message':'saved',
						},status=status.HTTP_202_ACCEPTED)
			return Response({
					'status':'error',
					'message':'ImageField can not be empty.',
				},status=status.HTTP_406_NOT_ACCEPTABLE)
		return Response({
				'status':'error',
				'message':'User does not exists.',
			},status=status.HTTP_404_NOT_FOUND)
	elif request.method == "GET":
		person = Person.nodes.get(did=request.user.id)
		return Response({
				'status':'success',
				'profile_pics':person.profile_pics,
			},status=status.HTTP_200_OK)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def viewProfile(request):
	try:
		person = Person.nodes.get(did=request.user.id)
		is_complete_check = person.completeCheck()
	except:
		person = None

	if person is not None:
		if is_complete_check == True:
			return Response({
					'status':'success',
					'message':'profile loaded.',
					'did':person.did,
					'joined_at':person.created_at,
					'Phone':person.phone,
					'email':person.email,
					'full_name':person.full_name,
					'nick_name':person.nick_name,
					'bio':person.bio,
					'age':person.age,
					'year_of_birth':person.year_of_birth,
					'gender':person.gender,
					'gender_preference':person.gender_preference,
					'profile_pics':person.profile_pics,
					'person_kundli_attributes':person.person_kundli_attributes,
					'partner_kundli_attributes':person.partner_kundli_attributes,
					'interests':person.interests,
					'zone':person.zone,
					'country':person.country,
					'city':person.city,
					'marital_status':person.marital_status,
					'language_preference1':person.language_preference1,
					'language_preference2':person.language_preference2,
					'language_preference3':person.language_preference3,
					'posts':len(person.posts.all()),

				})

		else:
			return Response({
					'status':'error',
					'profile_completed':False,
					'is_profile_complete':False,
					'incomplete_profile_label':is_complete_check
				},status=status.HTTP_406_NOT_ACCEPTABLE)
	return Response({
			'status':'error',
			'message':'user does not exist'
		},status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def viewUserProfile(request,did):
	try:
		person = Person.nodes.get(did=did)
		is_complete_check = person.completeCheck()
	except:
		person = None

	if person is not None:
		if is_complete_check == True:
			self_person = Person.nodes.get(did=request.user.id)
			person_like_list = person.like.all()
			self_like_list = self_person.like.all()
			return Response({
					'status':'success',
					'message':'profile loaded.',
					'did':person.did,
					'is_friend_requested_to':True if self_person in person.request.all() else False,
					'is_friend_requested_from':True if person in self_person.request.all() else False,
					'is_friend':True if self_person in person.friends.all() else False,
					'is_like_to':True if self_person in person_like_list else False,
					'is_like_from':True if person in self_like_list else False,
					'joined_at':person.created_at,
					'Phone':person.phone,
					'email':person.email,
					'full_name':person.full_name,
					'nick_name':person.nick_name,
					'bio':person.bio,
					'age':person.age,
					'year_of_birth':person.year_of_birth,
					'gender':person.gender,
					'gender_preference':person.gender_preference,
					'profile_pics':person.profile_pics,
					'person_kundli_attributes':person.person_kundli_attributes,
					'partner_kundli_attributes':person.partner_kundli_attributes,
					'interests':person.interests,
					'zone':person.zone,
					'like_count':len(person.like.all()),
					'country':person.country,
					'city':person.city,
					'marital_status':person.marital_status,
					'language_preference1':person.language_preference1,
					'language_preference2':person.language_preference2,
					'language_preference3':person.language_preference3,
					'posts':len(person.posts.all()),

				})

		else:
			return Response({
					'status':'error',
					'profile_completed':False,
					'is_profile_complete':False,
					'incomplete_profile_label':is_complete_check,
				},status=status.HTTP_406_NOT_ACCEPTABLE)
	return Response({
			'status':'error',
			'message':'user does not exist'
		},status=status.HTTP_404_NOT_FOUND)


@api_view(['POST','PUT'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsAuthenticated,])
def UpdateProfile(request):

	if Users.objects.filter(id=request.user.id).exists():

		if request.user.phone_verified and request.user.email_verified:
			try:
				person = Person.nodes.get(did=request.user.id)
			except:
				person = None
			if person is not None:
				try:
					gender = request.data.get('gender')
					gender_preference = request.data.get('gender_preference')
					person_kundli_attributes = request.data.getlist('person_kundli_attributes')
					partner_kundli_attributes = request.data.getlist('partner_kundli_attributes')
					zone = request.data.get('zone')
					interests = request.data.getlist('interests')
					city = request.data.get('city')
					marital_status = request.data.get('marital_status')
					full_name = request.data.get('full_name')
					year_of_birth = request.data.get('year_of_birth')
					country = request.data.get('country')
					bio = request.data.get('bio')
					language_preference1 = request.data.get('language_preference1')
					language_preference2 = request.data.get('language_preference2')
					language_preference3 = request.data.get('language_preference3')

				except Exception as e:
					return Response({
							'status':'error',
							'message':'getlist error.'
						},status=status.HTTP_406_NOT_ACCEPTABLE)

				if not request.data:
					return Response({
							'status':'error',
							'message':'No data is provided.'
						},status=status.HTTP_406_NOT_ACCEPTABLE)

				if bio:
					person.bio = bio
					person.save()

				if gender:
					gender = gender.lower()
					genders = ['male','female','genderqueer']
					if gender not in genders:
						return Response({
								'status':'error',
								'message':'This option is not available.',
							},status=status.HTTP_406_NOT_ACCEPTABLE)

					person.gender = gender
					person.save()


				if gender_preference:
					gender_preference = gender_preference.lower()
					preference_list = ['male','female','genderqueer']
					if gender_preference not in preference_list:
						return Response({
								'status':'error',
								'message':'This option is not available.',
							},status=status.HTTP_406_NOT_ACCEPTABLE)
					person.gender_preference = gender_preference
					person.save()

				if person_kundli_attributes:
					if len(person_kundli_attributes)==5:
						attributes_list = [
							'leader',
							'bread earner',
							'homemaker',
							'thinker',
							'good parent',
							'straight',
							'passionate lover',
							'care giver',
							'funny',
							'gender fluid',
							'homosexual',
							'nomad',
						]
						attributes_checked=[]
						for attr in person_kundli_attributes:
							attr = attr.lower()
							if attr not in attributes_list:
								return Response({
										'status':'error',
										'message':'This option is not available',
									},status=status.HTTP_406_NOT_ACCEPTABLE)
							attributes_checked.append(attr)
						person.person_kundli_attributes = attributes_checked
						try:
							person.save()
						except:
							return Response({
									'status':'error',
									'message':'This option is not available.',
								},status=status.HTTP_406_NOT_ACCEPTABLE)

					else:
						return Response({
								'status':'error',
								'message':'Number of attributes did not match.'
							},status=status.HTTP_406_NOT_ACCEPTABLE)


				if partner_kundli_attributes:
					if len(partner_kundli_attributes)==5:
						attributes_list = [
							'leader',
							'bread earner',
							'homemaker',
							'thinker',
							'good parent',
							'straight',
							'passionate lover',
							'care giver',
							'funny',
							'gender fluid',
							'homosexual',
							'nomad',
						]
						attributes_checked=[]
						for attr in partner_kundli_attributes:
							attr = attr.lower()
							if attr not in attributes_list:
								return Response({
										'status':'error',
										'message':'This option is not available.',
									},status=status.HTTP_406_NOT_ACCEPTABLE)
							attributes_checked.append(attr)
						person.partner_kundli_attributes = attributes_checked
						try:
							person.save()
						except:
							return Response({
									'status':'error',
									'message':'This option is not available.',
								},status=status.HTTP_406_NOT_ACCEPTABLE)

					else:
						return Response({
								'status':'error',
								'message':'Number of attributes did not match.'
							},status=status.HTTP_406_NOT_ACCEPTABLE)

				if zone:
					zone_list = ('love grounds','open marriage commune','seniors in love again',)
					zone = zone.lower()
					if zone not in zone_list:
						return Response({
								'status':'error',
								'message':'This option is not available.',
							},status=status.HTTP_406_NOT_ACCEPTABLE)
					else:
						person.zone = zone
					try:
						person.save()
					except:
						return Response({
								'status':'error',
								'message':'This option is not available.',
							},status=status.HTTP_406_NOT_ACCEPTABLE)


				if interests:
					if len(interests)==8:
						for item in interests:
							if Person_Interests_List.objects.filter(name=item).exists():
								pass
							else:
								return Response({
										'status':'error',
										'message':f'Interest {item} is not available.'
									},status=status.HTTP_406_NOT_ACCEPTABLE)
						person.interests=interests
						person.save()

					else:
						return Response({
								'status':'error',
								'message':'Number of interests did not match.'
							},status=status.HTTP_406_NOT_ACCEPTABLE)

				if city:
					person.city = city.lower()
					person.save()

				if marital_status:
					person.marital_status = marital_status
					try:
						person.save()
					except:
						return Response({
								'status':'error',
								'message':'Request invalid.'
							},status=status.HTTP_406_NOT_ACCEPTABLE)

				if full_name:
					if full_name == "":
						return Response({
								'status':'error',
								'message':'Invalid name',
							},status=status.HTTP_406_NOT_ACCEPTABLE)
					for char in full_name:
						if char.isdigit	():
							return Response({
									'status':'error',
									'message':'Invalid name.'
								},status=status.HTTP_406_NOT_ACCEPTABLE)

					person.full_name = full_name
					person.save()

				if year_of_birth:
					if not year_of_birth.isdigit() or len(year_of_birth)!=4:
						return Response({
								'status':'error',
								'message':'Invalid year.'
							},status=status.HTTP_406_NOT_ACCEPTABLE)

					person.year_of_birth = year_of_birth
					person.age = calculate_age(person.year_of_birth)
					try:
						person.save()
					except:
						return Response({
								'status':'error',
								'message':'Invalid year.'
							},status=status.HTTP_406_NOT_ACCEPTABLE)

				if country:
					if not country.isalpha():
						return Response({
								'status':'error',
								'message':'Invaid country name.'
							},status=status.HTTP_406_NOT_ACCEPTABLE)
					person.country = country.lower()
					person.save()

				if language_preference1:
					if not language_preference1.isalpha():
						return Response({
								'status':'error',
								'message':'Invalid input.'
							},status=status.HTTP_406_NOT_ACCEPTABLE)
					else:
						person.language_preference1 = language_preference1
						person.save()

				if language_preference2:
					if not language_preference2.isalpha():
						return Response({
								'status':'error',
								'message':'Invalid input.'
							},status=status.HTTP_406_NOT_ACCEPTABLE)
					else:
						person.language_preference2 = language_preference2
						person.save()

				if language_preference3:
					if not language_preference3.isalpha():
						return Response({
								'status':'error',
								'message':'Invalid input.'
							},status=status.HTTP_406_NOT_ACCEPTABLE)
					else:
						person.language_preference3 = language_preference3
						person.save()


				return Response({
						'status':'success',
						'message':'Profile saved'
					},status=status.HTTP_202_ACCEPTED)

			return Response({
				'status':'error',
				'message':'User does not exists.',
			},status=status.HTTP_404_NOT_FOUND)

		return Response({
				'status':'error',
				'message':'User not verified.',
			},status=status.HTTP_404_NOT_FOUND)
	return Response({
			'status':'error',
			'message':'User does not exists.'
		},status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_interests(request):
	interests = Person_Interests_List.objects.all().order_by('name')
	serializer = InterestsSerializer(interests,many=True)
	return Response(serializer.data,status=status.HTTP_200_OK)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated,])
def timeline(request,page_number):
	try:
		person = Person.nodes.get(did=request.user.id)
	except:
		return Response({
				'status':'error',
				'message':'User does not exits'
			},status=status.HTTP_404_NOT_FOUND)
	recent_posts = []

	context = {}
	if person.completeCheck()==True:
		context['is_profile_complete'] = True
	else:
		context['is_profile_complete'] = False
		context['incomplete_profile_label'] = person.completeCheck()
	context['status']='success'
	context['message']='timeline loaded'
	context['user_profile']= person.profile_info()
	context['posts'] = person.fetch_posts_new(page_number=page_number)
	return Response(context,status=status.HTTP_200_OK)

## TEMPORARY TIMELINE #############################################################
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated,])
def timelineTemp(request):
	try:
		person = Person.nodes.get(did=request.user.id)
	except:
		return Response({
				'status':'error',
				'message':'User does not exits'
			},status=status.HTTP_404_NOT_FOUND)
	else:
		recent_posts = []

		context = {}
		if person.completeCheck()==True:
			context['is_profile_complete'] = True
		else:
			context['is_profile_complete'] = False
			context['incomplete_profile_label'] = person.completeCheck()
		context['status']='success'
		context['message']='timeline loaded'
		context['user_profile']= person.profile_info()
		context['posts'] = person.fetch_posts_new()
		return Response(context,status=status.HTTP_200_OK)

###############################################################################


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def viewMatch(request,page_number):
	if Users.objects.filter(id=request.user.id).exists():
		try:
			person = Person.nodes.get(did=request.user.id)
		except:
			return Response({
					'status':'error',
					'message':'User does not exist.'
				},status=status.HTTP_404_NOT_FOUND)
		else:
			# print(person.gender_preference)
			context = {}
			context['matches'] = person.match_person(page_number=page_number)
			context['message']='Matches loaded.'
			context['status']='success'
			return Response(context,status=status.HTTP_200_OK)

	else:
		return Response({
				'status':'error',
				'message':'User does not exists.'
			},status=status.HTTP_404_NOT_FOUND)

##########################################################################
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def viewMatchOld(request):
	if Users.objects.filter(id=request.user.id).exists():
		try:
			person = Person.nodes.get(did=request.user.id)
		except:
			return Response({
					'status':'error',
					'message':'User does not exist.'
				},status=status.HTTP_404_NOT_FOUND)
		else:
			# print(person.gender_preference)
			context = {}
			context['matches'] = person.match_person()
			context['message']='Matches loaded.'
			context['status']='success'
			return Response(context,status=status.HTTP_200_OK)

	else:
		return Response({
				'status':'error',
				'message':'User does not exists.'
			},status=status.HTTP_404_NOT_FOUND)
##########################################################################

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def viewMatchCount(request):
	try:
		person = Person.nodes.get(did=request.user.id)
	except:
		return Response({
				'status':'error',
				'message':'User not found',
			},status=status.HTTP_404_NOT_FOUND)
	else:
		return Response({
				'status':'success',
				'message':'match count',
				'total_match_count':match_count(person)
			})


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def createClub(request):
	person = Person.nodes.get(did=request.user.id)
	club_name = request.data.get('club_name')
	description = request.data.get('description')
	category = request.data.get('category')

	if club_name is None:
		return Response({
				'status':'error',
				'message':'Club name is missing'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	elif description is None:
		return Response({
				'status':'error',
				'message':'description is missing'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	elif category is None:
		return Response({
				'status':'error',
				'message':'category is missing'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		if not Person_Interests_List.objects.filter(name=category).exists():
			return Response({
					'status':'error',
					'message':f'category {category} is not available'
				},status=status.HTTP_406_NOT_ACCEPTABLE)

	if not custom_file_validator(request.FILES):
		return Response({
				'status':'error',
				'message':'Invalid file type'
			},status=status.HTTP_406_NOT_ACCEPTABLE)

	## CLUB
	if club_name is not None :
		club = Club(club_name=club_name,description=description,category=category).save()
		urls = handle_club_upload(request.FILES,club.club_id)
		if urls is not None:
			club.profile_image = urls.get('profile_image')
			club.cover_image = urls.get('cover_image')
			club.save()
		club.owner.connect(person)
		club.save()
		person.clubs.connect(club)
		person.save()
		if category:
			club.category=category
			club.save()
		if club.owner.is_connected(person):
			return Response({
					'status':'success',
					'message':f'Club {club.club_name} created successfully',
					'club_info':{
						'club_id':club.club_id,
						'club_name':club.club_name,
						'description':club.description,
						'category':club.category,
						'profile_image':club.profile_image,
						'cover_image':club.cover_image,
						'created_at':club.created_at
					}
				},status=status.HTTP_201_CREATED)
		else:
			club.delete()
			return Response({
					'status':'error',
					'message':'Connection error please recreate your club'
				})
	else:
		return Response({
				'status':'error',
				'message':'Club name is required'
			},status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def updateClub(request):
	club_id = request.data.get('club_id')
	category = request.data.get('category')
	club_name = request.data.get('club_name')
	description = request.data.get('club_name')

	try:
		club = Club.nodes.get(club_id=club_id)
	except:
		return Response({
				'status':'error',
				'message':'Invalid Club ID'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		if request.user.id == club.owner.all()[0].did:
			if club_name:
				club.club_name = club_name
				club.save()
			if description:
				club.description = description
				club.save()
			if category:
				if Person_Interests_List.objects.filter(name=category).exists():
					club.category = category
					club.save()
				else:
					return Response({
							'status':'error',
							'message':'category not available'
						},status=status.HTTP_406_NOT_ACCEPTABLE)
			if request.FILES:
				if not custom_file_validator(request.FILES):
					return Response({
							'status':'error',
							'message':'Invalid file type'
						},status=status.HTTP_406_NOT_ACCEPTABLE)

				elif delete_media_files([club.profile_image,club.cover_image]):
					urls = handle_club_upload(request.FILES,club_id)
					club.profile_image = urls.get('profile_image')
					club.cover_image = urls.get('cover_image')
					club.save()
			return Response({
					'status':'success',
					'message':'Updated successfully'
				},status=status.HTTP_200_OK)
		else:
			return Response({
					'status':'error',
					'message':'Not authorized'
				},status=status.HTTP_406_NOT_ACCEPTABLE)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def viewClub(request,club_id):
	try:
		club = Club.nodes.get(club_id=club_id)
	except:
		return Response({
				'status':'error',
				'message':'Invalid Club ID'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	if False:
		pass
	else:
		club = Club.nodes.get(club_id=club_id)
		person = Person.nodes.get(did=request.user.id)
		owner = club.owner[0]
		if person in club.members.all():
			posts = club.posts.all()
			post_list = []
			for post in posts:
				postfrom = post.postFrom[0]
				from_object = {
					'did':postfrom.did,
					'nick_name':postfrom.nick_name,
					'joined_at':postfrom.created_at,
					'zone':postfrom.zone,
					'kundli_attributes':postfrom.person_kundli_attributes,
					'profile_pics':postfrom.profile_pics,
					'like_count':len(postfrom.like.all()),
					'is_friend':True if person in postfrom.friends.all() else False,
					'is_friend_requested_to':True if person in postfrom.request.all() else False,
					'is_friend_requested_from':True if postfrom in person.request.all() else False,
					'is_like_to': True if person in postfrom.like.all() else False,
					'is_like_from':True if postfrom in person.like.all() else False,
				}
				post_object = {
					'post_from':from_object,
					'pid':post.pid,
					'created_at':post.created_at,
					'text':post.text,
					'images':post.imageLink,
					'tags':post.tags(),
					'likes':post.likes,
					'comments':post.comments(),
				}
				post_list.append(post_object)
			return Response({
					'status':'success',
					'message':'Club loaded',
					'club_info':{
						'club_id':club.club_id,
						'club_name':club.club_name,
						'description':club.description,
						'category':club.category,
						'profile_image':club.profile_image,
						'cover_image':club.cover_image,
						'created_at':club.created_at,
						'member_count':len(club.members.all()),
						'is_member': True if Person.nodes.get(did=request.user.id) in club.members.all() else False,
						'owner':{
							'did':owner.did,
							'nick_name':owner.nick_name,
							'joined_at':owner.created_at,
							'kundli_attributes':owner.person_kundli_attributes,
							'zone':owner.zone,
							'like_count':len(owner.like.all()),
							'profile_pics':owner.profile_pics,
						},
						'posts':post_list,
					}
				},status=status.HTTP_200_OK)
		else:
			return Response({
					'status':'success',
					'message':'Club loaded',
					'club_info':{
						'club_id':club.club_id,
						'club_name':club.club_name,
						'description':club.description,
						'category':club.category,
						'profile_image':club.profile_image,
						'cover_image':club.cover_image,
						'created_at':club.created_at,
						'member_count':len(club.members.all()),
						'is_member': True if Person.nodes.get(did=request.user.id) in club.members.all() else False,
						'owner':{
							'did':owner.did,
							'nick_name':owner.nick_name,
							'joined_at':owner.created_at,
							'kundli_attributes':owner.person_kundli_attributes,
							'zone':owner.zone,
							'like_count':len(owner.like.all()),
							'profile_pics':owner.profile_pics,
						},
						'posts':[],
					}
				},status=status.HTTP_200_OK)

@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def deleteClub(request):
	club_id = request.data.get('club_id')
	try:
		club = Club.nodes.get(club_id=club_id)
	except:
		return Response({
				'status':'error',
				'message':'Invalid Club ID'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		if request.user.id == club.owner.all()[0].did:
			club.delete()
			return Response({
					'status':'success',
					'message':'Club deleted successfully',
				},status=status.HTTP_200_OK)
		else:
			return Response({
					'status':'error',
					'message':'Unauthorized'
				},status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def joinClub(request):
	transaction_id = request.data.get('transaction_id')
	try:
		club = Club.nodes.get(club_id=request.data.get('club_id'))
	except:
		return Response({
				'status':'error',
				'message':'Invalid club ID'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		person = Person.nodes.get(did=request.user.id)
		if person.clubs.is_connected(club):
			return Response({
					'status':'success',
					'message':'Club already joined'
				},status=status.HTTP_200_OK)
		else:
			if club.request_membership.is_connected(person):
				return Response({
						'status':'error',
						'message':'Membership already requested'
					},status=status.HTTP_226_IM_USED)
			else:
				if transaction_id:
					relation = club.request_membership.connect(person)
					relation.transaction_id = transaction_id
					relation.requested_at = datetime.now()
					relation.save()
					return Response({
							'status':'success',
							'message':'Membership requested'
						},status=status.HTTP_200_OK)
				else:
					return Response({
							'status':'error',
							'message':'Transactiona ID missing'
						},status=status.HTTP_406_NOT_ACCEPTABLE)

@api_view(['POST'])
def validateTransaction(request):
	transaction_id = request.data.get('transaction_id')
	if not transaction_id:
		return Response({
				'status':'error',
				'message':'Transaction ID missing'
			},status=status.HTTP_406_NOT_ACCEPTABLE)

	clubs = Club.nodes.all()
	for club in clubs:
		for each in club.request_membership.all():
			relation = club.request_membership.relationship(each)
			if relation.transaction_id==transaction_id:
				person = relation.start_node()
				club = relation.end_node()
				requested_at = relation.requested_at
				relation = club.members.connect(person)
				relation.transaction_id = transaction_id
				relation.requested_at = requested_at
				relation.accepted_at = datetime.now()
				relation.save()
				club.request_membership.disconnect(person)
				club.save()
				if club.members.is_connected(person):
					return Response({
							'status':'success',
							'message':'Transaction confirmed',
						},status=status.HTTP_200_OK)
				else:
					return Response({
							'status':'error',
							'message':'Connection error, please validate transaction again'
						},status=status.HTTP_406_NOT_ACCEPTABLE)

	return Response({
			'status':'error',
			'message':'Transaction not found'
		},status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def clubMembers(request,club_id):
	try:
		club = Club.nodes.get(club_id=club_id)
	except:
		return Response({
				'status':'error',
				'message':'Club not found',
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		members = club.members.all()
		member_list = []
		for member in members:
			member_object = {
				'did':member.did,
				'nick_name':member.nick_name,
				'joined_at':member.created_at,
				'kundli_attributes':member.person_kundli_attributes,
				'zone':member.zone,
				'like_count':len(member.like.all()),
				'profile_pics':member.profile_pics,
			}
			member_list.append(member_object)
		return Response({
				'status':'success',
				'message':'Members loaded',
				'members':member_list,
			},status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def allClubListOld(request):
	if Person.nodes.get(did=request.user.id):
		return Response({
				'status':'success',
				'message':'Clubs loaded',
				'club_list':fetch_all_clubs(request.user.id),
			},status=status.HTTP_200_OK)
	else:
		return Response({
				'status':'error',
				'message':'User does not exists.',
			},status=status.HTTP_404_NOT_FOUND)

##################################### club list new  #####################################################
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def allClubList(request,page_number):
	if exists_person_node(request.user.id):
		return Response({
				'status':'success',
				'message':'Clubs loaded',
				'club_list':fetch_all_clubs(request.user.id,page_number=page_number),
			},status=status.HTTP_200_OK)
	else:
		return Response({
				'status':'error',
				'message':'User does not exists.',
			},status=status.HTTP_404_NOT_FOUND)




@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def myClubListOld(request):
	if exists_person_node(request.user.id):
		return Response({
				'status':'success',
				'message':'Clubs loaded',
				'club_list':fetch_user_clubs(request.user.id),
			},status=status.HTTP_200_OK)
	else:
		return Response({
				'status':'error',
				'message':'User does not exists'
			},status=status.HTTP_404_NOT_FOUND)


############################## new my clubs ############################################################

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def myClubList(request,page_number):
	if exists_person_node(request.user.id):
		return Response({
				'status':'success',
				'message':'Clubs loaded',
				'club_list':fetch_user_clubs(request.user.id,page_number=page_number),
			},status=status.HTTP_200_OK)
	else:
		return Response({
				'status':'error',
				'message':'User does not exists'
			},status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def personLike(request):
	did = request.data.get('did')
	if did is not None:
		person = Person.nodes.get(did=request.user.id)
		target_person = Person.nodes.get(did=did)
		if target_person.like.is_connected(person):
			target_person.like.disconnect(person)
			# print(target_person.likes)
			target_person.likes = len(target_person.like.all())
			target_person.save()
			return Response({
					'status':'success',
					'message':f'{person.nick_name} no longer like {target_person.nick_name}',
					'like_count': target_person.likes,
				},status=status.HTTP_200_OK)
		else:
			relation = target_person.like.connect(person)
			relation.liked_at = datetime.now()
			relation.save()
			target_person.likes = len(target_person.like.all())
			# print(target_person.likes)
			return Response({
					'status':'success',
					'message':f'{person.nick_name} liked {target_person.nick_name}',
					'like_count':target_person.likes,
				},status=status.HTTP_200_OK)
	else:
		return Response({
				'status':'error',
				'message':'Invalid did',
			},status=status.HTTP_406_NOT_ACCEPTABLE)




@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def createPage(request):
	person = Person.nodes.get(did=request.user.id)
	page_name = request.data.get('page_name')
	description = request.data.get('description')

	if not custom_file_validator(request.FILES):
		return Response({
				'status':'error',
				'message':'Invalid file type'
			},status=status.HTTP_406_NOT_ACCEPTABLE)


	## PAGE
	if page_name is not None:
		page = Page(page_name=page_name,description=description).save()
		urls = handle_page_upload(request.FILES,page.page_id)
		if urls is not None:
			page.profile_image = urls.get('profile_image')
			page.cover_image = urls.get('cover_image')
			page.save()
		page.owner.connect(person)
		page.save()
		if page.owner.is_connected(person):
			return Response({
					'status':'success',
					'message':f'Page {page.page_name} created successfully',
					'page':{
						'page_id':page.page_id,
						'page_name':page.page_name,
						'description':page.description,
						'profile_image':page.profile_image,
						'cover_image':page.cover_image,
						'like_count':len(page.liked_by.all()),
						'created_at':page.created_at
					}
				},status=status.HTTP_201_CREATED)
		else:
			page.delete()
			return Response({
					'status':'error',
					'message':'Connection error please recreate your page'
				})
	return Response({
			'status':'error',
			'message':'Page name is required'
		},status=status.HTTP_406_NOT_ACCEPTABLE)



@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def updatePage(request):
	page_id = request.data.get('page_id')
	try:
		page = Page.nodes.get(page_id=page_id)
	except:
		return Response({
				'status':'error',
				'message':'Invalid page ID'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		if request.user.id == page.owner.all()[0].did:
			if request.data.get('page_name'):
				page.page_name = request.data.get('page_name')
				page.save()
			if request.data.get('description'):
				page.description = request.data.get('description')
				page.save()
			if request.FILES:
				if not custom_file_validator(request.FILES):
					return Response({
							'status':'error',
							'message':'Invalid file type'
						},status=status.HTTP_406_NOT_ACCEPTABLE)

				elif delete_media_files([page.profile_image,page.cover_image]):
					urls = handle_page_upload(request.FILES,page_id)
					page.profile_image = urls.get('profile_image')
					page.cover_image = urls.get('cover_image')
					page.save()


			return Response({
					'status':'success',
					'message':'Updated successfully'
				},status=status.HTTP_200_OK)
		else:
			return Response({
					'status':'error',
					'message':'Not authorized'
				},status=status.HTTP_406_NOT_ACCEPTABLE)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def viewPage(request,page_id):
	try:
		page = Page.nodes.get(page_id=page_id)
	except:
		return Response({
				'status':'error',
				'message':'Invalid page ID'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		if Users.objects.filter(id=request.user.id).exists():
			owner = page.owner[0]
			person = Person.nodes.get(did=request.user.id)
			posts = page.posts.all()
			post_list = []
			for post in posts:
				post_object = post.post_info(person)
				post_list.append(post_object)
			return Response({
					'status':'success',
					'message':'Page loaded',
					'page':{
						'page_id':page.page_id,
						'page_name':page.page_name,
						'description':page.description,
						'profile_image':page.profile_image,
						'cover_image':page.cover_image,
						'created_at':page.created_at,
						'like_count':len(page.liked_by.all()),
						'is_like_to':True if person in page.liked_by.all() else False,
						'owner':{
							'did':owner.did,
							'nick_name':owner.nick_name,
							'joined_at':owner.created_at,
							'kundli_attributes':owner.person_kundli_attributes,
							'zone':owner.zone,
							'like_count':len(owner.like.all()),
							'profile_pics':owner.profile_pics,
						},
						'posts':post_list,
					}
				},status=status.HTTP_200_OK)
		else:
			posts = page.posts.all()
			post_list = []
			return Response({
					'status':'success',
					'message':'Page loaded',
					'page':{
						'page_id':page.page_id,
						'page_name':page.page_name,
						'description':page.description,
						'profile_image':page.profile_image,
						'cover_image':page.cover_image,
						'created_at':page.created_at,
						'like_count':len(page.liked_by.all()),
						'posts':post_list,
					}
				},status=status.HTTP_200_OK)

@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def deletePage(request):
	page_id = request.data.get('page_id')
	try:
		page = Page.nodes.get(page_id=page_id)
	except:
		return Response({
				'status':'error',
				'message':'Invalid Page ID'
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		if request.user.id == page.owner.all()[0].did:
			page.delete()
			return Response({
					'status':'success',
					'message':'Page deleted successfully',
				},status=status.HTTP_200_OK)
		else:
			return Response({
					'status':'error',
					'message':'Unauthorized'
				},status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def likePage(request):
	try:
		page = Page.nodes.get(page_id=request.data.get('page_id'))
	except:
		return Response({
				'status':'error',
				'message':'Invalid page ID',
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		person = Person.nodes.get(did=request.user.id)
		if page.liked_by.is_connected(person):
			page.liked_by.disconnect(person)
			page.likes=len(page.liked_by.all())
			page.save()
			return Response({
					'status':'success',
					'message':'like reverted',
					'likes':len(page.liked_by.all()),
				},status=status.HTTP_200_OK)
		else:
			relation = page.liked_by.connect(person)
			page.likes = len(page.liked_by.all())
			page.save()
			relation.liked_at = datetime.now()
			relation.save()
			return Response({
					'status':'success',
					'message':'Liked',
					'likes':len(page.liked_by.all())
				},status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def allPageListOld(request):
	if exists_person_node(request.user.id):
		return Response({
				'status':'success',
				'message':'Pages loaded',
				'pages':fetch_all_pages(request.user.id)
			},status=status.HTTP_200_OK)

	else:
		return Response({
				'status':'error',
				'message':'User does not exists.',
			},status=status.HTTP_404_NOT_FOUND)

######################## new page list ###############################################################

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def allPageList(request,page_number):
	if exists_person_node(request.user.id):
		return Response({
				'status':'success',
				'message':'Pages loaded',
				'pages':fetch_all_pages(request.user.id,page_number=page_number)
			},status=status.HTTP_200_OK)

	else:
		return Response({
				'status':'error',
				'message':'User does not exists.',
			},status=status.HTTP_404_NOT_FOUND)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def myPageListOld(request):
	if exists_person_node(request.user.id):
		return Response({
			'status':'success',
			'message':'Pages loaded',
			'pages':fetch_user_pages(request.user.id),
		},status=status.HTTP_200_OK)
	else:
		return Response({
				'status':'error',
				'message':'User does not exists.',
			},status=status.HTTP_404_NOT_FOUND)

########################### new my pages ##################################################

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def myPageList(request,page_number):
	if exists_person_node(request.user.id):
		return Response({
			'status':'success',
			'message':'Pages loaded',
			'pages':fetch_user_pages(request.user.id,page_number=page_number),
		},status=status.HTTP_200_OK)
	else:
		return Response({
				'status':'error',
				'message':'User does not exists.',
			},status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def friendRequest(request):
	try:
		target_person = Person.nodes.get(did=request.data.get('did'))
		if request.user.id == request.data.get('did'):
			return Response({
					'status':'error',
					'message':"You can not send friend request to yourself"
				},status=status.HTTP_406_NOT_ACCEPTABLE)
	except:
		return Response({
				'status':'error',
				'message':'User not found'
			},status=status.HTTP_404_NOT_FOUND)
	else:
		person = Person.nodes.get(did=request.user.id)
		send_friend_request = request.data.get('send_friend_request')
		transaction_id = request.data.get('transaction_id')
		if  transaction_id:
			if send_friend_request is not None and send_friend_request == 'true':
				if target_person.request.is_connected(person):
					return Response({
							'status':'success',
							'message':'Request already sent'
						},status=status.HTTP_200_OK)
				else:
					if person.friends.is_connected(target_person):
						return Response({
								'status':'error',
								'message':f'You are already friend of {target_person.nick_name}'
							})
					rel = target_person.request.connect(person)
					rel.requested_date = datetime.now()
					rel.transaction_id = transaction_id
					rel.save()
					return Response({
							'status':'success',
							'message':'Friend request sent'
						},status=status.HTTP_200_OK)
			elif send_friend_request is not None and send_friend_request == 'false':
				if target_person.request.is_connected(person):
					target_person.request.disconnect(person)
					target_person.save()
					return Response({
							'status':'success',
							'message':'Request revoked'
						},status=status.HTTP_200_OK)
				else:
					return Response({
							'status':'success',
							'message':'Friend request does not exist'
						},status=status.HTTP_406_NOT_ACCEPTABLE)
			else:
				return Response({
						'status':'error',
						'message':'Invalid parameters',
					},status=status.HTTP_406_NOT_ACCEPTABLE)
		else:
			return Response({
				'status':'error',
				'message':'Transaction ID missing',
			},status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def friendRequestList(request):
	try:
		person = Person.nodes.get(did=request.user.id)
	except:
		return Response({
				'status':'error',
				'message':'User not Found',
			},status=status.HTTP_404_NOT_FOUND)
	else:
		request_info = []
		requests = person.request.all()
		for each in requests:
			info_dict = {}
			info_dict['requested_date']=(person.request.relationship(each)).requested_date,
			info_dict['did']=each.did
			info_dict['nickname']=each.nick_name
			info_dict['kundli_attributes']=each.person_kundli_attributes
			info_dict['joined_at']=each.created_at
			info_dict['zone']=each.zone
			info_dict['like_count']=len(each.like.all())
			info_dict['profile_pics']=each.profile_pics
			# info_dict['']=each.nick_name
			request_info.append(info_dict)

		else:
			return Response({
					'status':'success',
					'message':'Requests loaded',
					'friend_requests':request_info,
				},status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def friendRequestSentList(request):
	try:
		person = Person.nodes.get(did=request.user.id)
	except:
		return Response({
				'status':'error',
				'message':'User not Found',
			},status=status.HTTP_404_NOT_FOUND)
	else:
		request_info = []
		requests = person.sent_request.all()
		for each in requests:
			info_dict = {}
			info_dict['requested_date']=(person.sent_request.relationship(each)).requested_date,
			info_dict['did']=each.did
			info_dict['nickname']=each.nick_name
			info_dict['kundli_attributes']=each.person_kundli_attributes
			info_dict['joined_at']=each.created_at
			info_dict['zone']=each.zone
			info_dict['like_count']=len(each.like.all())
			info_dict['profile_pics']=each.profile_pics
			# info_dict['']=each.nick_name
			request_info.append(info_dict)

		else:
			return Response({
					'status':'success',
					'message':'Requests loaded',
					'friend_requests_sent':request_info,
				},status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def friendRequestAccept(request):
	try:
		target_person = Person.nodes.get(did=request.data.get('did'))
		person_requested = Person.nodes.get(did=request.user.id)
	except:
		return Response({
				'status':'error',
				'message':'User not found'
			},status=status.HTTP_404_NOT_FOUND)
	else:
		if person_requested.request.is_connected(target_person):
			make_friend(person_requested,target_person)
			return Response({
		 			'status':'success',
		 			'message':'Request accepted',
		 		},status=status.HTTP_200_OK)
		else:
		 	return Response({
		 			'status':'error',
		 			'message':f'{target_person.nick_name} has not requeste yet, person needs to make a friend request first'
		 		},status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def friendRequestReject(request):
	try:
		requested_person = Person.nodes.get(did=request.data.get('did'))
	except:
		return Response({
				'status':'error',
				'message':'User not found',
			},status=status.HTTP_406_NOT_ACCEPTABLE)
	else:
		person = Person.nodes.get(did=request.user.id)
		if person.request.is_connected(requested_person):
			person.request.disconnect(requested_person)
			person.save()
			return Response({
					'status':'success',
					'message':'Request rejected'
				},status=status.HTTP_200_OK)
		else:
			return Response({
					'status':'error',
					'message':f'{requested_person.nick_name} has not requested yet, person needs to make a friend request first'
				},status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def friendListOld(request):
	try:
		person = Person.nodes.get(did=request.user.id)
	except:
		return Response({
				'status':'error',
				'message':'User not Found',
			},status=status.HTTP_404_NOT_FOUND)
	else:
		friends_info = []
		friends = person.friends.all()
		for each in friends:
			rel = person.friends.relationship(each)
			info_dict = {}
			info_dict['requested_date']=(person.friends.relationship(each)).requested_date,
			info_dict['accepted_date']=(person.friends.relationship(each)).accepted_date,
			info_dict['did']=each.did
			info_dict['nick_name']=each.nick_name
			info_dict['kundli_attributes']=each.person_kundli_attributes
			info_dict['joined_at']=each.created_at
			info_dict['zone']=each.zone
			info_dict['like_count']=len(each.like.all())
			info_dict['profile_pics']=each.profile_pics
			info_dict['room_code'] = rel.chat_room_id
			# info_dict['']=each.nick_name
			friends_info.append(info_dict)

		else:
			return Response({
					'status':'success',
					'message':'Requests loaded',
					'friend_list':friends_info,
				},status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def friendList(request,page_number):
	try:
		friend_list = fetch_friend_list(request.user.id,page_number)
	except:
		return Response({
				'status':'error',
				'message':'User not Found',
			},status=status.HTTP_404_NOT_FOUND)
	else:
		return Response({
				'status':'success',
				'message':'Requests loaded',
				'friend_list':friend_list,
			},status=status.HTTP_200_OK)



def login_view(request):
    if request.method == "POST":
        # print(request.POST)
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        print(phone,password)
        # user = authenticate(username=username,password=password)
        try:
        	user = Users.objects.get(phone=phone)
        except:
        	return render(request,"neoUserModel/login.html")
        if user.check_password(password):
            login(request, user)
            token = Token.objects.get(user=user).key
            node = Person.nodes.get(phone=phone)
            print(node.nick_name,token)
            return redirect("chat-list",uid=user.uid)
        else:
            return render(request,"neoUserModel/login.html")
    else:
        return render(request,"neoUserModel/login.html")


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_jwt(request):
	refresh = RefreshToken.for_user(request.user)
	return Response({
			# 'refresh':str(refresh),
			'status':'success',
			'access_token':str(refresh.access_token)
		})


# @api_view(['GET'])
# @authentication_classes([JWTStatelessUserAuthentication])
# @permission_classes([IsAuthenticated])
# def test_api(request):
# 	# # print(request.user)
# 	# data = {'token': token}
# 	# try:
# 	# 	print(type(token))
# 	# 	valid_data = TokenBackend(algorithm='HS256').decode(token,verify=True)
# 	# 	user = valid_data['user']
# 	# 	request.user = user
# 	# except ValidationError as v:
# 	# 	print("validation error", v)
# 	token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
# 	# print(token)
# 	valid_token = JWTStatelessUserAuthentication().get_validated_token(token)
# 	user = JWTStatelessUserAuthentication().get_user(valid_token)
# 	print(JWTStatelessUserAuthentication().authenticate(request))
# 	return Response({
# 			'status':'200 ok',
# 		})

# @login_required(login_url="login-view")
# def chats(request,uid):
# 	user  = Users.objects.get(uid=uid)
# 	nick_name = Person.nodes.get(uid=uid).nick_name
# 	token = Token.objects.get(user=user).key
# 	return render(request,"neoUserModel/index.html",{
# 			'nick_name':nick_name,
# 			'token':token,
# 		})
# @login_required(login_url="login-view")
# def chat_room(request,consumer_name,did,room_code):
# 	person = Person.nodes.get(uid=request.user.uid)
# 	token  = Token.objects.get(user=request.user).key
# 	return render(request,"neoUserModel/room.html",{'room_code':room_code,'to_id':did,'nick_name':person.nick_name,'token':token})
