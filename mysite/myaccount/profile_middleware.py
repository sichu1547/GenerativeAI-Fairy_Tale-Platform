from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from myaccount.models import Profile

class ProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_paths = [
            reverse('select_account'),
            reverse('profile'),
            reverse('logout')
        ]

        if request.user.is_authenticated:
            selected_profile_id = request.session.get('selected_profile_id')

            if selected_profile_id:
                try:
                    profile = get_object_or_404(Profile, id=selected_profile_id, user=request.user)
                    choose_profile_url = reverse('choose_profile', args=[profile.id])
                    allowed_paths.append(choose_profile_url)
                except Profile.DoesNotExist:
                    pass
            
            if not selected_profile_id and request.path not in allowed_paths:
                return redirect(reverse('select_account') + '?next=' + request.path)

        response = self.get_response(request)
        return response
