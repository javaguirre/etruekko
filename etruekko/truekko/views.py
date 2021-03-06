# -*- coding: utf-8 -*-
import uuid
from unidecode import unidecode
import datetime
import os
from PIL import Image

from django.utils.datastructures import SortedDict

from django.http import Http404
from django.contrib import messages
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils import translation
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import View, TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from decorators import is_group_admin, is_group_editable, is_member
from django.shortcuts import render_to_response
from django.db.models import Q
from django.conf import settings
from django.utils import simplejson as json
from django.http import HttpResponse

from etruekko.truekko.forms import UserProfileForm
from etruekko.truekko.forms import GroupForm
from etruekko.truekko.forms import RegisterForm
from etruekko.truekko.forms import TransferDirectForm
from etruekko.truekko.forms import ItemAddForm
from etruekko.truekko.forms import ContactForm
from etruekko.truekko.forms import CommitmentForm
from etruekko.truekko.forms import PostalForm

from etruekko.truekko.models import UserProfile
from etruekko.truekko.models import User
from etruekko.truekko.models import Group
from etruekko.truekko.models import Channel
from etruekko.truekko.models import Membership
from etruekko.truekko.models import Denounce
from etruekko.truekko.models import Transfer
from etruekko.truekko.models import Item, ItemImage
from etruekko.truekko.models import Tag
from etruekko.truekko.models import ItemTagged
from etruekko.truekko.models import Swap, SwapItems, SwapComment
from etruekko.truekko.models import Wall, WallMessage
from etruekko.truekko.models import Follow
from etruekko.truekko.models import Commitment
from etruekko.truekko.models import PostalAddress

from etruekko.truekko.utils import generate_menu
from etruekko.utils import paginate, template_email


class Index(TemplateView):
    template_name = 'truekko/index.html'

    def get_context_data(self, **kwargs):
        context = super(Index, self).get_context_data(**kwargs)
        context['klass'] = 'home'
        context['menu'] = generate_menu("home")

        if self.request.user.is_authenticated():
            u = self.request.user
            wall, created = Wall.objects.get_or_create(user=u, name="%s wall" % u.username)
            messages = self.messages_for_user()
            context['wallmessages'] = paginate(self.request, messages, 20)
            context['wall'] = wall
            context['groups'] = u.get_profile().groups()
            items = Item.objects.filter(user=u)
            context['offers'] = items.filter(offer_or_demand="OFF")
            context['demands'] = items.filter(offer_or_demand="DEM")
            context['priv'] = self.request.GET.get('priv', '')

            context['admin'] = self.request.user.get_profile().is_admin()
            if context['admin']:
                groups = self.request.user.get_profile().admin_groups()
                context['admin_denounces'] = Denounce.objects.filter(status__in=["PEN", "CON"]).filter(group__in=groups)

            tq = Q(user_from=u) | Q(user_to=u)
            context['denounces'] = Denounce.objects.filter(status__in=["PEN", "CON"]).filter(tq)

            tq = Q(user_from=u) | Q(user_to=u)
            tq2 = Q(status__in=['US1', 'US2'])
            context['swaps'] = Swap.objects.filter(tq).filter(tq2)
            context['my_commitments'] = u.my_commitments.filter(status='WAI')
            context['commitments_to_me'] = u.commitments_to_me.filter(status='WAI')
        else:
            context['last_services'] = Item.objects.filter(type="SR")[0:3]
            context['last_items'] = Item.objects.filter(type="IT")[0:3]
            context['last_groups'] = Group.objects.all().order_by("-id")[0:3]

        return context

    def get(self, request):
        self.request = request
        return super(Index, self).get(request)

    def messages_for_user(self):
        priv = self.request.GET.get('priv', '')

        u = self.request.user
        if u.is_anonymous():
            return WallMessage.objects.filter(private=False)

        groups = u.get_profile().groups()
        friends = u.get_profile().followings()
        wall, created = Wall.objects.get_or_create(user=u, name="%s wall" % u.username)

        if priv:
            query = Q(wall=wall, private=True)
        else:
            # user wall messages
            query = Q(wall=wall)
            # and user sended messages
            query = query | Q(user=u)
            # and user groups messages
            query = query | Q(wall__group__in=groups)
            # and friends messages
            query = query | Q(user__in=friends, private=False)
            # and user group notification wall
            query = query | Q(wall=Wall.notification(), user__membership__group__in=groups)
            # and channels msgs
            query = query | Q(wall__channels__in=u.get_profile().channels())
            # and etruekko
            if u.get_profile().is_admin():
                query = query | Q(wall=Wall.etruekko())
            # replies will be shown in template
            query = query & Q(parent=None)

        return WallMessage.objects.filter(query).distinct()


############
#          #
#  PEOPLE  #
#          #
############

class ViewProfile(TemplateView):
    template_name = 'truekko/view_profile.html'

    def get_context_data(self, **kwargs):
        context = super(ViewProfile, self).get_context_data(**kwargs)
        u = get_object_or_404(User, username=self.username, is_active=True)
        wall, created = Wall.objects.get_or_create(user=u, name="%s wall" % u.username)
        messages = wall.messages_for_user(self.request.user)

        context['klass'] = 'people'
        context['menu'] = generate_menu()
        context['viewing'] = u
        context['admin'] = self.request.user.get_profile().is_admin_user(u)
        context['wall'] = wall
        context['wallmessages'] = paginate(self.request, messages, 20)
        d = Denounce.objects.filter(user_from=self.request.user, user_to=u, status__in=['PEN', 'CON'])
        if d.count():
            context['denounced'] = d[0]
        else:
            context['denounced'] = False

        items = Item.objects.filter(user=u)
        context['offers'] = items.filter(offer_or_demand="OFF")
        context['demands'] = items.filter(offer_or_demand="DEM")

        context['groups'] = u.get_profile().groups()

        return context

    def get(self, request, username):
        self.request = request
        self.username = username
        return super(ViewProfile, self).get(request)


class EditProfile(TemplateView):
    template_name = 'truekko/edit_profile.html'

    def get_context_data(self, **kwargs):
        context = super(EditProfile, self).get_context_data(**kwargs)
        context['form'] = UserProfileForm(instance=self.request.user.get_profile())
        context['klass'] = 'people'
        context['viewing'] = self.request.user
        context['menu'] = generate_menu()

        p = PostalAddress.objects.filter(user=self.request.user)
        if p.count():
            f = PostalForm(instance=p[0])
        else:
            f = PostalForm()
        context['postal_form'] = f
        context['pwform'] = PasswordChangeForm(self.request.user)
        context['default'] = self.request.GET.get('setting', 'general')
        return context

    def get(self, request):
        self.request = request
        return super(EditProfile, self).get(request)

    def post(self, request):
        data = request.POST

        files_req = request.FILES
        if (files_req.get('photo', '')):
            files_req['photo'].name = request.user.username

        form = UserProfileForm(request.POST, files_req, instance=request.user.get_profile())
        if not form.is_valid():
            menu = generate_menu()
            context = RequestContext(request, {'viewing': request.user, 'form': form, 'menu': menu})
            context['klass'] = 'people'
            return render_to_response(EditProfile.template_name, context)

        form.save()

        nxt = redirect('view_profile', request.user.username)
        return nxt


