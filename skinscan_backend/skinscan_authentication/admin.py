from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'email', 'username', 'full_name', 'is_email_verified',
        'analysis_count', 'conversation_count', 'is_active', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_superuser', 'is_email_verified',
        'created_at', 'last_login'
    ]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'phone_number',
                       'date_of_birth', 'profile_picture')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
        ('Verification', {
            'fields': ('is_email_verified',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']

    def analysis_count(self, obj):
        count = obj.analysis_count
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return count

    analysis_count.short_description = 'Analyses'

    def conversation_count(self, obj):  # Add this method
        count = obj.conversation_count
        if count > 0:
            return format_html(
                '<span style="color: blue; font-weight: bold;">{}</span>',
                count
            )
        return count

    conversation_count.short_description = 'Chats'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'skin_type', 'profile_visibility',
        'email_notifications', 'created_at'
    ]
    list_filter = [
        'skin_type', 'profile_visibility', 'email_notifications',
        'analysis_reminders', 'created_at'
    ]
    search_fields = ['user__email', 'user__username', 'location']
    raw_id_fields = ['user']

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Profile Details', {
            'fields': ('bio', 'location', 'website', 'skin_type')
        }),
        ('Medical Information', {
            'fields': ('medical_conditions',),
            'description': 'Optional medical information for reference'
        }),
        ('Privacy Settings', {
            'fields': ('profile_visibility',)
        }),
        ('Notification Preferences', {
            'fields': ('email_notifications', 'analysis_reminders')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'