from django.core.management.base import BaseCommand,CommandError
from authUser.models import  *
from neoUserModel.models import *
from faker import Faker
from random import randint
from datetime import datetime
from authUser.helper import handle_fake_upload
from django.conf import settings
import os

pages_and_clubs_directory = settings.FAKE_IMAGES+"/pages_and_clubes"
posts_directory = settings.FAKE_IMAGES+"/posts"
profiles_directory = settings.FAKE_IMAGES+"/profiles"

posts_files = os.listdir(posts_directory)
profiles_files = os.listdir(profiles_directory)
files = os.listdir(pages_and_clubs_directory)
class Command(BaseCommand):
	def add_arguments(self,parser):
		parser.add_argument("number_of_users",nargs="+",type=int)
	def handle(self,*args,**options):
		num = options['number_of_users'][0]
		fake = Faker()
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
		zone_list = ('love grounds','open marriage commune','seniors in love again',)
		interests =(
				'Golf',
				'Cycling',
				'Cricket',
				'Swimming',
				'Tennis',
				'Running',
				'Badminton',
				'Yoga',
				'Meditation',
				'Fiction',
				'Fasting',
				'Gaming',
				'Painting',
				'Film-making',
				'Philosophy',
				'Baking',
				'Dance',
				'Poetry',
				'Dogs',
				'Simple Living',
				'Luxuries',
				'Pottery',
				'Cats',
				'Gardening',
				'Fiction',
				'Non-Fiction',
				'Photography',
				'Music',
				'Outdoors',
				'Cooking',
				'Religion',
				'Marijuana',
				'Netflix',
				'Acting',
				'Parenting',
				'Comedy',
				'LTR',
				'Startups',
				'Fashion',
				'DTF',
				'BDSM',
				'Sex Toys',
				'Tantra',
				'FWB',
				'Crypto',
				'Nudism',
				'Politics',
				'Group Sex',
			)
		languages = ['Hindi','English','Punjabi']
		self.stdout.write(f"Seeding {num} users........\n")

		for _ in range(num):
			user = Users.objects.create(phone=fake.msisdn()[0:12])
			user.email = fake.unique.email()
			try:
				user.email_verified = True
				user.phone_verified = True
				user.save()
			except Exception as error:
				self.stdout.write("VALIDATION-ERROR:",error)
			else:
				temp_languages = languages.copy()
				person = Person.nodes.get(did=user.id)
				name = fake.unique.name()
				person.nick_name = name.split()[0]
				person.full_name = name
				person.city = fake.city()
				person.country = fake.country()
				person.zone = zone_list[randint(0,2)]
				person.gender = ["male","female",].pop(randint(0,1))
				person.gender_preference = ["male","female",].pop(randint(0,1))
				person.marital_status = ["Married","Unmarried"].pop(randint(0,1))
				person.language_preference1 = temp_languages.pop(randint(0,len(temp_languages)-1))
				person.language_preference2 = temp_languages.pop(randint(0,len(temp_languages)-1))
				person.language_preference3 = temp_languages.pop()
				person.year_of_birth = fake.year()
				person.age = datetime.now().year - int(person.year_of_birth)
				person.save()
				temp_files = profiles_files.copy()
				file = open(settings.FAKE_IMAGES+f"/profiles/{temp_files.pop(randint(0,len(temp_files)-1))}",'rb')
				person.profile_pics = handle_fake_upload(file,person.did)
				file.close()
				person.save()



				copy = attributes_list.copy()
				attributes=[]
				######################
				# self.stdout.write(f"User:\n")
				# self.stdout.write(f"{len(attributes_list)}")

				for _ in range(5):
					length = len(copy)
					attributes.append(copy.pop(randint(0,length-1)))
				else:
					t = tuple(attributes)
					attributes = list(t)
					person.person_kundli_attributes = attributes if len(attributes)==5 else None


				copy = attributes_list.copy()
				attributes = []
				#####################

				for _ in range(5):
					length = len(copy)
					attributes.append(copy.pop(randint(0,length-1)))
				else:
					t = tuple(attributes)
					attributes = list(t)
					person.partner_kundli_attributes = attributes if len(attributes)==5 else None

				#####################


				temp_interests = list(interests)
				interests_push = []
				for _ in range(8):
					length = len(temp_interests)
					interests_push.append(temp_interests.pop(randint(0,length-1)))
					# interests_push.append(temp_interests.pop())
				else:
					t = tuple(interests_push)
					interests_push = list(interests_push)
					person.interests = interests_push if len(interests_push)==8 else None
				person.save()

				#### post for each

				post = Post()
				post.text = fake.text()
				post.created_at = datetime.now()
				post.save()
				post.postFrom.connect(person)
				post.save()
				temp_files = posts_files.copy()
				file = open(settings.FAKE_IMAGES+f"/posts/{temp_files.pop(randint(0,len(temp_files)-1))}",'rb')
				post.imageLink = handle_fake_upload(file,post.pid)
				file.close()
				post.save()


				### clubs for each
				listed_files = files.copy()
				club = Club(club_name=fake.unique.job(),description=fake.text(),category=interests[randint(0,len(interests)-1)],created_at=datetime.now()).save()
				club.owner.connect(person)
				club.save() 
				profile_file = open(settings.FAKE_IMAGES+f"/pages_and_clubes/{listed_files.pop(randint(0,len(listed_files)-1))}","rb")
				club.profile_image = handle_fake_upload(profile_file,club.club_id)[0]
				profile_file.close()
			

				cover_file = open(settings.FAKE_IMAGES+f"/pages_and_clubes/{listed_files.pop(randint(0,len(listed_files)-1))}","rb")
				club.cover_image = handle_fake_upload(cover_file,club.club_id)[0]
				cover_file.close()
				club.save()
				person.clubs.connect(club)
				person.save()

				### page for each
				page = Page(page_name=fake.unique.job(),description=fake.text(),created_at=datetime.now()).save()
				page.owner.connect(person)
				page.save()

				profile_file = open(settings.FAKE_IMAGES+f"/pages_and_clubes/{listed_files.pop(randint(0,len(listed_files)-1))}","rb")
				page.profile_image = handle_fake_upload(profile_file,page.page_id)[0]
				profile_file.close()
				

				cover_file = open(settings.FAKE_IMAGES+f"/pages_and_clubes/{listed_files.pop(randint(0,len(listed_files)-1))}","rb")
				page.cover_image = handle_fake_upload(cover_file,page.page_id)[0]
				cover_file.close()
				page.save()

		else:
			self.stdout.write(self.style.SUCCESS("Database seeded with users successfully"))


		#### post