class EditPostal(TemplateView):
    template_name = 'truekko/edit_profile.html'

    def get_context_data(self, **kwargs):
        context = super(EditPostal, self).get_context_data(**kwargs)
        context['klass'] = 'people'
        context['viewing'] = self.user
        context['menu'] = generate_menu()

        p = PostalAddress.objects.filter(user=self.user)
        if p.count():
            f = PostalForm(instance=p[0])
        else:
            f = PostalForm()
        context['postal_form'] = f
        context['default'] = self.request.GET.get('setting', 'postal')
        return context

    def get(self, request, uid=None):
        if not uid:
            self.user = request.user
        else:
            self.user = get_object_or_404(User, pk=uid)
        if self.user != request.user and\
           not request.user.get_profile().is_admin_user(self.user):
            raise Http404

        return super(EditPostal, self).get(request)

    def post(self, request, uid=None):
        if not uid:
            u = request.user
        else:
            u = get_object_or_404(User, pk=uid)

        if u != request.user and\
           not request.user.get_profile().is_admin_user(u):
            raise Http404

        p = PostalAddress.objects.filter(user=u)

        if p.count():
            f = PostalForm(request.POST, instance=p[0])
        else:
            f = PostalForm(request.POST)

        if not f.is_valid():
            menu = generate_menu()
            context = RequestContext(request, {'viewing': u, 'postal_form': f, 'menu': menu})
            context['default'] = self.request.GET.get('setting', 'postal')
            context['klass'] = 'people'
            return render_to_response(EditPostal.template_name, context)

        p = f.save(commit=False)
        p.user = u

        p.save()

        return redirect("view_profile", u)


class EditProfileAdmin(TemplateView):
    template_name = 'truekko/edit_profile.html'

    def get_context_data(self, **kwargs):
        context = super(EditProfileAdmin, self).get_context_data(**kwargs)
        context['form'] = UserProfileForm(instance=self.user.get_profile())
        context['klass'] = 'people'
        context['viewing'] = self.user
        context['menu'] = generate_menu()

        context['default'] = self.request.GET.get('setting', 'general')
        return context

    def get(self, request, username):
        self.request = request
        self.user = get_object_or_404(User, username=username)
        if not self.request.user.get_profile().is_admin_user(self.user):
            raise Http404
        return super(EditProfileAdmin, self).get(request)

    def post(self, request, username):
        self.user = get_object_or_404(User, username=username)
        if not self.request.user.get_profile().is_admin_user(self.user):
            raise Http404

        data = request.POST

        files_req = request.FILES
        if (files_req.get('photo', '')):
            files_req['photo'].name = self.user.username

        form = UserProfileForm(request.POST, files_req, instance=self.user.get_profile())
        if not form.is_valid():
            menu = generate_menu()
            context = RequestContext(request, {'viewing': self.user, 'form': form, 'menu': menu})
            context['klass'] = 'people'
            return render_to_response(EditProfileAdmin.template_name, context)

        form.save()

        nxt = redirect('view_profile', username)
        return nxt


class People(TemplateView):
    template_name = 'truekko/people.html'

    def get_filters(self):
        filters = SortedDict()
        filters['all'] = {'text': _("All"), 'query': Q()}
        u = self.request.user

        if not u.is_authenticated():
            return filters

        filters['friends'] = {'text': _("Only Friends"), 'query': Q(followers__follower=self.request.user)}

        for g in u.get_profile().groups():
            filters['community%d' % g.id] = {'text': g.name, 'query': Q(membership__group=g)}

        return filters


    def get(self, request, filter_name=None):
        self.request = request
        self.filter_name = filter_name or "all"
        self.filter = self.get_filters().get(self.filter_name, None)
        if not self.filter:
            self.filter = self.get_filters()['all']
        return super(People, self).get(request)

    def get_context_data(self, **kwargs):
        context = super(People, self).get_context_data(**kwargs)
        context['klass'] = 'people'
        context['menu'] = generate_menu("people")
        context['filters'] = self.get_filters()
        context['sfilter'] = self.filter_name

        query = User.objects.filter(self.filter['query'])
        query = query.filter(is_active=True)

        q = self.request.GET.get('search', '')
        if q:
            k = Q(username__icontains=q) |\
                Q(email__icontains=q) |\
                Q(userprofile__description__icontains=q) |\
                Q(userprofile__name__icontains=q) |\
                Q(userprofile__location__icontains=q)

            query = query.filter(k)
        context['users'] = paginate(self.request, query, 10)
        return context


class RateUser(View):
    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        try:
            rating = int(request.POST['rating'])
        except:
            messages.info(request, _(u"Error receiving the rating"))
            return redirect('view_profile', user.username)

        if user == request.user:
            messages.info(request, _(u"You don't have permissions to rate this user"))
            return redirect('view_profile', user.username)

        if 1 > rating > 5:
            messages.info(request, _(u"Rating must be between 1 and 5"))
            return redirect('view_profile', user.username)

        user.get_profile().rating.add(score=rating,
                                      user=request.user,
                                      ip_address=request.META['REMOTE_ADDR'])
        messages.info(request, _(u"User rated successfully"))

        return redirect('view_profile', user.username)


############
#          #
# CHANNELS #
#          #
############

class ChannelView(TemplateView):
    template_name = 'truekko/channel_view.html'

    def get_context_data(self, **kwargs):
        context = super(ChannelView, self).get_context_data(**kwargs)
        context['klass'] = 'group'
        context['menu'] = generate_menu("group")
        context['channel'] = self.channel
        context['wallmessages'] = paginate(self.request, WallMessage.objects.filter(Q(wall=self.channel.wall) & Q(parent=None)), 20)

        return context

    def get(self, request, channelid):
        self.request = request
        self.channel = get_object_or_404(Channel, pk=channelid)
        # checking perms
        if not self.channel.can_view(request.user):
            raise Http404

        return super(ChannelView, self).get(request)


class Etruekko(TemplateView):
    template_name = 'truekko/etruekko.html'

    def get_context_data(self, **kwargs):
        context = super(Etruekko, self).get_context_data(**kwargs)
        context['klass'] = 'home'
        context['menu'] = generate_menu("home")
        context['wall'] = self.wall
        context['wallmessages'] = paginate(self.request, WallMessage.objects.filter(Q(wall=self.wall) & Q(parent=None)), 20)

        return context

    def get(self, request):
        self.request = request
        self.wall = Wall.etruekko()
        # checking perms
        if not self.can_view(request.user):
            raise Http404

        return super(Etruekko, self).get(request)

    def can_view(self, user):
        if user.is_staff and user.is_superuser:
            return True

        if Membership.objects.filter(role="ADM", user=user).count():
                return True


############
#          #
#  GROUPS  #
#          #
############


class Groups(TemplateView):
    template_name = 'truekko/groups.html'

    def get_filters(self):
        filters = SortedDict()
        filters['all'] = {'text': _("All"), 'query': Q()}
        u = self.request.user

        if not u.is_authenticated():
            return filters

        filters['mine'] = {'text': _("My communities"), 'query': Q(membership__user=u,
                                                                   membership__role__in=["MEM", "ADM"])}

        return filters

    def get_context_data(self, **kwargs):
        context = super(Groups, self).get_context_data(**kwargs)
        context['klass'] = 'group'
        context['menu'] = generate_menu("group")
        context['filters'] = self.get_filters()
        context['sfilter'] = self.filter_name

        query = Group.objects.filter(self.filter['query'])

        q = self.request.GET.get('search', '')
        if q:
            k = Q(email__icontains=q) |\
                Q(description__icontains=q) |\
                Q(name__icontains=q) |\
                Q(location__icontains=q)

            query = query.filter(k)
        context['groups'] = paginate(self.request, query, 10)
        return context

    def get(self, request, filter_name=None):
        self.request = request
        self.filter_name = filter_name or "all"
        self.filter = self.get_filters().get(self.filter_name, None)
        if not self.filter:
            self.filter = self.get_filters()['all']
        return super(Groups, self).get(request)


class ViewGroup(TemplateView):
    template_name = 'truekko/view_group.html'

    def get_context_data(self, **kwargs):
        context = super(ViewGroup, self).get_context_data(**kwargs)
        context['klass'] = 'group'
        context['menu'] = generate_menu('group')
        context['viewing'] = get_object_or_404(Group, pk=self.groupid)

        context['editable'] = is_group_editable(self.request.user.username, self.groupid)

        try:
            ms = Membership.objects.get(user=self.request.user, group=self.groupid)
            context['membership'] = ms
        except:
            context['membership'] = None

        g = get_object_or_404(Group, pk=self.groupid)
        context['requests'] = g.membership_set.filter(role="REQ").count()
        admins = [i for i in g.membership_set.filter(role="ADM").order_by("-id")]
        context['memberships'] = admins + [i for i in g.membership_set.exclude(role__in=["REQ", "BAN", "ADM"]).order_by("-id")[0:10]]

        context['denounces'] = Denounce.objects.filter(group=g, status__in=["PEN", "CON"])

        wall, created = Wall.objects.get_or_create(group=g, name="%s wall" % g.name)
        messages = wall.messages_for_user(self.request.user)

        context['wall'] = wall
        context['wallmessages'] = paginate(self.request, messages, 20)
        return context

    def get(self, request, groupid):
        self.request = request
        self.groupid = groupid
        return super(ViewGroup, self).get(request)


