# -*- coding: utf-8 -*-
import os
import json
import urllib
import requests
import logging
from django.http import HttpResponse, StreamingHttpResponse
from django.http import StreamingHttpResponse
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes as permission_decorator
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from mjtt_django.settings import native_wechat_conf
from mjtt_django.errors import Success, Failed

from libs.wechat_pay import WeixinClient
from libs.utils import ResultResponse
from libs.utils import params_to_str
from libs.utils import archive_zip_package
from libs.excel import Excel

from common.models import VersionCategory
from .models import Order, PurchaseItem
from .models import ORDER_PREFIX_FOR_PAY, generate_global_id
from .models import STATUS_AS_COMMITTED

from people.permissions import CustomUserIsAuthenticated
from people.permissions import AdministratorIsAuthenticated
from statistics.models import Statistics

from .forms import NotifyForm
logger = logging.getLogger('lushu.order')


def decode_base64_file(data):

    def get_file_extension(file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension

    from django.core.files.base import ContentFile
    import base64
    import six
    import uuid

    # Check if this is a base64 string
    if isinstance(data, six.string_types):
        # Check if the base64 string is in the "data:" format
        if 'data:' in data and ';base64,' in data:
            # Break out the header from the base64 content
            header, data = data.split(';base64,')

        # Try to decode the file. Return validation error if it fails.
        try:
            decoded_file = base64.b64decode(data)
        except TypeError:
            TypeError('invalid_image')

        # Generate file name:
        file_name = str(uuid.uuid4())[:12] # 12 characters are more than enough.
        # Get the file name extension:
        file_extension = get_file_extension(file_name, decoded_file)

        complete_file_name = "%s.%s" % (file_name, file_extension, )

        return ContentFile(decoded_file, name=complete_file_name)


@api_view(['POST'])
@permission_decorator([CustomUserIsAuthenticated, ])
def pre_pay(request):
    """
    :param request:
    [
        {
            "version": "mjtt",
            "cities": "1",
            "slogans": ""
            "logo_1": "",
            "logo_2": "",
        }
    ]
    :return:
    """
    version_code = request.POST.get('version')
    city_list = request.POST.getlist('cities[]')

    if (not version_code) or (not city_list):
        raise ValidationError('参数无效')

    try:
        version = VersionCategory.objects.get(code=version_code)
    except ObjectDoesNotExist:
        raise ValidationError('版本无效')

    amount = 0
    body_list = []
    logo_list = []
    slogan_list = []
    for i, city_id in enumerate(city_list, 1):
        slogan = request.POST.get('slogan_{}'.format(i), '')
        if slogan and len(slogan) > 10:
            raise ValidationError('Slogan长度不得多于10位')
        slogan_list.append(slogan)

        logo = request.FILES.get('logo_{}'.format(i), None)
        if version.can_customize_logo:
            if logo and hasattr(logo, 'size') and logo.size > settings.LOGO_UPLOAD_MAX_SIZE:
                raise ValidationError('Logo图片不得大于100k')
            logo_list.append(logo)

        amount += version.price
        try:
            city_id, city_name, country_id, country_name = version.check_city(city_id)
            body_list.append(city_name)
        except Exception as e:
            raise ValidationError('城市不存在')

    out_trade_no = ORDER_PREFIX_FOR_PAY + generate_global_id()
    body_desc = u" ".join(body_list)
    success, info = WeixinClient(native_wechat_conf).request_qrcode(
        out_trade_no=out_trade_no, total_fee=amount * 100,
        body=body_desc.encode("utf8"), attach=params_to_str({}),
    )
    if not info:
        raise ValidationError('下单失败')

    order = Order.objects.create_consume_order(out_trade_no, request.user, version, amount,
                                               description=u'购买%s的订单' % body_desc,
                                               pay_url=info['qrcode'])
    logo_dict = dict(zip(range(len(logo_list)), logo_list))
    slogan_dict = dict(zip(range(len(slogan_list)), slogan_list))
    for i, city_id in enumerate(city_list):
        PurchaseItem.objects.create(order=order, user=request.user, version=version, item_id=city_id,
                                    logo=logo_dict.get(i), slogan=slogan_dict.get(i, ""))

    info["out_trade_no"] = out_trade_no
    info['qrcode_img_url'] = order.pay_qr_url
    return ResultResponse(Success, data=info)


@api_view(['POST'])
def notify_result(request):
    """
    async call_back
    :param request:
    :return:
    """
    is_succeed, data = WeixinClient(native_wechat_conf).verify_notify_data(request.body)
    form = NotifyForm(data)
    if form.is_valid():
        out_trade_no = data['out_trade_no']
        try:
            order = Order.objects.get(out_trade_no=out_trade_no)
            order.grant_consume(data["transaction_id"])
            order.save()
            PurchaseItem.default_objects.filter(order=order).update(succeed=True)
        except ObjectDoesNotExist:
            return HttpResponse(WeixinClient.gen_notify_fail_response('订单号无效'))

        return HttpResponse(WeixinClient.gen_notify_success_response())
    logger.info(form.errors)
    return HttpResponse(WeixinClient.gen_notify_fail_response('数据错误'))


@api_view(['POST'])
def get_qrcode_state(request):
    now_time = request.query_params.get('nowTime')
    out_trade_no = request.data.get('orderId')
    try:
        order = Order.objects.get(out_trade_no=out_trade_no)
    except ObjectDoesNotExist as e:
        logger.error(str(e))
        return ResultResponse(2, msg='参数无效')
    if order.status == STATUS_AS_COMMITTED:
        return ResultResponse(0, msg='扫码成功')
    elif (timezone.now() - order.dt_created).seconds > 60 * 10:
        return ResultResponse(4, msg='二维码过期')
    else:
        return ResultResponse(3, msg='等待扫码')


@api_view(['POST'])
@permission_decorator([CustomUserIsAuthenticated, ])
def download_qrcode(request):
    purchase_id = request.data.get('id')
    try:
        purchase = PurchaseItem.objects.get(id=purchase_id, user=request.user)
    except Exception as e:
        logger.error('download_qrcode err: {}, data: {}'.format(str(e), request.data.dict()))
        raise ValidationError('参数无效')

    data = requests.get(purchase.image.url).content

    # file_name, url = '{0}-{1}-{2}.jpg'.format(purchase.id, purchase.item_pname, purchase.item_name), purchase.image.url
    response = HttpResponse(data, content_type='application/octet-stream')
    # response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file_name)
    purchase.download_count += 1
    purchase.save()

    current = timezone.now()
    day = current.day
    year = current.year
    month = current.month

    stat, created = Statistics.objects.get_or_create(item=purchase, year=year, month=month, day=day)
    stat.download_count += 1
    stat.save()
    return response


@api_view(['POST'])
@permission_decorator([CustomUserIsAuthenticated, ])
def bulk_download_qrcode(request):
    try:
        id_list = request.data.get('ids').split(',')
    except Exception as e:
        logger.error('bulk_download_qrcode err: {}, data: {}'.format(str(e), request.data.dict()))
        raise ValidationError('参数无效')

    save_path = os.path.join('./', '试听二维码')
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    image_list = []
    queryset = PurchaseItem.objects.filter(id__in=id_list, user=request.user)
    for q in queryset:
        if q.image:
            image_list.append(['{0}-{1}-{2}.jpg'.format(q.id, q.item_pname, q.item_name), q.image.url])
            q.download_count += 1
            q.save()

            current = timezone.now()
            day = current.day
            year = current.year
            month = current.month

            stat, created = Statistics.objects.get_or_create(item=q, year=year, month=month, day=day)
            stat.download_count += 1
            stat.save()

    for filename, url in image_list:
        url = urllib.unquote(url)
        urllib.urlretrieve(url, os.path.join(save_path, '%s' % filename))
    zip_path = archive_zip_package(save_path)

    def file_iterator(fn, chunk_size=512):
        with open(fn) as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break

    response = StreamingHttpResponse(file_iterator(zip_path))
    response['Content-Type'] = 'application/octet-stream'
    file_name = zip_path.rsplit('/', 1)[-1] or '试听二维码.zip'
    # response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file_name)

    return response


@api_view(['POST'])
@permission_decorator([CustomUserIsAuthenticated, ])
def bulk_delete_purchase(request):
    try:
        id_list = request.data.get('ids').split(',')
    except Exception as e:
        logger.error('bulk_delete_purchase err: {}, data: {}'.format(str(e), request.data.dict()))
        raise ValidationError('参数无效')

    PurchaseItem.objects.filter(id__in=id_list, user=request.user).delete()
    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_decorator([AdministratorIsAuthenticated, ])
def admin_bulk_delete_purchase(request):
    try:
        id_list = request.data.get('ids').split(',')
    except Exception as e:
        logger.error('admin_bulk_delete_purchase err: {}, data: {}'.format(str(e), request.data.dict()))
        raise ValidationError('参数无效')

    PurchaseItem.objects.filter(id__in=id_list).delete()
    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_decorator([AdministratorIsAuthenticated, ])
def admin_download_qrcode(request):
    purchase_id = request.data.get('id')
    try:
        purchase = PurchaseItem.objects.get(id=purchase_id)
    except Exception as e:
        logger.error('admin_download_qrcode err: {}, data: {}'.format(str(e), request.data.dict()))
        raise ValidationError('参数无效')

    data = requests.get(purchase.image.url).content

    file_name, url = '{0}-{1}-{2}.jpg'.format(purchase.item_pname,
                                              purchase.item_name,
                                              purchase.dt_expired.strftime('%Y%m%d')), purchase.image.url
    response = HttpResponse(data, content_type='application/octet-stream')
    # response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file_name)

    purchase.download_count += 1
    purchase.save()

    current = timezone.now()
    day = current.day
    year = current.year
    month = current.month

    stat, created = Statistics.objects.get_or_create(item=purchase, year=year, month=month, day=day)
    stat.download_count += 1
    stat.save()
    return response


@api_view(['POST'])
@permission_decorator([AdministratorIsAuthenticated, ])
def admin_export_order(request):
    try:
        id_list = request.data.get('ids').split(',')
    except Exception as e:
        logger.error('admin_export_order err: {}, data: {}'.format(str(e), request.data.dict()))
        raise ValidationError('参数无效')
    title_dict = [
        {'name': '订单号', "field": "out_trade_no"},
        {'name': '支付订单号', 'field': 'transaction_id'},
        {'name': '用户ID', 'field': 'user_id'},
        {'name': '姓名', 'field': 'username'},
        {'name': '版本', 'field': 'version'},
        {'name': '城市数量', 'field': 'city_count'},
        {'name': '金额', 'field': 'amount'},
    ]
    data_list = []
    queryset = Order.objects.filter(out_trade_no__in=id_list)
    for i in queryset:
        data = {
            'out_trade_no': i.out_trade_no,
            'transaction_id': i.transaction_id,
            'user_id': i.user.id,
            'username': i.user.username,
            'version': i.version.name,
            'city_count': PurchaseItem.objects.filter(order=i).count(),
            'amount': i.amount_display
        }
        data_list.append(data)
    content = Excel().generate(title_dict, data_list)

    response = HttpResponse(content, content_type='application/octet-stream')
    return response
