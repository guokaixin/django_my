from django.conf.urls import url
from django.conf.urls import include

from rest_framework import routers

from .views import pre_pay
from .views import notify_result
from .views import get_qrcode_state
from .views import download_qrcode
from .views import bulk_download_qrcode
from .views import bulk_delete_purchase
from .views import admin_bulk_delete_purchase
from .views import admin_download_qrcode
from .views import admin_export_order

from .viewsets import OrderViewSet
from .viewsets import AdminOrderViewSet
from .viewsets import FreePurchaseItemViewSet
from .viewsets import PurchaseItemViewSet
from .viewsets import AdminPurchaseItemViewSet


router = routers.DefaultRouter()
# router.register('purchase', PurchaseItemViewSet, base_name='PurchaseItemViewSet')


front_urls = [
    url(r'^user/(?P<user_pk>\d+)/order/', OrderViewSet.as_view({'get': 'list'}), name='ListOrderViewSet'),

    url(r'^user/(?P<user_pk>\d+)/purchase/$', PurchaseItemViewSet.as_view({'get': 'list'}), name='user_purchase_list'),
    url(r'^version/free/purchase/$', FreePurchaseItemViewSet.as_view({'post': 'create'}), name='FreePurchaseItemViewSet'),

    url(r'^prepay/$', pre_pay, name='Prepay'),
    url(r'^notify/$', notify_result, name='NotifyResult'),

    url(r'^getQrcodeState/$', get_qrcode_state, name='get_qrcode_state'),
    url(r'^downloadQrcode/$', download_qrcode, name='download_qrcode'),
    url(r'^bulkDownloadQrcode/$', bulk_download_qrcode, name='bulk_download_qrcode'),
    url(r'^bulkDeletePurchase/$', bulk_delete_purchase, name='bulk_delete_purchase'),
]

backend_urls = [
    url(r'^order/', AdminOrderViewSet.as_view({'get': 'list'}), name='ListOrderViewSet'),
    url(r'^purchase/$', AdminPurchaseItemViewSet.as_view({'get': 'list'}),
        name='ListPurchaseItemViewSet'),
    url(r'^bulkDeletePurchase/$', admin_bulk_delete_purchase, name='administrator_bulk_delete_purchase'),
    url(r'^downloadQrcode/$', admin_download_qrcode, name='admin_download_qrcode'),
    url(r'^exportOrder/$', admin_export_order, name='admin_export_order'),

]

urlpatterns = [
    url(r'pay/', include(router.urls, )),
    url(r'pay/', include(front_urls)),
    url(r'payment/', include(backend_urls)),

]