class EditGroup(TemplateView):
    template_name = 'truekko/edit_group.html'

    def get_context_data(self, **kwargs):
        context = super(EditGroup, self).get_context_data(**kwargs)
        g = get_object_or_404(Group, pk=self.groupid)
        context['form'] = GroupForm(instance=g)
        context['klass'] = 'group'
        context['group'] = g
        context['menu'] = generate_menu("group")
        return context

    def get(self, request, groupid):
        self.request = request
        self.groupid = groupid
        return super(EditGroup, self).get(request)

    def post(self, request, groupid):
        self.groupid = groupid
        g = get_object_or_404(Group, pk=self.groupid)
        data = request.POST

        files_req = request.FILES
        if (files_req.get('photo', '')):
            files_req['photo'].name = "group_%s" % g.id

        form = GroupForm(request.POST, files_req, instance=g)
        if not form.is_valid():
            menu = generate_menu("group")
            context = RequestContext(request, {'group': g, 'form': form, 'menu': menu})
            context['klass'] = 'group'
            return render_to_response(EditGroup.template_name, context)

        form.save()

        nxt = redirect('view_group', groupid)
        return nxt


class EditGroupMembers(TemplateView):
    template_name = 'truekko/edit_group_members.html'

    def get_context_data(self, **kwargs):
        context = super(EditGroupMembers, self).get_context_data(**kwargs)
        g = get_object_or_404(Group, pk=self.groupid)
        context['form'] = GroupForm(instance=g)
        context['klass'] = 'group'
        context['group'] = g
        context['requests'] = g.membership_set.filter(role="REQ").order_by("-id")
        context['memberships'] = g.membership_set.exclude(role__in=["REQ", "BAN"]).order_by("-id")
        context['banned'] = g.membership_set.filter(role="BAN").order_by("-id")
        context['menu'] = generate_menu("group")
        return context

    def get(self, request, groupid):
        self.request = request
        self.groupid = groupid
        return super(EditGroupMembers, self).get(request)

    def post(self, request, groupid):
        self.groupid = groupid
        g = get_object_or_404(Group, pk=self.groupid)
        data = request.POST

        def notify_user(user):
            context = {'group': g, 'user': user, 'url': reverse('view_group', args=[groupid])}
            template_email('truekko/user_member_mail.txt',
                           _("Membership request confirmed %s") % g.name,
                           [user.email], context)

        for k, v in data.items():
            if k.startswith("role_"):
                role, uid = k.split("_")
                m = Membership.objects.get(user__id=uid, group=g)
                if data[k] == "admin":
                    if m.role == "REQ":
                        notify_user(m.user)
                    m.role = "ADM"
                    m.save()
                elif data[k] == "req":
                    m.role = "REQ"
                    m.save()
                elif data[k] == "member":
                    if m.role == "REQ":
                        notify_user(m.user)
                    m.role = "MEM"
                    m.save()
                elif data[k] == "ban":
                    m.role = "BAN"
                    m.save()
                elif data[k] == "remove":
                    m.delete()

                if not m.user.is_active and data[k] in ["admin", "member"]:
                    m.user.is_active = True
                    m.user.save()

        messages.info(request, _("Community memebership modified correctly"))

        nxt = redirect('view_group', groupid)
        return nxt


class Register(TemplateView):

    template_name = 'truekko/register.html'

    def get_context_data(self, **kwargs):
        context = super(Register, self).get_context_data(**kwargs)
        g = get_object_or_404(Group, pk=self.groupid)
        context['form'] = RegisterForm()
        context['klass'] = 'group'
        context['group'] = g
        context['menu'] = generate_menu("group")
        return context

    def get(self, request, groupid):
        self.request = request
        self.groupid = groupid
        return super(Register, self).get(request)

    def post(self, request, groupid):
        self.groupid = groupid
        g = get_object_or_404(Group, pk=self.groupid)
        data = request.POST

        f = RegisterForm(data)
        if not f.is_valid():
            context = RequestContext(request, {})
            context['klass'] = 'group'
            context['group'] = g
            context['menu'] = generate_menu("group")
            context['form'] = f
            return render_to_response(Register.template_name, context)

        f.save(g)

        # sending mail to user and admins
        context = dict(f.data.items())
        context['group'] = g
        template_email('truekko/user_registered_mail.txt', _("Welcome to etruekko"), [f.data['email']], context)
        context['url'] = reverse('edit_group_members', args=(groupid,))
        template_email('truekko/user_registered_admin_mail.txt',
                       _("New user '%(user)s' in community '%(group)s'") % dict(user=f.data['username'], group=g.name),
                       g.admins_emails(), context)

        nxt = redirect('register_confirm', groupid)
        return nxt


class RegisterSingle(TemplateView):

    template_name = 'truekko/register_single.html'

    def get_context_data(self, **kwargs):
        context = super(RegisterSingle, self).get_context_data(**kwargs)
        context['form'] = RegisterForm()
        context['klass'] = 'home'
        context['menu'] = generate_menu("home")
        return context

    def post(self, request):
        data = request.POST

        f = RegisterForm(data)
        if not f.is_valid():
            context = RequestContext(request, {})
            context['klass'] = 'home'
            context['menu'] = generate_menu("home")
            context['form'] = f
            return render_to_response(self.template_name, context)

        f.save()

        # sending mail to user and admins
        context = dict(f.data.items())
        context['groupurl'] = reverse('groups')
        template_email('truekko/single_user_registered_mail.txt', _("Welcome to etruekko"), [f.data['email']], context)

        msg = _("Conglatulations! You're now part of etruekko. Loggin in and start to make a better work")
        messages.info(request, msg)

        return redirect('index')


class RegisterAdmin(TemplateView):

    template_name = 'truekko/register_admin.html'

    def get_context_data(self, **kwargs):
        context = super(RegisterAdmin, self).get_context_data(**kwargs)
        g = get_object_or_404(Group, pk=self.groupid)
        context['form'] = RegisterForm()
        context['klass'] = 'group'
        context['group'] = g
        context['menu'] = generate_menu("group")
        return context

    def get_context(self, data):
        context = RequestContext(self.request, data)
        context['klass'] = 'group'
        context['menu'] = generate_menu("group")
        return context

    def get(self, request, groupid):
        self.request = request
        self.groupid = groupid
        return super(RegisterAdmin, self).get(request)

    def post(self, request, groupid):
        self.groupid = groupid
        g = get_object_or_404(Group, pk=self.groupid)
        data = request.POST

        if 'existing' in data:
            username = data.get('existinguser', '')
            try:
                u = User.objects.get(username=username)
            except:
                msg = _("The user '%s' doesn't exist") % username
                messages.info(request, msg)
                return render_to_response(RegisterAdmin.template_name,
                                          self.get_context({'group': g, 'form': RegisterForm()}))
                return redirect('edit_group_members', groupid)

            if (Membership.objects.filter(user=u, group=g).count()):
                msg = _("The user '%s' is already member of the community") % username
                messages.info(request, msg)
                return render_to_response(RegisterAdmin.template_name,
                                          self.get_context({'group': g, 'form': RegisterForm()}))
                return redirect('edit_group_members', groupid)

            m = Membership(user=u, group=g, role='REQ')
            m.save()

            msg = _("A new membership request has been created, you need to confirm")
            messages.info(request, msg)
            return redirect('edit_group_members', groupid)

        f = RegisterForm(data)
        if not f.is_valid():
            return render_to_response(RegisterAdmin.template_name,
                                      self.get_context({'group': g, 'form': f}))

        f.save(g)

        # sending mail to user
        context = dict(f.data.items())
        context['group'] = g
        template_email('truekko/user_registered_mail.txt', _("Welcome to etruekko"), [context['email']], context)

        nxt = redirect('edit_group_members', groupid)
        return nxt


