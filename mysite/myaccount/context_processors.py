from .models import Profile

def profile_name(request):
    if request.user.is_authenticated:
        profile_id = request.session.get('selected_profile_id')
        if profile_id:
            try:
                profile = Profile.objects.get(id=profile_id, user=request.user)
                return {'profile_name': profile.name}
            except Profile.DoesNotExist:
                pass
    return {'profile_name': None}
