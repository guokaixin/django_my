#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.db.models import Manager


class ExcludeDeleteManager(Manager):
    def get_queryset(self):
        queryset = super(ExcludeDeleteManager, self).get_queryset()
        fields = (f.name for f in self.model._meta.fields)
        if 'is_deleted' in fields:
            queryset = queryset.filter(is_deleted=False)
        return queryset


class PublishedManager(ExcludeDeleteManager):
    def get_queryset(self):
        queryset = super(PublishedManager, self).get_queryset()
        queryset = queryset.filter(is_published=True)
        return queryset