class RegisterConfirm(TemplateView):
    template_name = 'truekko/register_confirm.html'

    def get_context_data(self, **kwargs):
        context = super(RegisterConfirm, self).get_context_data(**kwargs)
        g = get_object_or_404(Group, pk=self.groupid)
        context['klass'] = 'group'
        context['group'] = g
        context['menu'] = generate_menu("group")
        return context

    def get(self, request, groupid):
        self.request = request
        self.groupid = groupid
        return super(RegisterConfirm, self).get(request)


class JoinGroup(View):

    def post(self, request, groupid):
        g = get_object_or_404(Group, pk=groupid)
        data = request.POST

        if request.user.is_anonymous():
            return redirect('register_group', groupid)

        if is_member(request.user, g):
            msg = _("You already are member of this community")
        else:
            m, created = Membership.objects.get_or_create(user=request.user, group=g, role='REQ')
            m.save()
            # sending email to group admin
            context = {'group': g, 'username': request.user.username, 'user': request.user,
                       'url': reverse('edit_group_members', args=(groupid,))}
            template_email('truekko/user_registered_admin_mail.txt',
                           _("New user '%(user)s' in community '%(group)s'") % dict(user=request.user.username, group=g.name),
                           g.admins_emails(), context)

            msg = _("Your membership request has been sent to community administrator")

        messages.info(request, msg)
        nxt = redirect('view_group', groupid)
        return nxt


class LeaveGroup(View):

    def post(self, request, groupid):
        g = get_object_or_404(Group, pk=groupid)
        data = request.POST

        if len(g.admins()) == 1 and g.is_admin(self.request.user):
            msg = _("You are the only admin of this community. "
                    "You can't leave until you set a new admin")

            messages.info(request, msg)
            return redirect('view_group', groupid)


        if is_member(request.user, g):
            m = Membership.objects.get(user=request.user, group=g)
            m.delete()

        msg = _("You are not member of this community")

        messages.info(request, msg)
        nxt = redirect('view_group', groupid)
        return nxt

# denounce

class GroupDenounce(TemplateView):
    template_name = 'truekko/group_denounce.html'

    def get_context_data(self, **kwargs):
        context = super(GroupDenounce, self).get_context_data(**kwargs)
        context['klass'] = 'group'
        context['group'] = self.group
        context['memberships'] = self.group.membership_set.exclude(role__in=["REQ", "BAN"]).order_by("-id")
        context['menu'] = generate_menu("group")
        return context

    def get(self, request, groupid):
        self.request = request
        self.group = get_object_or_404(Group, pk=groupid)
        return super(GroupDenounce, self).get(request)


class GroupDenounceUser(TemplateView):
    template_name = 'truekko/group_denounce_user.html'

    def get_context_data(self, **kwargs):
        context = super(GroupDenounceUser, self).get_context_data(**kwargs)
        context['klass'] = 'group'
        context['group'] = self.group
        context['denounced'] = self.user
        context['menu'] = generate_menu("group")
        return context

    def get(self, request, groupid, username):
        self.request = request
        self.group = get_object_or_404(Group, pk=groupid)
        self.user = get_object_or_404(User, username=username)
        return super(GroupDenounceUser, self).get(request)

    def post(self, request, groupid, username):
        self.request = request
        self.group = get_object_or_404(Group, pk=groupid)
        self.user = get_object_or_404(User, username=username)

        msg = request.POST.get('msg', '')

        d = Denounce(user_from=request.user,
                     user_to=self.user,
                     group=self.group,
                     msg=msg)
        d.save()
        messages.info(request, _("User has been denounced correctly"))
        messages.info(request, _("You should receive an email"))

        return redirect('group_denounce_view', d.id)


class GroupDenounceView(TemplateView):
    template_name = 'truekko/group_denounce_view.html'

    def get_context_data(self, **kwargs):
        context = super(GroupDenounceView, self).get_context_data(**kwargs)
        context['klass'] = 'group'
        context['denounce'] = self.denounce
        context['group'] = self.denounce.group
        context['denounced'] = self.denounce.user_to
        context['denouncer'] = self.denounce.user_from
        context['admin'] = self.denounce.group.is_admin(self.request.user)
        context['menu'] = generate_menu("group")
        return context

    def get(self, request, did):
        self.request = request
        self.denounce = get_object_or_404(Denounce, pk=did)
        viewers = self.denounce.group.admins() + [self.denounce.user_from, self.denounce.user_to]
        if not request.user in viewers:
            raise Http404
        return super(GroupDenounceView, self).get(request)

    def post(self, request, did):
        self.request = request
        self.denounce = get_object_or_404(Denounce, pk=did)
        if not self.denounce.group.is_admin(request.user):
            raise Http404

        st = "PEN"
        if 'con' in request.POST.keys():
            st = "CON"
        elif 'res' in request.POST.keys():
            st = "RES"
        elif 'can' in request.POST.keys():
            st = "CAN"
        self.denounce.status = st
        self.denounce.save()
        return redirect('group_denounce_view', self.denounce.id)


#############
#           #
# TRANSFER  #
#           #
#############


class TransferDirect(TemplateView):
    template_name = 'truekko/transfer_direct.html'

    def get_context(self, data):
        context = RequestContext(self.request, data)
        context['klass'] = 'transf'
        context['menu'] = generate_menu("transf")
        return context

    def get_context_data(self, **kwargs):
        context = super(TransferDirect, self).get_context_data(**kwargs)
        u = get_object_or_404(User, username=self.username)
        context['user_to'] = u
        context['form'] = TransferDirectForm(self.request.user, u)
        context['klass'] = 'transf'
        context['menu'] = generate_menu("transf")
        return context

    def get(self, request, username):
        self.request = request
        self.username = username
        return super(TransferDirect, self).get(request)

    def post(self, request, username):
        self.request = request
        self.username = username
        u = get_object_or_404(User, username=self.username)
        data = request.POST

        f = TransferDirectForm(self.request.user, u, data)
        if not f.is_valid():
            return render_to_response(TransferDirect.template_name,
                                      self.get_context({'user_to': u, 'form': f}))

        f.save()

        # sending mail to both users
        context = dict(f.data.items())
        context['user_from'] = request.user
        context['user_to'] = u
        #template_email('truekko/transfer_direct_mail.txt', _("Direct transfer"), [u.email, request.user.email], context)
        messages.info(request, _("Transfer has been made correctly"))

        nxt = redirect('view_profile', u.username)
        return nxt


class TransferList(TemplateView):
    template_name = 'truekko/transfer_list.html'

    def get_context_data(self, **kwargs):
        context = super(TransferList, self).get_context_data(**kwargs)
        context['klass'] = 'transf'
        context['menu'] = generate_menu("transf")

        tq = Q(user_from=self.request.user) | Q(user_to=self.request.user)
        query = Transfer.objects.filter(tq)

        q = self.request.GET.get('search', '')
        if q:
            k = Q(user_from__username__icontains=q) |\
                Q(user_from__email__icontains=q) |\
                Q(user_from__userprofile__name__icontains=q) |\
                Q(user_from__userprofile__location__icontains=q) |\
                Q(user_to__username__icontains=q) |\
                Q(user_to__email__icontains=q) |\
                Q(user_to__userprofile__name__icontains=q) |\
                Q(user_to__userprofile__location__icontains=q)

            query = query.filter(k)

        query = query.order_by('-date')[:20]

        query2 = Swap.objects.filter(tq)
        if q:
            k = Q(user_from__username__icontains=q) |\
                Q(user_from__email__icontains=q) |\
                Q(user_from__userprofile__name__icontains=q) |\
                Q(user_from__userprofile__location__icontains=q) |\
                Q(user_to__username__icontains=q) |\
                Q(user_to__email__icontains=q) |\
                Q(user_to__userprofile__name__icontains=q) |\
                Q(user_to__userprofile__location__icontains=q)

            query2 = query2.filter(k).order_by('-date')[:20]

        queries = [i for i in query] + [i for i in query2]
        queries = sorted(queries, key=lambda x: x.date, reverse=True)

        context['transfs'] = paginate(self.request, queries, 20)
        return context

    def get(self, request):
        self.request = request
        return super(TransferList, self).get(request)


