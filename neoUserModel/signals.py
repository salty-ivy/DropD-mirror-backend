from django.conf import settings
from django.db.models.signals import post_save , post_delete
from django.dispatch import receiver
from authUser.models import Users
from neoUserModel.models import *

# def deleteComments(sender,instance,signal,**kwargs):
# 	if instance is not None:
# 		try:
# 			comments = instance.comment.all()
# 		except:
# 			comments = None
# 		if comments is not None:
# 			for comment in comments:
# 				comment.delete()
# 		else:
# 			print("!!!!!!!!!!!!!!did not get it")
			
# post_delete.connect(deleteComments,sender=Post)