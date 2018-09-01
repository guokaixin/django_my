# -*- coding: utf-8 -*-
from django.db.models import Q
from django.contrib import admin, messages
from common.utils.admin import BaseModelAdmin
from common.utils.image_tag import image_tag
from libs.wechat_pay import WeixinClient

from .models import PurchaseItem
from .models import Order, STATUS_AS_COMMITTED
from .models import RefundOrder
from .models import generate_global_id

native_wechat_conf = {
    "appid": "wxdc59e871888819d2",
    "mch_id": "1424177502",
    "key": "XvqgNGylRirU1kcw26MehPETm8QjHxJn",
    "notify_url": "http://testlushu.gowithtommy.com/api/pay/notify/",
    "sign_cert_path": "/usr/local/mjango/certpublic/apiclient_cert.pem",
    "sign_key_path": "/usr/local/mjango/certpublic/apiclient_key.pem",
}

@admin.register(Order)
class OrderModelAdmin(BaseModelAdmin):
    list_display = ('out_trade_no', 'transaction_id', 'purchase_record', 'user', 'amount_display',
                    'status', 'pay_url', 'is_refunded', 'dt_granted', 'dt_created')
    list_filter = ('status', 'is_refunded')
    search_fields = ('user__username', 'user__id', 'out_trade_no', 'transaction_id')
    readonly_fields = ('pay_url', 'pay_image', 'out_trade_no', 'comment')
    fields = ('out_trade_no', 'transaction_id', 'comment', 'status', 'pay_url', 'pay_image')
    actions = ["refund_action", ]
    date_hierarchy = 'dt_created'

    def refund_action(self, request, queryset):
        queryset = queryset.exclude(Q(transaction_id='') | Q(transaction_id__isnull=True))\
            .filter(is_refunded=False, status=STATUS_AS_COMMITTED)
        if queryset.count() <= 10:
            i = 0
            for order in queryset:
                # out_refund_no
                out_refund_no = "R" + generate_global_id()

                # package refund info
                refund_info = {
                    "transaction_id": order.transaction_id,
                    "out_trade_no": order.out_trade_no,
                    "out_refund_no": out_refund_no,
                    "total_fee": order.amount_cents,
                    "refund_fee": order.amount_cents,
                }

                # make refund
                res = WeixinClient(native_wechat_conf).create_refund(refund_info)
                if res:
                    RefundOrder.objects.create(refund_no=out_refund_no, order=order)
                    i += 1
                else:
                    messages.error(request, "成功退款{}笔订单，退款失败{}笔订单".format(i, 1))
                    return
            messages.success(request, "成功退款{}笔订单".format(i))
        else:
            messages.warning(request, "最多可选择10个完成支付的订单")
    refund_action.short_description = "退款"

    def purchase_record(self, instance):
        return '<a href="/admin/order/purchaseitem/?order_id={}">{}</a>'.format(instance.id, PurchaseItem.default_objects.filter(order=instance).count())
    purchase_record.allow_tags = True
    purchase_record.short_description = '购买城市数量'


@admin.register(PurchaseItem)
class PurchaseItemModelAdmin(BaseModelAdmin):
    list_display = ('id', 'user', 'code', 'version', 'item_pname', 'item_name', 'logo_', 'slogan',
                    'viewed_count', 'download_count', 'url', 'image', 'succeed', 'dt_created', 'dt_expired')
    list_filter = ('version', 'succeed')
    fields = ('code', 'user', 'version', 'item_pname', 'item_name', 'logo', 'slogan',
              'url', 'image', 'succeed', 'viewed_count', 'dt_created', 'dt_expired')
    readonly_fields = ('dt_expired', 'viewed_count', 'dt_created', 'code', 'item_pname', 'version')
    search_fields = ('user__username', 'user__id', 'item_pname', 'item_name')
    date_hierarchy = 'dt_created'

    def logo_(self, instance):
        if instance.logo:
            return image_tag.format(image_url=instance.logo.url, height='20px')

    logo_.allow_tags = True
    logo_.short_description = 'Logo'

    # def get_queryset(self, request):
    #     queryset = super(PurchaseItemModelAdmin, self).get_queryset(request)
    #     return queryset.filter(succeed=True)


@admin.register(RefundOrder)
class RefundOrderAdmin(admin.ModelAdmin):
    list_display = ("refund_no", "transaction_id", "username", "total_fee")

    def get_actions(self, request):
        return []

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def transaction_id(self, obj):
        return obj.order.transaction_id

    def username(self, obj):
        return obj.order.user.username

    def total_fee(self, obj):
        return obj.order.amount_cents

