from django.urls import reverse, resolve
from django.shortcuts import get_object_or_404, redirect
from django.utils.deprecation import MiddlewareMixin
from myaccount.models import Profile

class ProfileMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_paths = [
            reverse('select_account'),
            reverse('logout'),
        ]

        if request.user.is_authenticated:
            selected_profile_id = request.session.get('selected_profile_id')

            if selected_profile_id:
                try:
                    profile = get_object_or_404(Profile, id=selected_profile_id, user=request.user)
                    choose_profile_url = reverse('choose_profile', args=[profile.id])
                    allowed_paths.append(choose_profile_url)
                except Profile.DoesNotExist:
                    print('Profile does not exist')

            path_resolver = resolve(request.path)
            if path_resolver.url_name in ['edit_profile', 'profile_delete', 'profile', 'profile_detail'] or request.path in allowed_paths:
                pass
            elif not selected_profile_id:
                return redirect(reverse('select_account') + '?next=' + request.path)

        response = self.get_response(request)
        return response
