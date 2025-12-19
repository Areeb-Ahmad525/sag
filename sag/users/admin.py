from django.contrib import admin
from .models import UserProfile,LoginActivity
from django.utils.html import format_html
from .models import Team

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

@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'login_time', 'logout_time', 'ip_address')
    search_fields = ('user__email', 'ip_address')
    list_filter = ('status',)




@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_id', 'name', 'manager', 'created_at')
    search_fields = ('name', 'team_id')
    filter_horizontal = ('members',) # Makes the ManyToMany selection much easier