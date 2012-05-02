from django.conf.urls.defaults import *

urlpatterns = patterns('etruekko.truekko.views',
    url(r'^profile/edit$', 'edit_profile', name='edit_profile'),
    url(r'^profile/edit/(\w+)$', 'edit_profile_admin', name='edit_profile_admin'),
    url(r'^profile/(\w+)$', 'view_profile', name='view_profile'),
    url(r'^people$', 'people', name='people'),
    url(r'^people/all$', 'people_all', name='people_all'),
    url(r'^rate/(\d+)$', 'rate_user', name='rate_user'),
    # follow
    url(r'^follow/(\d+)$', 'follow', name='follow'),
    url(r'^unfollow/(\d+)$', 'unfollow', name='unfollow'),
    # channels
    url(r'^channel/view/(\d+)$', 'channel_view', name='channel_view'),
    # groups
    url(r'^groups$', 'groups', name='groups'),
    url(r'^group/(\d+)$', 'view_group', name='view_group'),
    url(r'^group/edit/(\d+)$', 'edit_group', name='edit_group'),
    url(r'^group/edit/members/(\d+)$', 'edit_group_members', name='edit_group_members'),
    url(r'^group/join/(\d+)$', 'join_group', name='join_group'),
    url(r'^group/leave/(\d+)$', 'leave_group', name='leave_group'),
    url(r'^group/register/(\d+)$', 'register_group', name='register_group'),
    url(r'^group/admin/register/(\d+)$', 'register_group_admin', name='register_group_admin'),
    url(r'^group/register/confirm/(\d+)$', 'register_confirm', name='register_confirm'),
    url(r'^group/denounce/(\d+)$', 'group_denounce', name='group_denounce'),
    url(r'^group/denounce/(\d+)/(\w+)$', 'group_denounce_user', name='group_denounce_user'),
    url(r'^group/denounce/view/(\d+)$', 'group_denounce_view', name='group_denounce_view'),
    # register
    url(r'^register$', 'register_wizard', name='register_wizard'),
    # transfer
    url(r'^transfer/direct/(\w+)$', 'transfer_direct', name='transfer_direct'),
    url(r'^transfer/list$', 'transfer_list', name='transfer_list'),
    # swap
    url(r'^swap/list$', 'swap_list', name='swap_list'),
    url(r'^swap/view/(\d+)$', 'swap_view', name='swap_view'),
    url(r'^swap/(\w+)$', 'swap_creation', name='swap_creation'),
    url(r'^commitment/done/(\d+)$', 'commitment_done', name='commitment_done'),
    # item
    url(r'^item/add$', 'item_add', name='item_add'),
    url(r'^item/edit/(?P<object_id>\d+)$', 'item_add', name='item_edit'),
    url(r'^item/remove/(\d+)$', 'item_remove', name='item_remove'),
    url(r'^item/view/(\d+)$', 'item_view', name='item_view'),
    url(r'^item/list/(item|serv)/(\w+)?$', 'item_list', name='item_list'),
    # messages
    url(r'^messages/post/(\d+)$', 'message_post', name='message_post'),
    url(r'^messages/remove/(\d+)$', 'message_remove', name='message_remove'),
    # search
    url(r'^search/advanced$', 'search_advanced', name='search_advanced'),
    url(r'^search/', include('haystack.urls')),
    # etruekko
    url(r'^etruekko$', 'etruekko', name='etruekko'),

    url(r'^$', 'index', name='index'),
)
