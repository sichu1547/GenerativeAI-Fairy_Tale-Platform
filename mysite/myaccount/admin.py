from django.contrib import admin
from .models import UserSessionData, Profile

@admin.register(UserSessionData)
class UserSessionDataAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'get_decoded']

    def session_id(self, obj):
        return obj.id

    def get_decoded(self, obj):
        data = obj.session_data
        user_id = data.get('user_id', 'N/A')
        session_index = data.get('session_index', 'N/A')
        return f"User ID: {user_id}, Session Index: {session_index}"

    get_decoded.short_description = 'Decoded Data'
    
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'avatar')