from authUser.custom_profile_storage import MediaStorage
from datetime import datetime
import os
import hashlib
import magic
import tempfile
from datetime import datetime,timedelta
import boto3
import environ
from django.core.files.storage import default_storage
from neoUserModel.models import *
from neomodel import Q,db
import time

env = environ.Env()
environ.Env.read_env()


def custom_file_validator(file_objects):
	allowed_types = ['image/jpeg','image/png','image/jpg']
	for key in file_objects:
		file_object=file_objects[key]
		with tempfile.NamedTemporaryFile() as temp:
			for chunk in file_object.chunks():
				temp.write(chunk)
			file_check_variable=magic.from_file(temp.name,mime=True)
			if file_check_variable not in allowed_types:
				return False
	return True


def handle_profile_upload(file_objects,did,):
	urls = []
	profile_storage = MediaStorage()
	if file_objects is None:
		return None
	for index,key in enumerate(file_objects):
		hash_str = str(hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest())
		file_name = f'profile-{did}-{hash_str}'
		file_path = os.path.join(file_name)
		if not profile_storage.exists(file_path):
			profile_storage.save(file_path,file_objects[key])
			link = str(profile_storage.url(file_path))
			partition = env('AWS_S3_MEDIA_FOLDER')
			link_part = link.split(f'/{partition}/')
			link = f"{partition}/"+link_part[1]
			urls.append(link)

	return urls




def handle_post_upload(file_objects,postid,):
	urls = []
	post_storage = MediaStorage()
	if file_objects is None:
		return None
	for index,key in enumerate(file_objects):
		hash_str = str(hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest())
		file_name = f'post-{postid}-{hash_str}'
		file_path = os.path.join(file_name)
		if not post_storage.exists(file_path):
			post_storage.save(file_path,file_objects[key])
			link = str(post_storage.url(file_path))
			partition = env('AWS_S3_MEDIA_FOLDER')
			link_part = link.split(f"/{partition}/")
			link = f"{partition}/"+link_part[1]
			urls.append(link)
	return urls

def handle_fake_upload(file_object,uid,):
	urls = []
	post_storage = MediaStorage()
	if file_object is None:
		return None

	hash_str = str(hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest())
	file_name = f'post-{uid}-{hash_str}'
	file_path = os.path.join(file_name)
	if not post_storage.exists(file_path):
		post_storage.save(file_path,file_object)
		link = str(post_storage.url(file_path))
		partition = env('AWS_S3_MEDIA_FOLDER')
		link_part = link.split(f"/{partition}/")
		link = f"{partition}/"+link_part[1]
		urls.append(link)
	return urls


def handle_club_upload(file_objects,club_id):
	urls = {}
	post_storage = MediaStorage()
	if not file_objects:
		return None
	# for index,key in enumerate(file_objects):
	if 'profile_image' in file_objects:
		hash_str = str(hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest())
		file_name = f'club-profile-{club_id}-{hash_str}'
		file_path = os.path.join(file_name)
		if not post_storage.exists(file_path):
			post_storage.save(file_path,file_objects['profile_image'])
			link = str(post_storage.url(file_path))
			partition = env('AWS_S3_MEDIA_FOLDER')
			link_part = link.split(f"/{partition}/")
			link = f"{partition}/"+link_part[1]
			urls['profile_image']=link

	if 'cover_image' in file_objects:
		hash_str = str(hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest())
		file_name = f'club-cover-{club_id}-{hash_str}'
		file_path = os.path.join(file_name)
		if not post_storage.exists(file_path):
			post_storage.save(file_path,file_objects['cover_image'])
			link = str(post_storage.url(file_path))
			partition = env('AWS_S3_MEDIA_FOLDER')
			link_part = link.split(f"/{partition}/")
			link = f"{partition}/"+link_part[1]
			urls['cover_image'] = link
	return urls


