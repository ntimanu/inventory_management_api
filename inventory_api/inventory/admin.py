from django.contrib import admin
from .models import Category, InventoryItem, InventoryChangeLog

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category', 'quantity', 'price', 'date_added', 'last_updated')
    list_filter = ('category', 'user')
    search_fields = ('name', 'description')
    date_hierarchy = 'date_added'

@admin.register(InventoryChangeLog)
class InventoryChangeLogAdmin(admin.ModelAdmin):
    list_display = ('inventory_item', 'user', 'previous_quantity', 'new_quantity', 'change_type', 'timestamp')
    list_filter = ('change_type', 'user')
    date_hierarchy = 'timestamp'