########
#      #
# SWAP #
#      #
########


class SwapCreation(TemplateView):
    template_name = 'truekko/swap_creation.html'

    def get_context(self, data):
        context = RequestContext(self.request, data)
        context['klass'] = 'transf'
        context['menu'] = generate_menu("transf")
        context['swap_opts'] = Swap.SWAP_MODE
        return context

    def get_context_data(self, **kwargs):
        context = super(SwapCreation, self).get_context_data(**kwargs)
        u = get_object_or_404(User, username=self.username)
        context = self.get_context({'user_to': u, 'user_from': self.request.user})
        #f = CommitmentForm([self.request.user.id, u.id])
        f = CommitmentForm()
        context['commitment_form'] = f
        context['items'] = [int(i) for i in self.request.GET.getlist('item')]
        return context

    def get(self, request, username):
        self.request = request
        self.username = username
        return super(SwapCreation, self).get(request)

    def post(self, request, username):
        self.request = request
        self.username = username
        u = get_object_or_404(User, username=self.username)
        data = request.POST

        items = []
        for k in data.keys():
            if k.startswith('item_'):
                items.append(int(k.split('_')[1]))

        credits1 = data.get('credits1', '0')
        credits2 = data.get('credits2', '0')
        swap_mode = data.get('swap_mode', 'NON')
        credits1 = credits1 if credits1 else '0'
        credits2 = credits2 if credits2 else '0'

        swap = Swap(status="US1",
                    credits_from=credits1,
                    credits_to=credits2,
                    swap_mode=swap_mode,
                    user_from=self.request.user,
                    user_to=u)

        swap.credits_from = credits1
        swap.credits_to = credits2

        if not swap.is_valid():
            context = self.get_context({'user_to': u,
                                        'user_from': self.request.user,
                                        'credits1': credits1,
                                        'credits2': credits2})
            context['items'] = items
            context['errors'] = [_("Invalid credits, you can't offer"
            " more than you have, and you can't request more that the"
            " other person has")]
            return render_to_response(SwapCreation.template_name, context)

        swap.save()

        for item in items:
            i = Item.objects.get(id=item)
            si = SwapItems(swap=swap, item=i)
            si.save()

        comment = data.get('comment', '')
        if comment:
            swap_comment = SwapComment(swap=swap,
                                       user=self.request.user,
                                       comment=comment)
            swap_comment.save()

        nxt = redirect('swap_view', swap.id)
        url = reverse('swap_view', args=(swap.id,))

        context = {'swap': swap, 'comment': comment, 'url': url}
        template_email('truekko/swap_creation_mail.txt',
                       _("A new swap has been created"),
                       [swap.user_to.email], context)

        return nxt


class SwapView(TemplateView):
    template_name = 'truekko/swap_creation.html'

    def get_context(self, data):
        context = RequestContext(self.request, data)
        context['klass'] = 'transf'
        context['menu'] = generate_menu("transf")
        context['swap_opts'] = Swap.SWAP_MODE
        return context

    def get_context_data(self, **kwargs):
        context = super(SwapView, self).get_context_data(**kwargs)
        context = self.get_context({'user_to': self.swap.user_to,
                                    'user_from': self.swap.user_from})
        #f = CommitmentForm([self.swap.user_to.id, self.swap.user_from.id])
        f = CommitmentForm()
        context['commitment_form'] = f
        context['items'] = [item.item.id for item in self.swap.items.all()]
        context['credits1'] = self.swap.credits_from
        context['credits2'] = self.swap.credits_to
        context['comments'] = self.swap.comments.all()
        context['swap'] = self.swap
        context['userto'] = self.swap.user_to if self.request.user == self.swap.user_from else self.swap.user_from
        if self.request.user == self.swap.user_from and self.swap.status == 'US2':
            context['accept'] = True
        if self.request.user == self.swap.user_to and self.swap.status == 'US1':
            context['accept'] = True

        context['swapstatus'] = self.swap.get_status_msg()

        return context

    def get(self, request, swapid):
        self.request = request
        self.swap = get_object_or_404(Swap, id=swapid)
        if request.user != self.swap.user_to and\
           request.user != self.swap.user_from:
            messages.info(request, _("You can't view this swap"))
            return redirect('/')

        return super(SwapView, self).get(request)

    def post(self, request, swapid):
        self.request = request
        self.swap = get_object_or_404(Swap, id=swapid)
        data = request.POST

        items = []
        for k in data.keys():
            if k.startswith('item_'):
                items.append(int(k.split('_')[1]))

        # comment
        comment = data.get('comment', '')
        if comment:
            swap_comment = SwapComment(swap=self.swap,
                                       user=self.request.user,
                                       comment=comment)
            swap_comment.save()

        if self.swap.status in ['CAN', 'CON', 'DON']:
            self.swap.save()
            return redirect('swap_view', self.swap.id)

        if 'cancel' in data.keys():
            self.swap.status = 'CAN'
            # deleting commitments
            self.swap.commitments.all().delete()
            self.swap.save()
            messages.info(request, _("Swap canceled"))
            return redirect('swap_view', self.swap.id)

        if 'accept' in data.keys():
            nxt = redirect('swap_view', self.swap.id)
            if self.request.user == self.swap.user_to and self.swap.status != 'US1':
                return nxt
            if self.request.user == self.swap.user_from and self.swap.status != 'US2':
                return nxt

            self.swap.status = 'CON'
            if self.swap.is_valid():
                self.swap.save()
                self.swap.commitments.all().update(status="WAI")
                messages.info(request, _("Conglatulations, swap has been accepted"))
            else:
                context = self.get_context({'user_to': self.swap.user_to,
                                            'user_from': self.swap.user_from,
                                            'credits1': self.swap.credits_from,
                                            'credits2': self.swap.credits_to})
                context['items'] = items
                context['errors'] = [_("Invalid credits, you can't offer"
                " more than you have, and you can't request more that the"
                " other person has")]
                return render_to_response(SwapView.template_name, context)
            return nxt

        credits1 = data.get('credits1', '0')
        credits2 = data.get('credits2', '0')
        swap_mode = data.get('swap_mode', 'NON')
        credits1 = credits1 if credits1 else '0'
        credits2 = credits2 if credits2 else '0'

        self.swap.swap_mode = swap_mode
        self.swap.credits_from = credits1
        self.swap.credits_to = credits2

        if not self.swap.is_valid():
            context = self.get_context({'user_to': self.swap.user_to,
                                        'user_from': self.swap.user_from,
                                        'credits1': credits1,
                                        'credits2': credits2})
            context['items'] = items
            context['errors'] = [_("Invalid credits, you can't offer"
            " more than you have, and you can't request more that the"
            " other person has")]
            return render_to_response(SwapView.template_name, context)

        self.swap.save()

        for swap_item in self.swap.items.all():
            if swap_item.item.id not in items:
                swap_item.delete()

        for item in items:
            i = Item.objects.get(id=item)
            si, created = SwapItems.objects.get_or_create(swap=self.swap, item=i)
            if created:
                si.save()

        if 'offer' in data.keys():
            if self.request.user == self.swap.user_to:
                self.swap.status = 'US2'
            if self.request.user == self.swap.user_from:
                self.swap.status = 'US1'

            self.swap.save()

        nxt = redirect('swap_view', self.swap.id)
        return nxt


