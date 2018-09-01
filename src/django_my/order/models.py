# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import qrcode
import hashlib
import datetime
import random
from cStringIO import StringIO
from hashlib import sha1
from django.db import models, transaction
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.utils import timezone

from common.utils.models import WithDeleteModel
from common.models import VersionCategory

from people.models import CustomUser
reload(sys)
sys.setdefaultencoding("utf-8")

ORDER_PREFIX_FOR_PAY = 'P'

STATUS_AS_FRESH = 1
STATUS_AS_CLOSED = 2
STATUS_AS_COMMITTED = 3


STATUS_CHOICES = (
    (STATUS_AS_FRESH, u'新事务'),
    (STATUS_AS_CLOSED, u'已关闭'),
    (STATUS_AS_COMMITTED, u'已完成'),
)


def generate_global_id():
    """ 生成订单号：两位（年）+ 一位（前两位+后四位校验和）+四位（月日）+ 六位（随机） """
    year_str = datetime.datetime.now().strftime('%y')
    date_str = datetime.datetime.now().strftime('%m%d')
    gen_str = sum([int(i) for i in u'%s%s' % (year_str, date_str)]) % 10
    return UniqueOrderId.objects.generate_unique_order_id(u'%s%d%s' % (year_str, gen_str, date_str))


def generate_qrcode(data):
    qr = qrcode.QRCode(
        version=6,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image()

    buf = StringIO()
    img.save(buf)
    return buf.getvalue()


def pay_qr_image_upload_to(instance, filename):
    sha1_hash = sha1(instance.pay_url).hexdigest()
    suffix = filename.split('.')[-1]
    args = [
            settings.UPLOAD_ROOT,
            'qr',
            '%s.%s' % (sha1_hash, suffix)
            ]
    return '/'.join(args)


class OrderManager(models.Manager):
    def create_consume_order(self, out_trade_no, user, version, amount, description='', pay_url=''):
        with transaction.atomic():
            # 创建消费记录
            order = self.model(user=user, comment=u'消费')
            order.out_trade_no = out_trade_no
            order.version = version
            order.description = description
            order.amount_display = amount
            order.amount_cents = int(order.amount_display * 100)
            order.status = STATUS_AS_FRESH
            order.pay_url = pay_url
            order.save()
            return order


class Order(models.Model):
    out_trade_no = models.CharField(u'订单号', max_length=20, db_index=True)
    transaction_id = models.CharField(u'微信支付ID', max_length=50, db_index=True, default=u'')
    user = models.ForeignKey(CustomUser, verbose_name=u'用户')
    version = models.ForeignKey(VersionCategory, verbose_name='版本类型')
    comment = models.CharField(u'备注', max_length=200, default=u'')
    description = models.TextField(u'订单记录描述', default=u'')
    count = models.PositiveIntegerField(u'购买商品数量', default=0)
    amount_display = models.FloatField(u'变动金额', default=0.0, help_text=u'以人民币元为单位')
    amount_cents = models.IntegerField(u'变动金额（计算用）', default=0, help_text=u'以人民币分为单位')
    status = models.SmallIntegerField(u'状态', db_index=True, default=STATUS_AS_FRESH, choices=STATUS_CHOICES)

    pay_url = models.CharField(u'微信支付的支付URL', max_length=256, blank=True, null=True)
    pay_image = models.ImageField(u'微信支付的二维码', upload_to=pay_qr_image_upload_to, blank=True, null=True)

    is_refunded = models.BooleanField("是否退款", db_index=True, default=False)
    dt_granted = models.DateTimeField(u'完成时间', null=True, blank=True)
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    objects = OrderManager()

    class Meta:
        verbose_name = '订单'
        verbose_name_plural = '订单'
        get_latest_by = 'id'

    def __unicode__(self):
        return '%s' % self.transaction_id

    @property
    def pay_qr_url(self):
        if self.pay_image:
            return self.pay_image.url
        return ''

    def grant_consume(self, transaction_id):
        if self.status == STATUS_AS_FRESH:
            with transaction.atomic():
                self.transaction_id = transaction_id
                self.status = STATUS_AS_COMMITTED
                self.dt_granted = timezone.now()
                self.save()


@receiver(post_save, sender="order.Order")
def order_post_save(sender, instance, created, **kwargs):
    if instance.pay_url and not instance.pay_image:
        image_path = pay_qr_image_upload_to(instance, 'pay.png')
        instance.pay_image.save(image_path, ContentFile(generate_qrcode(instance.pay_url)))
        instance.save()


class UniqueAuditIdManager(models.Manager):
    @staticmethod
    def generate_unique_order_id(prefix):
        ret_code = ''
        while not ret_code:
            for i in range(0, 6):
                ret_code += str(random.randint(0, 9))
            if UniqueOrderId.objects.filter(unique_id=(prefix + ret_code)).exists():
                ret_code = ''
            else:
                random_code = UniqueOrderId(unique_id=(prefix + ret_code))
                random_code.save()
                break
        return prefix + ret_code


class UniqueOrderId(models.Model):
    """ 订单号生成器 """
    unique_id = models.CharField(u'唯一编码', unique=True, db_index=True, max_length=20)
    dt_created = models.DateTimeField(u'生成时间', auto_now_add=True)
    objects = UniqueAuditIdManager()

    def __unicode__(self):
        return self.unique_id


def logo_upload_to(instance, filename):
    content = instance.logo.file.read()
    sha1_hash = sha1(content).hexdigest()
    suffix = filename.split('.')[-1]
    args = [
            settings.UPLOAD_ROOT,
            'logo',
            '%s.%s' % (sha1_hash, suffix)
            ]
    return '/'.join(args)


def qr_image_upload_to(instance, filename):
    sha1_hash = sha1(instance.url).hexdigest()
    suffix = filename.split('.')[-1]
    args = [
            settings.UPLOAD_ROOT,
            'qr',
            '%s.%s' % (sha1_hash, suffix)
            ]
    return '/'.join(args)


class PurchaseItemManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        queryset = super(PurchaseItemManager, self).get_queryset(*args, **kwargs)
        return queryset.filter(succeed=True)


class PurchaseItem(models.Model):
    """ 用户的购买项目 """
    code = models.CharField(max_length=40, verbose_name='编码', unique=True, blank=True)
    order = models.ForeignKey(Order, verbose_name=u'所属订单', blank=True, null=True)
    user = models.ForeignKey(CustomUser, verbose_name='用户', blank=True, null=True)
    version = models.ForeignKey(VersionCategory, verbose_name='版本类型')
    item_pid = models.PositiveIntegerField(u'国家ID', blank=True, null=True)
    item_pname = models.CharField(u'国家名称', max_length=32, blank=True, null=True)
    item_id = models.PositiveIntegerField(u'城市ID')
    item_name = models.CharField(u'城市名称', max_length=32, blank=True, null=True)
    logo = models.ImageField('Logo', upload_to=logo_upload_to, blank=True, null=True)
    slogan = models.CharField('Slogan', max_length=50, blank=True, null=True)

    succeed = models.BooleanField(u'是否成功', default=False)
    url = models.CharField(u'web app跳转地址', max_length=256)
    image = models.ImageField(u'web app跳转地址的二维码', upload_to=qr_image_upload_to, blank=True)

    viewed_count = models.PositiveIntegerField('浏览量', default=0)
    download_count = models.PositiveIntegerField('下载量', default=0)
    dt_expired = models.DateTimeField('失效于', blank=True, null=True)
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')
    default_objects = models.Manager()
    objects = PurchaseItemManager()

    class Meta:
        verbose_name = '购买项目'
        verbose_name_plural = '购买项目'
        get_latest_by = 'id'

    def __unicode__(self):
        return '%s: %s: %s' % (self.user or 'nologinuser', self.version, self.item_name)

    def set_item_parent(self):
        if not (self.item_pid and self.item_pname and self.item_name):
            self.item_id, self.item_name, self.item_pid, self.item_pname = self.version.check_city(self.item_id)

    def generate_code(self):
        m5 = hashlib.md5()
        m5.update("{}-{}-{}-{}-{}".format(
            self.user.username.encode('utf-8'),
            self.version.code,
            self.item_id,
            self.item_name.encode('utf-8'),
            self.dt_created.strftime('%Y-%m-%d %H:%M:%S')))
        return m5.hexdigest().upper()

    def save(self, *args, **kwargs):
        self.set_item_parent()
        if not self.user:
            self.user = CustomUser.objects.get(mobile=settings.DEFAULT_USER_MOBILE)
        return super(PurchaseItem, self).save(*args, **kwargs)


@receiver(post_save, sender="order.PurchaseItem")
def purchase_item_post_save(sender, instance, created, **kwargs):
    if created:
        instance.dt_expired = instance.dt_created + datetime.timedelta(days=instance.version.valid_days)
        instance.save()
    if not instance.code:
        instance.code = instance.generate_code()
    instance.url = "{0}{1}?code={2}".format(settings.API_BASE_URL,
                                            reverse('statistics_viewed', args=()), instance.code)
    if not instance.image:
        image_path = qr_image_upload_to(instance, 'view.png')
        instance.image.save(image_path, ContentFile(generate_qrcode(instance.url)))


class RefundOrder(models.Model):
    order = models.OneToOneField(Order, verbose_name="支付订单")
    refund_no = models.CharField(max_length=64, verbose_name="退款订单号")

    def __unicode__(self):
        return self.refund_no

    def save(self, *args, **kwargs):
        if not self.order.is_refunded:
            self.order.is_refunded = True
            self.order.save()
        return super(RefundOrder, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "退款订单"
        verbose_name_plural = verbose_name
