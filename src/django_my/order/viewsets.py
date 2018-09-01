# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.decorators import permission_classes as permission_decorator
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny

from libs.utils import ResultResponse
from libs.utils import str_to_int
from mjtt_django.errors import Success, Failed

from people.models import CustomUser
from people.models import Administrator
from people.permissions import CustomUserIsAuthenticated
from people.permissions import AdministratorIsAuthenticated

from .models import PurchaseItem
from .models import Order
from .models import STATUS_AS_COMMITTED

from .serializers import OrderSerializer
from .serializers import PurchaseItemSerializer
from .serializers import FreePurchaseItemSerializer


class OrderViewSet(viewsets.ModelViewSet):
    model = Order
    serializer_class = OrderSerializer
    search_fields = ('out_trade_no', )
    ordering = ('-dt_granted', )
    permission_classes = (CustomUserIsAuthenticated, )

    def get_queryset(self):
        queryset = self.model.objects.filter(status=STATUS_AS_COMMITTED)
        if 'user_pk' in self.kwargs:
            queryset = queryset.filter(user_id=self.kwargs['user_pk'])
        if 'version' in self.request.query_params:
            queryset = queryset.filter(version__code=self.request.query_params['version'])
        return queryset


class AdminOrderViewSet(OrderViewSet):
    search_fields = ('user__id', 'user__username')
    permission_classes = (AdministratorIsAuthenticated, )

    def get_queryset(self):
        queryset = self.model.objects.filter(status=STATUS_AS_COMMITTED)
        if 'version' in self.request.query_params:
            queryset = queryset.filter(version__code=self.request.query_params['version'])
        return queryset


class FreePurchaseItemViewSet(viewsets.ModelViewSet):
    model = PurchaseItem
    serializer_class = FreePurchaseItemSerializer
    permission_classes = (CustomUserIsAuthenticated, )
    ordering = ('-dt_created', )

    def get_queryset(self):
        queryset = PurchaseItem.objects.all()
        return queryset


class PurchaseItemViewSet(viewsets.ModelViewSet):
    model = PurchaseItem
    serializer_class = PurchaseItemSerializer
    search_fields = ('item_pname', 'item_name')
    permission_classes = (CustomUserIsAuthenticated, )

    def get_queryset(self):
        queryset = PurchaseItem.objects.all().order_by('-dt_created')
        if 'user_pk' in self.kwargs:
            queryset = queryset.filter(user_id=self.kwargs['user_pk'])
        if 'version' in self.kwargs:
            queryset = queryset.filter(version__code=self.kwargs['version'])

        if 'time_type' in self.request.query_params:
            time_type = str_to_int(self.request.query_params['time_type'])
            if time_type == 1:
                today = timezone.now().date()
                one_month_ago = today - datetime.timedelta(days=30)
                queryset = queryset.filter(dt_created__date__gte=one_month_ago)
            elif time_type == 2:
                today = timezone.now().date()
                three_month_ago = today - datetime.timedelta(days=90)
                queryset = queryset.filter(dt_created__date__gte=three_month_ago)
            elif time_type == 3:
                queryset = queryset.filter(dt_expired__gte=timezone.now())
            elif time_type == 4:
                queryset = queryset.filter(dt_expired__lt=timezone.now())
        if 'version' in self.request.query_params:
            queryset = queryset.filter(version__code=self.request.query_params['version'])
        return queryset


class AdminPurchaseItemViewSet(PurchaseItemViewSet):
    permission_classes = (AdministratorIsAuthenticated, )
    serializer_class = PurchaseItemSerializer
    search_fields = ('user__id', 'user__username', 'item_name')

    def get_queryset(self):
        queryset = PurchaseItem.objects.all()
        if 'version' in self.request.query_params:
            queryset = queryset.filter(version__code=self.request.query_params['version'])
        if 'view_order' in self.request.query_params:
            viewed_count_order = str_to_int(self.request.query_params['view_order'])
            if viewed_count_order == 1:
                order_by = '-viewed_count'
            else:
                order_by = 'viewed_count'
            queryset = queryset.order_by(order_by)

        return queryset
