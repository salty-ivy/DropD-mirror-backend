from rest_framework import serializers
from authUser.models import Users,Person_Interests_List



class InterestsSerializer(serializers.ModelSerializer):
	class Meta:
		model = Person_Interests_List
		# fields = "__all__"
		exclude = ('id',)