from django.core.management.base import BaseCommand , CommandError
from authUser.models import Person_Interests_List

class Command(BaseCommand):
	def handle(self,*args,**options):
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
		count=0
		for interest in interests:
			if Person_Interests_List.objects.filter(name=interest).exists():
				pass
			else:
				Person_Interests_List.objects.create(name=interest)
				count += 1
		self.stdout.write(self.style.SUCCESS(f"Person_Interests_List populated successfully"))
		self.stdout.write(self.style.SUCCESS(f"{count} interests created"))
		self.stdout.write(self.style.SUCCESS(f"total interests: {Person_Interests_List.objects.all().count()}"))

