# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from common.models import VersionCategory


class PrepayForm(forms.Form):
    version = forms.CharField(
        required=True,
        max_length=20
    )
    city_id = forms.ImageField(
        required=False
    )
    logo = forms.ImageField(
        required=False,
        error_messages={'required': u'请选择有效的图片文件！',
                        'invalid': u'请选择有效的图片文件！',
                        'missing': u'请选择有效的图片文件！',
                        'empty': u'请选择有效的图片文件！',
                        'invalid_image': u'请选择有效的图片文件！'}
    )
    slogan = forms.CharField(
        required=False,
        max_length=20
    )

    def clean(self):
        version_code = self.cleaned_data.get('version')
        city_id = self.cleaned_data.get('city_id')
        logo = self.cleaned_data.get('logo')
        slogan = self.cleaned_data.get('slogan')
        try:
            version = VersionCategory.objects.get(code=version_code)
            if version.can_customize_city:
                if not city_id:
                    raise ValidationError('缺少参数')
                try:
                    city_id, city_name, country_id, country_name = version.check_city(city_id)
                except Exception as e:
                    raise str(e)
            if version.can_customize_logo:
                if (not logo) or (not slogan):
                    raise ValidationError('缺少参数')
        except ObjectDoesNotExist:
            raise ValidationError('版本无效')
        return self.cleaned_data


class NotifyForm(forms.Form):

    return_code = forms.CharField(max_length=16)
    return_msg = forms.CharField(max_length=128, required=False)
    appid = forms.CharField(max_length=32)
    mch_id = forms.CharField(max_length=32)
    nonce_str = forms.CharField(max_length=32)
    sign = forms.CharField(max_length=32)
    result_code = forms.CharField(max_length=16)
    openid = forms.CharField(max_length=128)
    trade_type = forms.CharField(max_length=16)
    bank_type = forms.CharField(max_length=16)
    total_fee = forms.IntegerField()
    cash_fee = forms.CharField(max_length=16)
    transaction_id = forms.CharField(max_length=32)
    out_trade_no = forms.CharField(max_length=32)
    time_end = forms.CharField(max_length=14)
