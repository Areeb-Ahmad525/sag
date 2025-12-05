from django.contrib import admin
from .models import UserProfile
from django.utils.html import format_html

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_email', 'role', 'phone', 'status', 'profile_image')
    list_filter = ('role', 'status')
    search_fields = ('name', 'user__email', 'phone')

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    def profile_image(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" />', obj.profile_picture.url)
        return "-"
    profile_image.short_description = 'Profile Picture'
