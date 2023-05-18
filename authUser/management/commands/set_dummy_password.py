from django.core.management.base import BaseCommand , CommandError
from authUser.models import Users
from neoUserModel.models import Person


class Command(BaseCommand):
	def handle(self,*args,**options):
		users = Users.objects.all()
		for user in users:
			# user = Users.objects.get(id=each.did)
			# each.uid = user.uid
			# each.save()
			if not user.is_superuser==True:
				user.set_password("testing321")
				user.save()
		else:
			self.stdout.write(self.style.SUCCESS(f"Dummy passwords successfully set"))