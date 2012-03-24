from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('etruekko.truekko.views',
    url(r'^profile/edit$', 'edit_profile', name='edit_profile'),
    url(r'^profile/(\w+)$', 'view_profile', name='view_profile'),
    url(r'^people$', 'people', name='people'),
    # groups
    url(r'^groups$', 'groups', name='groups'),
    url(r'^group/(\w+)$', 'view_group', name='view_group'),
    url(r'^group/edit/(\w+)$', 'edit_group', name='edit_group'),
    url(r'^group/edit/members/(\w+)$', 'edit_group_members', name='edit_group_members'),
    url(r'^group/join/(\w+)$', 'join_group', name='join_group'),
    url(r'^group/leave/(\w+)$', 'leave_group', name='leave_group'),
    url(r'^group/register/(\w+)$', 'register_group', name='register_group'),
    url(r'^group/admin/register/(\w+)$', 'register_group_admin', name='register_group_admin'),
    url(r'^group/register/confirm/(\w+)$', 'register_confirm', name='register_confirm'),
    # transfer
    url(r'^transfer/direct/(\w+)$', 'transfer_direct', name='transfer_direct'),
    url(r'^transfer/list$', 'transfer_list', name='transfer_list'),
    # swap
    url(r'^swap/list$', 'swap_list', name='swap_list'),
    url(r'^swap/view/(\d+)$', 'swap_view', name='swap_view'),
    url(r'^swap/(\w+)$', 'swap_creation', name='swap_creation'),
    # item
    url(r'^item/add$', 'item_add', name='item_add'),
    url(r'^item/view/(\d+)$', 'item_view', name='item_view'),
    url(r'^item/list/(item|serv)/(\w+)?$', 'item_list', name='item_list'),

    url(r'^$', 'index', name='index'),
)
