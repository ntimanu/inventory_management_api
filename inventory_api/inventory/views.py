from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from .models import Category, InventoryItem, InventoryChangeLog
from .serializers import (UserSerializer, CategorySerializer, 
                         InventoryItemSerializer, InventoryChangeLogSerializer)
from .permissions import IsOwnerOrReadOnly

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('id')  # Add ordering here
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
class InventoryItemViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'quantity', 'date_added']
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
      # Add ordering here
   
class InventoryItemViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'quantity', 'date_added']
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return InventoryItem.objects.filter(user=self.request.user).order_by('id')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        # Get the original item
        item = self.get_object()
        old_quantity = item.quantity
        
        # Save the updated item
        updated_item = serializer.save()
        new_quantity = updated_item.quantity
        
        # If quantity changed, log it
        if old_quantity != new_quantity:
            change_type = 'restock' if new_quantity > old_quantity else 'sale'
            if new_quantity == old_quantity:
                change_type = 'adjustment'
                
            InventoryChangeLog.objects.create(
                inventory_item=updated_item,
                user=self.request.user,
                previous_quantity=old_quantity,
                new_quantity=new_quantity,
                change_type=change_type
            )
    
    @action(detail=False, methods=['get'])
    def levels(self, request):
        queryset = self.get_queryset()
        
        # Filter for low stock if requested
        low_stock_threshold = request.query_params.get('low_stock')
        if low_stock_threshold:
            queryset = queryset.filter(quantity__lt=int(low_stock_threshold))
            
        # Additional filtering
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
            
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=float(min_price))
        if max_price:
            queryset = queryset.filter(price__lte=float(max_price))
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class InventoryChangeLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InventoryChangeLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['inventory_item', 'change_type']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']  # Default to most recent first
    
    def get_queryset(self):
        # Return only change logs for items owned by the current user
        return InventoryChangeLog.objects.filter(inventory_item__user=self.request.user)