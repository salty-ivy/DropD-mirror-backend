from django.core.management.base import BaseCommand , CommandError
from authUser.models import Users
from neoUserModel.models import Person


class Command(BaseCommand):
	def handle(self,*args,**options):
		persons = Person.nodes.all()
		for each in persons:
			try:
				user = Users.objects.get(id=each.did)
				each.uid = user.uid
				each.save()
			except:
				self.stdout.write(f"ERROR: User Not Found",ending="\n")

		else:
			self.stdout.write(self.style.SUCCESS(f"UIDs successfully set"))
