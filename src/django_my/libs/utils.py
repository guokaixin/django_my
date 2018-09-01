# -*- coding: utf-8 -*-
import re
import os
import hashlib
import zipfile
import logging
import shutil
from django.http import JsonResponse
logger = logging.getLogger('lushu.utils')


class ResultResponse(JsonResponse):
    def __init__(self, result, data='', msg='', safe=True, status=200):
        """
        Result represent the error code, while bad things happend,
        and the data gives a blank string default.

        Using JsonResponse to make sure the `Content-Type` header
        is set to 'application/json'.
        """

        content = {'code': result, 'data': data, 'msg': msg}
        super(ResultResponse, self).__init__(content, status=status, safe=safe)


def force_utf8(data):
    """
    convert data to UTF8
    :param data: data will to convert
    :param :return: converted data
    """
    if isinstance(data, unicode):
        return data.encode("utf-8")
    elif isinstance(data, list):
        return [force_utf8(i) for i in data]
    elif isinstance(data, dict):
        return {force_utf8(i): force_utf8(data[i]) for i in data}
    return data


def is_validate_china_mobile(mobile):
    """
    合法中国电话号码，仅限手机号
    """
    if re.match(r'^(86)?1[35678]\d{9}$|^(86)?147\d{8}$', mobile.strip()):
        return True
    return False


def is_validate_username(username):
    """
    中文字母数字下划线
    """
    if username:
        if isinstance(username, str):
            nickname = username.strip().decode('utf-8')
        else:
            nickname = username.strip()
        if re.match(ur"[\u4e00-\u9fa5\w ]*", nickname).group() == nickname:
            return True
        return False
    else:
        return True


def params_to_str(params):
    return "&".join(['%s=%s' % (key, params[key]) for key in sorted(params)])


def str_to_params(pstr):
    try:
        lst = pstr.strip().split('&')
        return {s.split('=')[0]: s.split('=')[1] for s in lst}
    except Exception as e:
        logger.info('str_to_params err: {}, pstr: {}'.find(str(e), pstr))
        return {}


def str_to_int(data):
    try:
        return int(data)
    except Exception as e:
        logger.info('str_to_int err: {}, data: {}'.find(str(e), data))
        return 0


def archive_zip_package(target_path):
    dest_path = '%s.zip' % target_path
    if os.path.exists(dest_path):
        os.remove(dest_path)
    z = zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(target_path):
        for filename in filenames:
            if not filename.startswith('.'):
                z.write(os.path.join(dirpath, filename))
    z.close()
    try:
        zp = zipfile.ZipFile(dest_path)
        zp.close()
        shutil.rmtree(target_path)
        logger.info('Archived zip package {} done, Size: {}KB'.format(
            dest_path, '%.2f' % (os.path.getsize(dest_path) / 1024.0)))
    except:
        logger.info('zip package is broken, archive again!')
        archive_zip_package(target_path)
    return dest_path


def build_signature(param, key):
    """
    构造签名
    """
    temp_str = "&".join(["%s=%s" % (k, v) for k, v in
                         sorted(param.items()) if str(v) and k != "sign"])
    temp_str += "&key=%s" % key
    logger.info('build signature: %s' % temp_str)
    return hashlib.md5(temp_str).hexdigest().upper()
