#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.core.mail import send_mail as _send_mail
from django.conf import settings
from celery import shared_task


@shared_task
def send_mail(subject, message, to_list):
    '''
    Send email via django's mail function.

    '''
    sender = settings.EMAIL_HOST_USER
    if type(to_list) is not list:
        to_list = [to_list]
    return _send_mail(subject, message, sender, to_list)
