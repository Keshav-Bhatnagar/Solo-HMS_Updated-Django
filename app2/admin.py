from django.contrib import admin
from app2.models import Form

# Register your models here.
admin.site.register(Form)

from django.contrib import admin
from .models import MessMenu

admin.site.register(MessMenu)

from django.contrib import admin
from .models import LostItem, FoundItem, ClaimRequest

@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date_lost', 'location', 'created_at', 'is_claimed')
    list_filter = ('category', 'is_claimed', 'date_lost')
    search_fields = ('title', 'description', 'location')

@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date_found', 'location', 'created_at', 'is_claimed')
    list_filter = ('category', 'is_claimed', 'date_found')
    search_fields = ('title', 'description', 'location')

@admin.register(ClaimRequest)
class ClaimRequestAdmin(admin.ModelAdmin):
    list_display = ('item', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('item__title', 'message')

from django.contrib import admin
from .models import MessRules
from .forms import MessRulesForm

class MessRulesAdmin(admin.ModelAdmin):
    form = MessRulesForm
    list_display = ['rule_short', 'order', 'created_at']
    ordering = ['order', 'created_at']

    def rule_short(self, obj):
        return obj.rule[:50] + ('...' if len(obj.rule) > 50 else '')
    rule_short.short_description = 'Rule'

admin.site.register(MessRules, MessRulesAdmin)