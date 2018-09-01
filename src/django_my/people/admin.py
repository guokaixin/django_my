# -*- coding: utf8 -*-

from django.contrib import admin
from django import forms
from django.http import HttpResponseRedirect
from django.utils.html import escape
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from jet.admin import CompactInline
from common.utils.admin import BaseModelAdmin
from .models import Business
from .models import CustomUser
from .models import Administrator
from .models import UserBusiness


@admin.register(Business)
class BusinessModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    ordering = ('id', )


class UserBusinessInline(CompactInline):
    model = UserBusiness
    fields = ('business', 'dt_created')
    readonly_fields = ('dt_created', )
    extra = 0


@admin.register(CustomUser)
class CustomUserModelAdmin(BaseModelAdmin):
    list_display = ('username', 'code', 'mobile', 'company', 'is_available', 'dt_updated', 'date_joined')
    list_filter = ('type', 'role', 'authority', 'is_available')
    search_fields = ('id', 'username', 'mobile')
    fields = ('code', 'username', 'avatar', 'mobile', 'company', 'is_available', 'is_superuser')
    readonly_fields = ('code', )
    inlines = [UserBusinessInline]

    def get_queryset(self, request):
        return super(CustomUserModelAdmin, self).get_queryset(request).filter(is_superuser=False)


class UserPasswordChangeFormAdmin(forms.Form):
    password1 = forms.CharField(
        label=u"请输入新登录密码。",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label=u"请再次输入新登录密码。",
        widget=forms.PasswordInput
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(UserPasswordChangeFormAdmin, self).__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(u"两次输入的密码不相同！")
        return password2

    def save(self, commit=True):
        """
        Saves the new password.
        """
        self.user.set_password(self.cleaned_data["password1"])
        if commit:
            self.user.save()
        return self.user


@admin.register(Administrator)
class AdministratorModelAdmin(BaseModelAdmin):
    list_display = ('username', 'code', 'date_joined')
    search_fields = ('id', 'username')
    fields = ('code', 'username', 'password', 'is_available', 'is_superuser')
    readonly_fields = ('code', 'password')
    change_password_form = UserPasswordChangeFormAdmin

    def __call__(self, request, url):
        if url is None:
            return self.changelist_view(request)
        if url.endswith('password'):
            return self.user_change_password(request, url.split('/')[0])

        return super(AdministratorModelAdmin, self).__call__(request, url)

    def get_urls(self):
        from django.conf.urls import url
        return [
                   url(r'^(\d+)/change/password/$', self.admin_site.admin_view(self.user_change_password)),
               ] + super(AdministratorModelAdmin, self).get_urls()

    def user_change_password(self, request, obj_id):
        if not request.user.has_perm('people.change_administrator'):
            raise PermissionDenied
        user = get_object_or_404(self.model, pk=obj_id)
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                self.message_user(request, u'成功修改用户登录密码！')
                return HttpResponseRedirect('..')
        else:
            form = self.change_password_form(user)
        return render(request, 'admin/people/user/change_password.html', {
            'title': u'修改用户密码： %s (%s)' % (escape(user.mobile), escape(user.username)),
            'form': form,
            'is_popup': ('_popup' in request.GET) or ('_popup' in request.POST),
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True})