class SwapList(TemplateView):
    template_name = 'truekko/swap_list.html'

    def get_context_data(self, **kwargs):
        context = super(SwapList, self).get_context_data(**kwargs)
        context['klass'] = 'transf'
        context['menu'] = generate_menu("transf")

        tq = Q(user_from=self.request.user) | Q(user_to=self.request.user)
        query = Swap.objects.filter(tq)

        q = self.request.GET.get('search', '')
        if q:
            k = Q(user_from__username__icontains=q) |\
                Q(user_from__email__icontains=q) |\
                Q(user_from__userprofile__name__icontains=q) |\
                Q(user_from__userprofile__location__icontains=q) |\
                Q(user_to__username__icontains=q) |\
                Q(user_to__email__icontains=q) |\
                Q(user_to__userprofile__name__icontains=q) |\
                Q(user_to__userprofile__location__icontains=q)

            query = query.filter(k)

        context['swaps'] = paginate(self.request, query.order_by('status'), 10)
        return context

    def get(self, request):
        self.request = request
        return super(SwapList, self).get(request)


class CommitmentCreate(View):
    def post(self, request, sid):
        swap = get_object_or_404(Swap, pk=sid)
        #f = CommitmentForm([swap.user_to.id, swap.user_from.id], request.POST)
        f = CommitmentForm(request.POST)
        cm = f.save(commit=False)
        cm.user_from = self.request.user
        cm.user_to = swap.user_to if swap.user_from == self.request.user else swap.user_from
        cm.swap = swap
        cm.save()

        return redirect('swap_view', cm.swap.id)


class CommitmentDone(View):
    def post(self, request, cid):
        cm = get_object_or_404(Commitment, pk=cid, user_to=request.user)
        cm.done()
        cm.save()

        return redirect('swap_view', cm.swap.id)


class CommitmentDelete(View):
    def post(self, request, cid):
        cm = get_object_or_404(Commitment, pk=cid)
        swapid = cm.swap.id
        if cm.status == "NEG" and cm.user_to == request.user or cm.user_from == request.user:
            cm.delete()

        return redirect('swap_view', swapid)


###########
#         #
#  ITEMS  #
#         #
###########


class ItemAdd(TemplateView):
    template_name = 'truekko/item_add.html'

    def get_context(self, data):
        context = RequestContext(self.request, data)
        context['klass'] = 'add'
        context['menu'] = generate_menu("add")
        context['item'] = None
        if self.item:
            context['form'] = ItemAddForm(instance=self.item)
            context['editing'] = True
            context['item'] = self.item
        else:
            context['form'] = ItemAddForm()
        return context

    def get_context_data(self, **kwargs):
        context = super(ItemAdd, self).get_context_data(**kwargs)
        context = self.get_context(context)
        return context

    def get(self, request, object_id=None):
        self.request = request
        self.item = None
        if object_id:
            self.item = get_object_or_404(Item, id=object_id, user=self.request.user)
        return super(ItemAdd, self).get(request)

    def post(self, request, object_id=None):
        stay_here = False
        self.item = None
        if object_id:
            self.item = get_object_or_404(Item, id=object_id, user=self.request.user)

        files_req = request.FILES
        itemimages = []
        for f in files_req:
            freq = files_req[f]
            if validate_image(freq):
                freq.name = "item_%s" % uuid.uuid4().hex
                itemimages.append(freq)
            else:
                messages.error(request, _("Invalid image format: %(name)s") % {'name': freq.name})
                stay_here = True

        if self.item:
            form = ItemAddForm(request.POST, instance=self.item)
        else:
            form = ItemAddForm(request.POST)

        try:
            quantity = int(request.POST.get('quantity', '0'))
            quantity_valid = True
        except:
            quantity_valid = False

        if not form.is_valid() or not quantity_valid:
            context = self.get_context({})
            context['form'] = form
            return render_to_response(ItemAdd.template_name, context)

        item = form.save(commit=False)
        item.quantity = 0
        if item.type == 'IT' and item.offer_or_demand == 'OFF':
            item.quantity = quantity

        item.user = self.request.user
        item.save()

        # adding images
        for im in itemimages:
            itemim = ItemImage(item=item, photo=im)
            itemim.save()

        # removing images:
        l = [i.split("_")[1] for i in request.POST if i.startswith("rmimg")]
        ItemImage.objects.filter(id__in=l).delete()

        # parsing tags
        tags = request.POST.get('tags')
        if tags:
            tagnames = [i.strip() for i in request.POST.get('tags').split(',')]
            for tag in tagnames:
                dbtag, created = Tag.objects.get_or_create(name=tag)
                it, created = ItemTagged.objects.get_or_create(item=item, tag=dbtag)

            oldtags = ItemTagged.objects.filter(item=item)\
                                         .exclude(tag__name__in=tagnames)
            oldtags.delete()

        if stay_here:
            nxt = redirect('item_edit', item.id)
        else:
            nxtsrv = 'item'
            if item.type == "IT":
                messages.info(request, _("Item added correctly"))
            else:
                messages.info(request, _("Service added correctly"))
                nxtsrv = 'serv'

            nxt = redirect('item_view', item.id)
        return nxt


class ItemView(TemplateView):
    template_name = 'truekko/item_view.html'

    def get_context_data(self, **kwargs):
        context = super(ItemView, self).get_context_data(**kwargs)

        item = get_object_or_404(Item, pk=self.itemid)
        if item.type == "IT":
            klass = 'item'
        else:
            klass = 'serv'

        context['klass'] = klass
        context['menu'] = generate_menu(klass)
        context['item'] = item
        return context

    def get(self, request, itemid):
        self.request = request
        self.itemid = itemid

        return super(ItemView, self).get(request)


class ItemList(TemplateView):
    template_name = 'truekko/item_list.html'

    def get_filters(self):
        filters = SortedDict()
        filters['all'] = {'text': _("All"), 'query': Q()}
        u = self.request.user

        if not u.is_authenticated():
            return filters

        filters['friends'] = {'text': _("Only Friends"), 'query': Q(user__followers__follower=u)}

        for g in u.get_profile().groups():
            filters['community%d' % g.id] = {'text': g.name, 'query': Q(user__membership__group=g)}

        return filters

    def get_context_data(self, **kwargs):
        context = super(ItemList, self).get_context_data(**kwargs)
        context['klass'] = self.klass
        context['menu'] = generate_menu(self.klass)
        context['filters'] = self.get_filters()
        context['sfilter'] = self.filter_name

        query = Item.objects.filter(type=self.itemtype).filter(self.filter['query'])

        q = self.request.GET.get('search', '')
        if q:
            k = Q(name__icontains=q) |\
                Q(description__icontains=q) |\
                Q(user__username__icontains=q) |\
                Q(user__userprofile__location__icontains=q) |\
                Q(user__userprofile__name__icontains=q)

            itemtagged = ItemTagged.objects.filter(tag__name__icontains=q)
            for it in itemtagged:
                k = k | Q(itemtagged=it)

            query = query.filter(k).distinct()

        context['items'] = paginate(self.request, query.order_by('-pub_date'), 10)
        return context

    def get(self, request, itemtype, filter_name=None):
        self.request = request

        self.filter_name = filter_name or "all"
        self.filter = self.get_filters().get(self.filter_name, None)
        if not self.filter:
            self.filter = self.get_filters()['all']

        if itemtype == "item":
            self.itemtype = "IT"
            self.klass = 'item'
        else:
            self.itemtype = "SR"
            self.klass = 'serv'

        return super(ItemList, self).get(request)


class ItemRemove(TemplateView):
    template_name = 'truekko/item_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super(ItemRemove, self).get_context_data(**kwargs)
        context['klass'] = self.klass
        context['menu'] = generate_menu(self.klass)
        context['item'] = self.item
        return context

    def get(self, request, itemid):
        self.request = request
        self.item = get_object_or_404(Item, pk=itemid, user=request.user)

        if self.item.type == "IT":
            self.klass = 'item'
        else:
            self.klass = 'serv'
        return super(ItemRemove, self).get(request)

    def post(self, request, itemid):
        self.request = request
        self.item = get_object_or_404(Item, pk=itemid, user=request.user)
        self.item.delete()

        messages.info(request, _(u"Item removed correctly"))

        return redirect(index)


