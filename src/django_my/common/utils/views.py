# -*- coding: utf-8 -*-
"""
@author demo <dongxlmo@163.com>
@file: views.py
@time 2018/4/9 下午2:08
"""
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(response.data, dict):
            detail_data = response.data.get('detail')
            if detail_data:
                if isinstance(detail_data, list):
                    detail_data = detail_data[0]
                elif isinstance(detail_data, dict):
                    detail_data = detail_data.values()[0]
                response.data['detail'] = detail_data
        if isinstance(response.data, list):
            data = response.data

            response.data = {}
            response.data['detail'] = data[0]
            del data

    return response