def handle_page_upload(file_objects,page_id):
	urls = {}
	post_storage = MediaStorage()
	if not file_objects:
		return None
	# for index,key in enumerate(file_objects):
	if 'profile_image' in file_objects:
		hash_str = str(hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest())
		file_name = f'page-profile-{page_id}-{hash_str}'
		file_path = os.path.join(file_name)
		if not post_storage.exists(file_path):
			post_storage.save(file_path,file_objects['profile_image'])
			link = str(post_storage.url(file_path))
			partition = env('AWS_S3_MEDIA_FOLDER')
			link_part = link.split(f"/{partition}/")
			link = f"{partition}/"+link_part[1]
			urls['profile_image']=link

	if 'cover_image' in file_objects:
		hash_str = str(hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest())
		file_name = f'page-cover-{page_id}-{hash_str}'
		file_path = os.path.join(file_name)
		if not post_storage.exists(file_path):
			post_storage.save(file_path,file_objects['cover_image'])
			link = str(post_storage.url(file_path))
			partition = env('AWS_S3_MEDIA_FOLDER')
			link_part = link.split(f"/{partition}/")
			link = f"{partition}/"+link_part[1]
			urls['cover_image'] = link
	return urls


def delete_media_files(media_links):
	if media_links is not None:
		for each in media_links:
			if each is not None:
				link = each.split("?")[0]
				if default_storage.exists(link):
					default_storage.delete(link)
		else:
			return True
	else:
		return True


def FindTopPost(person):
	return person.posts.order_by('-created_at').first()


def calculate_age(year):
	year = int(year)
	return datetime.now().year - year




# AWS Credentials
AWS_ACCESS_KEY_ID = env('AWS_SNS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SNS_SECRET_ACCESS_KEY')
AWS_REGION_NAME = env('AWS_SNS_REGION_NAME')
SENDER_ID = env('SENDER_ID')

def sendSMS(phone,msg):
	# Create an SNS client
	client = boto3.client(
	    "sns",
	    aws_access_key_id=AWS_ACCESS_KEY_ID,
	    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
	    region_name=AWS_REGION_NAME
	)

	# Send your sms message.
	try:
		response = client.publish(
		    PhoneNumber=phone,
		    Message=msg,
		    MessageAttributes={
		        'string': {
		            'DataType': 'String',
		            'StringValue': 'String',
		        },
		        'AWS.SNS.SMS.SenderID': {
		            'DataType': 'String',
		            'StringValue': SENDER_ID
		        },
		        'AWS.SNS.SMS.SMSType': {
		            'DataType': 'String',
		            'StringValue': 'Transactional'
		        }
		    }
		)
	except:
		return False
	else:
		return True


# def binary_filter(person,page_number=1):
# 	range_up = (page_number or 1)*10
# 	range_down = range_up-10
# 	if person.gender_preference is not None and person.zone is not None:
# 		persons  = person.nodes.filter(Q(gender=person.gender_preference),Q(zone=person.zone),Q(did__ne=person.did))[range_down:range_up]
# 		return persons
# 	else:
# 		return list(),0

def match_count(person):
	if person.gender_preference is not None and person.zone is not None:
		persons  = person.nodes.filter(Q(gender=person.gender_preference),Q(zone=person.zone),Q(did__ne=person.did))
		return len(persons)
	else:
		return 0


# def static_and_dynamic_filter(person,page_number):
# 	persons = binary_filter(person,page_number)
# 	match_list = []
# 	#language_preference points
# 	# start = time.time()
# 	for each in persons:
# 		score = 0
# 		if (each.language_preference1 is not None and person.language_preference1 is not None) and each.language_preference1 == person.language_preference1:
# 			score += 100
# 		if (each.language_preference2 is not None and person.language_preference2 is not None) and each.language_preference2 == person.language_preference2:
# 			score += 100
# 		if (each.language_preference3 is not None and person.language_preference3 is not None) and  each.language_preference3 == person.language_preference3:
# 			score += 100		

# 		#interests points

# 		if each.interests and person.interests:
# 			for interest in each.interests:
# 				if interest in person.interests:
# 					score += 10

# 		max_club_list = each.clubs.all() if len(each.clubs.all())>len(person.clubs.all()) else person.clubs.all()
# 		min_club_list = each.clubs.all() if len(each.clubs.all())<len(person.clubs.all()) else person.clubs.all()

# 		for club in min_club_list:
# 			if club in max_club_list:
# 				score += 100


# 		info = each.full_profile_info(person)
# 		# info['match_score'] = score
# 		# match_list.append(info)
# 	end = time.time()
# 	print("time:",end-start)
# 	return sorted(match_list, key=lambda d: d['match_score'],reverse=True)

