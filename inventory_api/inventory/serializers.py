from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, InventoryItem, InventoryChangeLog

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class InventoryItemSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    
    class Meta:
        model = InventoryItem
        fields = ['id', 'user', 'name', 'description', 'quantity', 'price', 
                  'category', 'category_name', 'date_added', 'last_updated']
        read_only_fields = ['date_added', 'last_updated', 'user']
    
    def create(self, validated_data):
        # Assign current user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class InventoryChangeLogSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    item_name = serializers.ReadOnlyField(source='inventory_item.name')
    
    class Meta:
        model = InventoryChangeLog
        fields = ['id', 'inventory_item', 'item_name', 'user', 'username', 
                  'previous_quantity', 'new_quantity', 'change_type', 'timestamp']
        read_only_fields = ['user', 'timestamp']