##############
#            #
#  MESSAGES  #
#            #
##############


class MessagePost(View):

    def post_notify(self, msg):
        wall = Wall.notification()
        wmsg = WallMessage(user=self.request.user,
                           wall=wall,
                           msg=msg)
        wmsg.save()
        return redirect("/")

    def post(self, request, wallid):
        wall = get_object_or_404(Wall, pk=wallid)
        msg = request.POST.get('comment', '')
        reply = request.POST.get('reply', '')
        priv = bool(request.POST.get('priv', False))

        notify = request.POST.get("notify", False)
        if notify and request.user.is_superuser:
            return self.post_notify(msg)

        # TODO check post permissions
        if not self.can_post(request.user, wall):
            messages.info(request, _(u"You can't post here"))
        else:
            wmsg = WallMessage(user=request.user,
                               wall=wall,
                               msg=msg,
                               private=priv)
            if reply:
                reply = get_object_or_404(WallMessage, pk=reply)
                wmsg.parent = reply
                reply.date = datetime.datetime.now()
                reply.save()

            wmsg.save()
            messages.info(request, _(u"Message posted correctly"))

        # redirecting to prev page
        referer = request.META['HTTP_REFERER']
        if not referer:
            return redirect("/")

        return redirect(referer)

    def can_post(self, user, wall):
        if wall.user == user:
            return True
        if wall.group:
            return is_member(user, wall.group)

        # TODO only can post in friend walls

        return True


class MessageRemove(TemplateView):
    template_name = 'truekko/message_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super(MessageRemove, self).get_context_data(**kwargs)
        context['menu'] = generate_menu()
        context['msg'] = self.msg
        return context

    def get(self, request, msgid):
        self.request = request
        self.msg = get_object_or_404(WallMessage, pk=msgid, user=request.user)

        return super(MessageRemove, self).get(request)

    def post(self, request, msgid):
        self.request = request
        self.msg = get_object_or_404(WallMessage, pk=msgid, user=request.user)
        self.msg.delete()

        messages.info(request, _(u"Message removed correctly"))

        return redirect(index)


class PasswordResetDoneView(TemplateView):
    def get(self, request):
        messages.info(request, _('An e-mail has been '
                                 'send to you which explains how to reset your password'))
        return redirect('/')


class PasswordResetCompleteView(TemplateView):
    def get(self, request):
        messages.add_message(request, messages.SUCCESS, _('Your password has '
              'been reset, you can now <a href="%(url)s">login</a> with your '
              'new password') % dict(url=reverse(index)))
        return redirect('/')


class RegisterWizard(TemplateView):
    template_name = 'truekko/user_register.html'

    def register_tip(self):
        if settings.REGISTER_TIP and Group.objects.all().count():
            try:
                community = Group.objects.get(name=settings.REGISTER_COMMUNITY)
            except:
                community = Group.objects.all()[0]
            link = reverse('register_group', args=[community.id])
            name = community.name

            return settings.REGISTER_TIP % {'name': name, 'link': link}
        else:
            return ''

    def get_context_data(self, **kwargs):
        context = super(RegisterWizard, self).get_context_data(**kwargs)
        context['klass'] = 'group'
        context['menu'] = generate_menu("group")
        context['register_tip'] = self.register_tip()

        q = self.request.GET.get('search', '')
        if q:
            k = Q(email__icontains=q) |\
                Q(description__icontains=q) |\
                Q(name__icontains=q) |\
                Q(location__icontains=q)

            query = Group.objects.filter(k)
        else:
            query = Group.objects.all()
        context['groups'] = paginate(self.request, query, 10)
        return context

    def get(self, request):
        self.request = request

        return super(RegisterWizard, self).get(request)


class SearchAdvanced(TemplateView):
    template_name = 'search/advanced.html'

    def get_context_data(self, **kwargs):
        context = super(SearchAdvanced, self).get_context_data(**kwargs)
        context['menu'] = generate_menu("")
        context['query'] = ''
        context['result'] = ''
        context['channels'] = Channel.objects.all()

        data = self.request.GET.dict()
        context['channel_selected'] = data.get('channel', 'all')

        if data.get('query', ''):
            query = self.query(data)

            # paginating the query
            result = paginate(self.request, query, 20)
            context['result'] = result

            if data.get('page', ''):
                del data['page']

            context['query'] = '&'.join(u'%s=%s' % (k,v) for k,v in data.items())

        else:
            # for initial checkbox selection
            data['offer'] = "on"
            data['demand'] = "on"
            data['item'] = "on"
            data['serv'] = "on"

        context['data'] = data
        return context

    def get(self, request):
        self.request = request

        return super(SearchAdvanced, self).get(request)

    def query(self, data):
        models = dict(item=Item, group=Group, user=UserProfile)
        modelname = data.get('type', '')

        q = data.get('q', '')
        offer = data.get('offer', False)
        demand = data.get('demand', False)
        item = data.get('item', False)
        serv = data.get('serv', False)
        location = data.get('location', '')
        channel = data.get('channel', 'all')

        if channel != "all":
            channel = get_object_or_404(Channel, pk=channel)
        else:
            channel = None

        # getting the model to query
        model = models.get(modelname, Item)

        sf = self.create_filters(modelname, q, location,
                                  serv, item, offer, demand, channel)

        if unidecode(q) != q or unidecode(location) != location:
            sf = sf | self.create_filters(modelname, unidecode(q),
                                          unidecode(location),
                                          serv, item, offer, demand,
                                          channel)

        # getting the objects
        query = model.objects.filter(sf)

        return query

    def create_filters(self, modelname, q, location, serv, item, offer, demand, channel):
        # building the query
        sf = Q()
        if modelname == 'item':
            if q:
                sf = Q(name__icontains=q) |\
                    Q(description__icontains=q) |\
                    Q(user__username__icontains=q) |\
                    Q(user__userprofile__location__icontains=q) |\
                    Q(user__userprofile__name__icontains=q)

                itemtagged = ItemTagged.objects.filter(tag__name__icontains=q)
                for it in itemtagged:
                    sf = sf | Q(itemtagged=it)

            if location:
                sf = sf & Q(user__userprofile__location__icontains=location)

            if channel:
                sf = sf & Q(user__membership__group__channel=channel)

            if not serv:
                sf = sf & ~Q(type="SR")
            if not item:
                sf = sf & ~Q(type="IT")
            if not offer:
                sf = sf & ~Q(offer_or_demand="OFF")
            if not demand:
                sf = sf & ~Q(offer_or_demand="DEM")

        elif modelname == 'group':
            if q:
                sf = Q(email__icontains=q) |\
                     Q(description__icontains=q) |\
                     Q(name__icontains=q) |\
                     Q(location__icontains=q)

            if location:
                sf = sf & Q(location__icontains=location)

            if channel:
                sf = sf & Q(channel=channel)

        elif modelname == 'user':
            if q:
                sf = Q(user__email__icontains=q) |\
                     Q(user__username__icontains=q) |\
                     Q(description__icontains=q) |\
                     Q(name__icontains=q) |\
                     Q(location__icontains=q)

            if location:
                sf = sf & Q(location__icontains=location)

            if channel:
                sf = sf & Q(user__membership__group__channel=channel)

        return sf


#############
#           #
# FOLLOWING #
#           #
#############

class FollowView(View):

    def post(self, request, userid, js=None):
        user = get_object_or_404(User, pk=userid)
        if user == request.user:
            raise Http404

        f, created = Follow.objects.get_or_create(follower=request.user, following=user)
        f.save()

        msg = _(u"You are now following %(user)s in etruekko") % {'user': user.username}
        url = reverse('view_profile', args=(request.user.username,))
        context = {'user': request.user, 'you': user, 'url': url}
        template_email('truekko/follow_mail.txt',
                       _("%(name)s (%(username)s) is now following you in etruekko") %\
                            {'name': request.user.get_profile().name,
                            'username': request.user.username},
                       [user.email], context)

        if js:
            json_response = json.dumps({'status': 'ok',
                        'url': reverse('unfollow', args=(userid,)),
                        'text': _("unfollow"),
                        'msg': msg})
            return HttpResponse(json_response, mimetype='application/json')
        else:
            messages.info(request, msg)
            return redirect('view_profile', user.username)

    get = post


