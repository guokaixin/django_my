import os
import oss2
import logging
import mimetypes
import posixpath
from urlparse import urlparse

from io import BytesIO
from StringIO import StringIO

from django.utils.encoding import force_text
from django.utils.encoding import filepath_to_uri
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import Storage
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import SuspiciousOperation

from oss.pkg_info import version

if not version == '0.4.6':
    raise ImproperlyConfigured(
            'Requires OSS SDK 0.4.6 or higher.'
            'See https://help.aliyun.com/.'
            )

from oss.oss_api import OssAPI
from oss.oss_util import convert_header2map, safe_get_element


def setting(name, default=None):
    return getattr(settings, name, default) or os.getenv(name)


class OSSStorageException(Exception):
    pass


class OSSStorage(Storage):
    """
    Django Storage for Aliyun OSS
    """
    ACCESS_KEY = setting('OSS_ACCESS_KEY_ID')
    ACCESS_SECRET = setting('OSS_SECRET_ACCESS_KEY')
    BUCKET_NAME = setting('OSS_STORAGE_BUCKET_NAME')
    ACCESS_ENDPOINT = setting('OSS_ACCESS_ENDPOINT')
    ACCESS_HEADERS = setting('OSS_ACCESS_HEADERS') or {}
    ACCESS_PORT = setting('OSS_ACCESS_PORT') or 80
    ACL = setting('OSS_DEFAULT_ACL') or 'public-read'
    IS_SECURITY = setting('OSS_IS_SECURITY') or False
    STS_TOKEN = setting('OSS_STS_TOKEN') or None

    _connection = None

    def __init__(self, access_endpoint=None, access_key=None, access_port=None, acl=None, bucket_name=None, headers=None, is_security=None, secret_key=None, sts_token=None):
        self.access_endpoint = access_endpoint or self.ACCESS_ENDPOINT
        self.access_key = access_key or self.ACCESS_KEY
        self.access_port = access_port or self.ACCESS_PORT
        self.access_secret = secret_key or self.ACCESS_SECRET
        self.acl = acl or self.ACL
        self.bucket = bucket_name or self.BUCKET_NAME
        self.headers = headers or self.ACCESS_HEADERS
        self.is_security = is_security or self.IS_SECURITY
        self.sts_token = sts_token or self.STS_TOKEN

    @property
    def connection(self):
        if self._connection is None:
            self._connection = OssAPI(
                    host=self.access_endpoint,
                    access_id=self.access_key,
                    secret_access_key=self.access_secret,
                    port=self.access_port,
                    is_security=self.is_security,
                    sts_token=self.sts_token,
                    )
        return self._connection

    def _clean_name(self, name):
        clean_name = posixpath.normpath(name).replace('\\', '/')
        clean_name = clean_name.replace(' ', '_')
        if name.endswith('/') and not clean_name.endswith('/'):
            return clean_name + '/'
        else:
            return clean_name

    def get_valid_name(self, name):
        return self._clean_name(name)

    def get_available_name(self, name, max_length=None):
        return self._clean_name(name)

    def _open(self, name, mode='rb', *args, **kwargs):
        name = self._clean_name(name)
        res = self.connection.get_object(self.bucket, name, self.headers)
        if res.status >= 300:
            raise OSSStorageException('OSSStorageError: %s' % res.read())
        return File(StringIO(res.read()), name=name)

    def _save(self, name, content_file):
        name = self._clean_name(name)
        content_type = mimetypes.guess_type(name)[0] or 'application/x-octet-stream'
        if hasattr(content_file, 'chunks'):
            content = b''.join(content_file.chunks())
        else:
            content = content_file.read()
        content_len = str(len(content))
        self.headers.update({
            'x-oss-acl': self.acl,
            'Content-Type': content_type,
            'Content-Length': content_len,
            })
        res = self.connection.put_object_from_fp(self.bucket, name, content_file, content_type, self.headers)
        if res.status >= 300:
            raise OSSStorageException('OSSStorage Error: %s' % res.read())
        return name

    def delete(self, name):
        name = self._clean_name(name)
        res = self.connection.delete_object(self.bucket, name)
        if res.status != 204:
            raise OSSStorageException('OSSStorageError: %s' % res.read())
    
    def listdir(self, prefix=''):
        return self.connection.list_objects_dirs(self.bucket, prefix)

    def exists(self, name):
        name = self._clean_name(name)
        res = self.connection.head_object(self.bucket, name)
        return res.status == 200

    def file_info(self, name):
        name = self._clean_name(name)
        res = self.connection.head_object(self.bucket, name)
        headers = convert_header2map(res.getheaders())
        return headers

    def size(self, name):
        file_info = self.file_info(name)
        return safe_get_element('content-length', file_info) if file_info else 0

    def usage(self):
        pass

    def url(self, name):
        name = self._clean_name(name)
        # name = filepath_to_uri(name)
        url = self.connection.sign_url('GET', self.bucket, name)
        url_ = urlparse(url)
        return '%s://%s%s' % (url_.scheme, url_.netloc, url_.path)
