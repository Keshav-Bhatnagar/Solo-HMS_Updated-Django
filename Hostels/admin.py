# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Hostel, Room, Allocation, StudentProfile,Feedback
from django.utils.html import format_html

# Custom User Admin
admin.site.site_header = "CampusNest Administration"
admin.site.index_title = "Welcome to CampusNest Admin Portal"
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'roll_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    
    
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'contact_number', 'profile_picture_preview')
    search_fields = ('user__email', 'contact_number')
    
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.profile_picture.url)
        return "-"
    profile_picture_preview.short_description = 'Profile Picture'

# Unregister default User and register CustomUser
# admin.site.unregister(CustomUser)
admin.site.register(CustomUser, CustomUserAdmin)



admin.site.site_title = "Hostel Management System"
# Hostel Admin with Image Preview
@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_floors', 'image_preview', 'features_list')
    list_filter = ('total_floors',)
    search_fields = ('name', 'features')
    
    def image_preview(self, obj):
        return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.main_image.url)
    image_preview.short_description = 'Preview'
    
    def features_list(self, obj):
        return ", ".join(obj.feature_list())
    features_list.short_description = 'Features'

# Room Admin with Advanced Filtering
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('hostel', 'room_number', 'room_type', 'ac_type', 'beds_status', 'price')
    list_filter = ('hostel', 'floor', 'room_type', 'ac_type')
    search_fields = ('room_number', 'amenities')
    
    def beds_status(self, obj):
        return f"{obj.occupied_beds}/{obj.total_beds}"
    beds_status.short_description = 'Occupancy'

# Allocation Admin with Action
@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'status', 'allocation_date')
    list_filter = ('status', 'room__hostel')
    search_fields = ('user__email', 'room__room_number')
    actions = ['approve_allocations']
    
    def approve_allocations(self, request, queryset):
        queryset.update(status='confirmed')
    approve_allocations.short_description = "Approve selected allocations"

# Student Profile Admin


# Admin Site Customization


admin.site.register(Feedback)