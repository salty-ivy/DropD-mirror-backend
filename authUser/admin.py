from django.contrib import admin

# Register your models here.
from authUser.models import *

class UserAdmin(admin.ModelAdmin):
	search_fields = ('email','id','phone','uid')
	list_display = ('email','phone','uid','id')
	# ordering = ('did')

	
admin.site.register(Users,UserAdmin)
admin.site.register(User_Signups)
admin.site.register(Person_Interests_List)