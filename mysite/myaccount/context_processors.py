from .models import Profile

def profile_name(request):
    context = {'profile_name': None, 'attendance_dates': []}
    if request.user.is_authenticated:
        profile_id = request.session.get('selected_profile_id')
        if profile_id:
            try:
                profile = Profile.objects.get(id=profile_id, user=request.user)
                context['profile_name'] = profile.name
                context['attendance_dates'] = profile.attendance_dates
            except Profile.DoesNotExist:
                print('Profie does not exist')
    return context