class UnFollowView(View):

    def post(self, request, userid, js=None):
        user = get_object_or_404(User, pk=userid)
        f = get_object_or_404(Follow, follower=request.user, following=user)
        f.delete()

        msg = _(u"You are not following %(user)s in etruekko anymore") % {'user': user.username}

        if js:
            json_response = json.dumps({'status': 'ok',
                'url': reverse('follow', args=(userid,)),
                'text': _("follow"),
                'msg': msg})
            return HttpResponse(json_response, mimetype='application/json')
        else:
            messages.info(request, msg)
            return redirect('view_profile', user.username)

    get = post


class FollowersView(TemplateView):
    template_name = 'truekko/userlist.html'
    title = _('People following you')

    def get_query(self):
        return self.user.get_profile().followers()

    def get_context_data(self, **kwargs):
        query = self.get_query()
        context = {}
        context['users'] = paginate(self.request, query, 20)
        context['viewing'] = self.user
        context['title'] = self.title

        context['klass'] = 'people'
        context['menu'] = generate_menu()
        return context

    def get(self, request, uid=None):
        self.user = self.request.user
        if uid:
            self.user = get_object_or_404(User, id=uid)
        return super(FollowersView, self).get(request)


class FollowingsView(FollowersView):
    template_name = 'truekko/userlist.html'
    title = _('People you follow')

    def get_query(self):
        return self.user.get_profile().followings()


class GroupMemberListView(FollowersView):
    template_name = 'truekko/userlist.html'

    def get_query(self):
        return self.group.members()

    def get_context_data(self, **kwargs):
        context = super(GroupMemberListView, self).get_context_data(**kwargs)
        context.update({'viewing': None})
        return context

    def get(self, request, gid):
        self.group = get_object_or_404(Group, id=gid)
        self.title = _(u'%(name)s members') % {'name': self.group.name}
        return super(GroupMemberListView, self).get(request)


###########
#         #
# CONTACT #
#         #
###########

class Contact(TemplateView):
    template_name = 'truekko/contact.html'
    help_text = ''
    help_text2 = ''
    subject = ''

    def get_context_data(self, **kwargs):
        context = super(Contact, self).get_context_data(**kwargs)
        context['menu'] = generate_menu()
        context['form'] = ContactForm()
        context['form'].fields['subject'].initial = self.subject
        context['help_text'] = self.help_text
        context['help_text2'] = self.help_text2

        return context

    def get(self, request):
        self.request = request

        return super(Contact, self).get(request)

    def post(self, request):
        self.request = request

        form = ContactForm(request.POST)
        if not form.is_valid():
            context = self.get_context_data()
            context = RequestContext(request, context)
            context['form'] = form
            return render_to_response(Contact.template_name, context)

        # Send email
        form.send()

        # notify
        messages.info(request, _(u"Thanks for contact with us, we will reply as soon as possible"))
        return redirect(index)


class NewCommunityContact(Contact):
    help_text = _("Fill the following form to register a new "
                  "community. We will contact you as soon as "
                  "possible. In the message you should put "
                  "a short description about your community.")
    subject = _("I want to create a new community in Etruekko")


class NewAdContact(Contact):
    help_text = _(\
u"Anunciarte en Etruekko es algo más que dar a conocer tu negocio "
u"publicitariamente, es apoyar una iniciativa basada en valores "
u"profundamente beneficiosos para la sociedad, es aportar tu granito de "
u"arena a la conservación medioambiental, es apoyar la comunidad en la "
u"que desarrollas tu actividad, es ser solidario y sobre todo es "
u"potenciar la Responsabilidad Social de tu negocio.")

    help_text2 = _("Fill the following form to advertise in "
                   "Etruekko. In the message you should put "
                   "a short description about what do you "
                   "want to ad in this platform. "
                   "We will contact you as soon as "
                   "possible to tell you more about "
                   "conditions and what we need")

    subject = _("I want add an advertise in Etruekko")


##############
# PLAIN TEXT #
##############

class PlainText(TemplateView):
    template_name = 'truekko/plain_text.html'
    filename = ''
    prefix = 'n'

    def get_context_data(self, **kwargs):
        context = super(PlainText, self).get_context_data(**kwargs)
        cur_language = translation.get_language()

        # looking for language file
        directory = os.path.join(settings.MEDIA_ROOT, "plaintext")
        default = os.path.join(directory, self.filename)
        langfile = "%s.%s" % (default, cur_language)

        if os.path.exists(langfile):
            path = langfile
        else:
            path = default

        context['text'] = open(path).read()
        context['prefix'] = self.prefix

        return context


class FAQ(PlainText):
    filename = "faq.txt"
    prefix = "faq"

class Privacy(PlainText):
    filename = "privacy.txt"
    prefix = "privacy"

class Terms(PlainText):
    filename = "terms.txt"
    prefix = "terms"


def validate_image(imfile):
    file = imfile.file
    try:
        trial_image = Image.open(file)
        trial_image.load()

        if hasattr(file, 'reset'):
            file.reset()

        trial_image = Image.open(file)
        trial_image.verify()
        return True
    except Exception:
        return False



# profile
edit_postal = login_required(EditPostal.as_view())
edit_profile = login_required(EditProfile.as_view())
edit_profile_admin = login_required(EditProfileAdmin.as_view())
view_profile = login_required(ViewProfile.as_view())
rate_user = login_required(RateUser.as_view())
people = People.as_view()

# friendship
follow = login_required(FollowView.as_view())
unfollow = login_required(UnFollowView.as_view())

followers = login_required(FollowersView.as_view())
followings = login_required(FollowingsView.as_view())

# channel
channel_view = login_required(ChannelView.as_view())

# group
groups = Groups.as_view()
group_member_list = GroupMemberListView.as_view()
view_group = ViewGroup.as_view()
edit_group = login_required(is_group_admin(EditGroup.as_view()))
edit_group_members = login_required(is_group_admin(EditGroupMembers.as_view()))
leave_group = login_required(LeaveGroup.as_view())
join_group = JoinGroup.as_view()
register_group_admin = login_required(is_group_admin(RegisterAdmin.as_view()))
register_group = Register.as_view()
register_confirm = RegisterConfirm.as_view()
# denounce
group_denounce = login_required(GroupDenounce.as_view())
group_denounce_user = login_required(GroupDenounceUser.as_view())
group_denounce_view = login_required(GroupDenounceView.as_view())

# transfer
transfer_direct = login_required(TransferDirect.as_view())
transfer_list = login_required(TransferList.as_view())

# swap
swap_creation = login_required(SwapCreation.as_view())
swap_view = login_required(SwapView.as_view())
swap_list = login_required(SwapList.as_view())

commitment_done = login_required(CommitmentDone.as_view())
commitment_create = login_required(CommitmentCreate.as_view())
commitment_delete = login_required(CommitmentDelete.as_view())

#item
item_add = login_required(ItemAdd.as_view())
item_view = ItemView.as_view()
item_list = ItemList.as_view()
item_remove = login_required(ItemRemove.as_view())

# messages
message_post = login_required(MessagePost.as_view())
message_remove = login_required(MessageRemove.as_view())

# register
register_wizard = RegisterWizard.as_view()
register_single = RegisterSingle.as_view()

# search
search_advanced = login_required(SearchAdvanced.as_view())

# etruekko
etruekko = login_required(Etruekko.as_view())

# contact
contact = Contact.as_view()
new_community_contact = NewCommunityContact.as_view()
new_ad_contact = NewAdContact.as_view()

# faq
faq = FAQ.as_view()
terms = Terms.as_view()
privacy = Privacy.as_view()

index = Index.as_view()
