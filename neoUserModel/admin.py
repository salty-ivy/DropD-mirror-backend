from django.contrib import admin

# Register your models here.

from django_neomodel import admin as neo_admin
from .models import Person,Club,Page,Tags

class PersonAdmin(admin.ModelAdmin):
	list_display = ("email","phone","nick_name","uid","did",)
	search_fields = ("email","did","uid")
	ordering = ("-did",)

class ClubAdmin(admin.ModelAdmin):
	list_display = ("club_name","club_id","created_at")

class PageAdmin(admin.ModelAdmin):
	list_display = ("page_name","page_id","created_at")

neo_admin.register(Person,PersonAdmin)
neo_admin.register(Club,ClubAdmin)
neo_admin.register(Page,PageAdmin)