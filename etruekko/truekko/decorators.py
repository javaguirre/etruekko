from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from truekko.models import Membership
from truekko.models import User
from truekko.models import Group


def has_perm(view, test_function, message="", next="/"):

    def new_func(request, *args, **kwargs):
        if test_function(request, *args, **kwargs):
            return view(request, *args, **kwargs)
        else:
            if not message:
                message = _("Sorry but you don't have permission")

            request.user.message_set.create(message=message)
            return redirect('/')

    return new_func


def is_group_admin(view):

    def new_func(request, groupname):
        if is_group_editable(request.user.username, groupname):
            return view(request, groupname)
        else:
            message = _("Only group admin can edit this group")
            request.user.message_set.create(message=message)
            return redirect('view_group', groupname)

    return new_func


def is_group_editable(username, groupname):
    try:
        user = User.objects.get(username=username)
        m = user.membership_set.get(group__name=groupname)
    except:
        return False

    return m.role == "ADM"
