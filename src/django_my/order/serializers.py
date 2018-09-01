# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied

from libs.time_utils import datetime_to_localtime
from common.utils.serializers import ModelSerializer
from common.models import VersionCategory
from common.serializers import VersionCategorySerializer

from people.models import CustomUser
from people.models import Administrator
from people.serializers import CommonCustomUserProfileSerializer
from .models import Order
from .models import PurchaseItem


class CurrentUser(object):
    def set_context(self, serializer_field):
        user = serializer_field.context['request'].user
        if isinstance(user, CustomUser):
            self.user = user
        else:
            self.user = None

    def __call__(self):
        return self.user


class CurrentVersion(object):
    def set_context(self, serializer_field):
        version_code = serializer_field.context['view'].kwargs.get('version', '')
        if version_code:
            try:
                self.version = VersionCategory.objects.get(code=version_code)
            except VersionCategory.DoesNotExist:
                raise NotFound
        else:
            self.version = None

    def __call__(self):
        return self.version


class CustomPrimaryKeyRelatedField(serializers.RelatedField):

    def __init__(self, **kwargs):
        self.pk_field = kwargs.pop('pk_field', None)
        super(CustomPrimaryKeyRelatedField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, value):
        if self.pk_field is not None:
            return self.pk_field.to_representation(value.pk)
        return value.pk


class UserPrimaryKeyRelatedField(CustomPrimaryKeyRelatedField):
    def to_representation(self, value):
        if self.pk_field is not None:
            return self.pk_field.to_representation(value.pk)
        return CommonCustomUserProfileSerializer(value).data


class VersionPrimaryKeyRelatedField(CustomPrimaryKeyRelatedField):
    def to_representation(self, value):
        if self.pk_field is not None:
            return self.pk_field.to_representation(value.pk)
        return VersionCategorySerializer(value).data


class OrderSerializer(ModelSerializer):
    user = UserPrimaryKeyRelatedField(
        read_only=True,
        default=CurrentUser(),
    )
    version = VersionPrimaryKeyRelatedField(
        read_only=True,
        default=CurrentVersion(),
    )
    pay_time = serializers.SerializerMethodField()
    city_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('out_trade_no', 'transaction_id', 'pay_time', 'city_count', 'user', 'version', 'amount_display')

    def get_pay_time(self, instance):
        if instance.dt_granted:
            return datetime_to_localtime(instance.dt_granted)
        return ''

    def get_city_count(self, instance):
        return PurchaseItem.objects.filter(order=instance).count()


class PurchaseItemSerializer(ModelSerializer):
    user = UserPrimaryKeyRelatedField(
        read_only=True,
        default=CurrentUser(),
    )
    version = VersionPrimaryKeyRelatedField(
        read_only=True,
        default=CurrentVersion(),
    )
    create_time = serializers.SerializerMethodField()
    expire_time = serializers.SerializerMethodField()
    url = serializers.CharField(max_length=256, required=False)

    class Meta:
        model = PurchaseItem
        fields = ('id', 'user', 'version', 'item_pid', 'item_pname', 'item_id', 'item_name',
                  'logo', 'slogan', 'viewed_count', 'download_count', 'url', 'image', 'create_time', 'expire_time')

    def get_create_time(self, instance):
        if instance.dt_created:
            return datetime_to_localtime(instance.dt_created)
        return ''

    def get_expire_time(self, instance):
        if instance.dt_expired:
            return datetime_to_localtime(instance.dt_expired)
        return ''


class FreePurchaseItemSerializer(PurchaseItemSerializer):
    class Meta:
        model = PurchaseItem
        fields = PurchaseItemSerializer.Meta.fields

    def create(self, validated_data):
        validated_data['version'] = VersionCategory.objects.get_or_create(code='free')[0]
        validated_data['succeed'] = True
        return super(FreePurchaseItemSerializer, self).create(validated_data)

