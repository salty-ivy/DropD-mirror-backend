from django.conf import settings
from django.db.models.signals import post_save , post_delete
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from authUser.models import Users
from neoUserModel.models import Person

@receiver(post_save,sender=settings.AUTH_USER_MODEL)
def tokenGenerator(sender,instance=None,created=False,**kwargs):
	if created:
		Token.objects.create(user=instance)


@receiver(post_save,sender=settings.AUTH_USER_MODEL)
def create_personNode(sender,instance=None,created=None,**kwargs):
	if created:
		if not instance.is_internal:
			personNode = Person(did=instance.id,uid=instance.uid)
			# personNode.created_at = instance.created_at
			personNode.save()
			if instance.email:
				personNode.email = instance.email
				personNode.save()
			if instance.phone:
				personNode.phone = instance.phone
				personNode.save()
		else:
			pass
	else:
		if not instance.is_internal:
			personNode = Person.nodes.get(did=instance.id)
			if instance.email:
				personNode.email = instance.email
				personNode.save()
			if instance.phone:
				personNode.phone = instance.phone
				personNode.save()

@receiver(post_delete,sender=Users)
def deletePersonNode(sender,instance=None,**kwargs):
	if instance is not None: #and (not instance.is_superuser) and (not instance.is_staff):
		try:
			personNode = Person.nodes.get(did=instance.id)
		except:
			personNode = None
		if personNode is not None:
			personNode.total_delete()