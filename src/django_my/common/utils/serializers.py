# -*- coding: utf-8 -*-
"""
@author demo <dongxlmo@163.com>
@file: serializers.py
@time 2018/4/9 下午12:05
"""
from collections import OrderedDict
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.settings import api_settings
from rest_framework.exceptions import ValidationError
ERROR_KEY = 'detail'


class ModelSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        if not isinstance(data, dict):
            message = self.error_messages['invalid'].format(
                datatype=type(data).__name__
            )
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            })

        ret = OrderedDict()
        errors = OrderedDict()
        fields = self._writable_fields

        for field in fields:
            validate_method = getattr(self, 'validate_' + field.field_name, None)
            primitive_value = field.get_value(data)
            try:
                validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except ValidationError as exc:
                errors[ERROR_KEY] = exc.detail
                break
            except DjangoValidationError as exc:
                errors[ERROR_KEY] = list(exc.messages)
                break
            except serializers.SkipField:
                pass
            else:
                serializers.set_value(ret, field.source_attrs, validated_value)

        if errors:
            raise ValidationError(errors)

        return ret
