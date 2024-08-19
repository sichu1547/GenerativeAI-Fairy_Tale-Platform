from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from .models import UserSessionData, Profile, ReadingHistory
from django.http import HttpResponse
from .forms import CustomUserCreationForm, ProfileForm
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator
from review.models import Review
from generator.models import GenStory
from reader.models import Story
from datetime import datetime
from django.contrib import messages 

def index(request):
    
    stories = Story.objects.all()
    len_story = stories.count()
    
    # 시작일과 종료일 설정
    start_date_str = '2023-06-17'
    end_date_str = '2023-07-30'

    # 문자열을 datetime 객체로 변환
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    # 두 날짜 사이의 시간 계산
    time_difference = end_date - start_date
    hours_difference = time_difference.total_seconds() / 3600

    time_count = hours_difference
    return render(request, 'index.html', {'len_story':len_story, 'time_count':time_count})

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session['user_email'] = user.email
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def custom_logout(request):
    if request.user.is_authenticated:
        user_session, created = UserSessionData.objects.get_or_create(user=request.user)
        user_session.session_data = dict(request.session)
        user_session.save()
    
    auth_logout(request)
    return redirect('login')

from django.http import HttpResponse

@login_required
def set_session_data(request):
    request.session['key'] = f"Value for user {request.user.username}"
    return HttpResponse(f"Session data set for user {request.user.username}")

@login_required
def get_session_data(request):
    value = request.session.get('key', 'No data found')
    return HttpResponse(f"Session data for user {request.user.username}: {value}")

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import login
from .forms import PasswordResetForm

def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user = User.objects.get(username=form.cleaned_data['username'], email=form.cleaned_data['email'])
            subject = "MealKid 비밀번호 재설정 요청"
            email_template_name = "password/password_reset_email.txt"
            c = {
                "email": user.email,
                "user" : user,
                'domain': request.get_host(),
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'protocol': 'https' if request.is_secure() else 'http',
            }
            email = render_to_string(email_template_name, c)
            send_mail(subject, email, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)
            return redirect("password_reset_done")
    else:
        form = PasswordResetForm()
    return render(request, "password/password_reset.html", {"form": form})

def password_reset_confirm(request, uidb64=None, token=None):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError):
        user = None
        print('Invalid Type')
    except (ValueError):
        user = None
        print('Invalid Value')
    except (OverflowError):
        user = None
        print('Overflow Error')
    except (User.DoesNotExist):
        user = None
        print('User does not exist')

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect('password_reset_complete')
        else:
            form = SetPasswordForm(user)
        return render(request, 'password/password_reset_confirm.html', {'form': form})
    else:
        return HttpResponse('비밀번호 재설정 링크가 유효하지 않습니다!')

def password_reset_done(request):
    return render(request, "password/password_reset_done.html")

def password_reset_complete(request):
    return render(request, 'password/password_reset_complete.html')

@login_required
def select_account(request):
    profiles = request.user.profiles.all()
    next_url = request.GET.get('next', request.POST.get('next', 'index'))

    if request.method == "POST":
        selected_profile_id = request.POST.get('profile_id')
        
        if selected_profile_id:
            profile = get_object_or_404(Profile, id=selected_profile_id, user=request.user)
            request.session['show_attendance_modal'] = True
            request.session['selected_profile_id'] = profile.id
            request.session['selected_profile_avatar'] = profile.avatar.url if profile.avatar else None
            request.session['selected_profile_name'] = profile.name
            
            return redirect(next_url)
        else:
            #messages.error(request, "프로필을 선택하세요.")
            return redirect('select_account')

    return render(request, 'registration/select_account.html', {'profiles': profiles, 'next': next_url})

@login_required
def profile(request):
    if request.method == 'POST':
        profile_id = request.POST.get('profile_id')
        
        if profile_id:  # 업데이트
            profile = get_object_or_404(Profile, id=profile_id, user=request.user)
            form = ProfileForm(request.POST, request.FILES, instance=profile)
        else:  # 생성
            if request.user.profiles.count() >= 4:
                messages.error(request, "최대 4개까지만 생성할 수 있습니다.")
                return redirect('profile')

            form = ProfileForm(request.POST, request.FILES)
        
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('profile')
    else:
        form = ProfileForm()
    profiles = request.user.profiles.all()
    return render(request, 'registration/profile.html', {'form': form, 'profiles': profiles})

def profile_detail(request, pk):
    profile = get_object_or_404(Profile, pk=pk, user=request.user)
    reading_histories = ReadingHistory.objects.filter(profile=profile).order_by('-read_at')
    reviews = Review.objects.filter(profile=profile).order_by('-created_at')
    gen_stories = GenStory.objects.filter(profile=profile).order_by('-id')
    
    paginator_stories = Paginator(gen_stories, 5)  # 페이지당 5개의 항목을 표시
    page_number_stories = request.GET.get('page_stories', 1)
    page_stories = paginator_stories.get_page(page_number_stories)
    
    paginator_histories = Paginator(reading_histories, 5)  # 페이지당 5개의 항목을 표시
    page_number_histories = request.GET.get('page_histories', 1)
    page_histories = paginator_histories.get_page(page_number_histories)

    paginator_reviews = Paginator(reviews, 5)  # 페이지당 5개의 항목을 표시
    page_number_reviews = request.GET.get('page_reviews', 1)
    page_reviews = paginator_reviews.get_page(page_number_reviews)
        
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_detail', pk=profile.pk)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'registration/profile_detail.html', {'form': form, 'profile': profile, 'page_histories': page_histories, 'page_reviews': page_reviews, 'page_stories' : page_stories})

@login_required
def choose_profile(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id, user=request.user)
    request.session['selected_profile_id'] = profile.id
    request.session['selected_profile_avatar'] = profile.avatar.url
    request.session['selected_profile_name'] = profile.name
    request.session['show_attendance_modal'] = True
    return redirect('index')

from .models import ReadingHistory
@login_required
def reading_history(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id, user=request.user)
    selected_profile_id = profile.id
    if selected_profile_id:
        reading_histories = ReadingHistory.objects.filter(user=request.user, profile_id=selected_profile_id)
    else:
        reading_histories = ReadingHistory.objects.filter(user=request.user)

    return render(request, 'registration/reading_history.html', {'reading_histories': reading_histories})

@login_required
def attendance_check(request):
    if request.method == 'POST':
        selected_profile_id = request.session.get('selected_profile_id')
        
        if not selected_profile_id:
            return JsonResponse({'status': 'fail', 'message': 'No profile selected'}, status=400)
        
        profile = get_object_or_404(Profile, id=selected_profile_id, user=request.user)
        date = timezone.now().date().isoformat()

        if date in profile.attendance_dates:
            return JsonResponse({'status': 'already_checked', 'message': '이미 출석이 완료되었습니다.'})
        else:
            profile.attendance_dates.append(date)
            profile.save()
            return JsonResponse({'status': 'ok', 'message': '오늘 출석이 완료되었습니다!'})
    else:
        return JsonResponse({'status': 'fail', 'message': 'Invalid request method'}, status=400)
    
from django.views.decorators.csrf import csrf_exempt

# @csrf_exempt
@login_required
def reset_show_attendance_modal(request):
    request.session['show_attendance_modal'] = False
    return JsonResponse({'status': 'ok'})

def edit_profile(request, pk):
    profile = get_object_or_404(Profile, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile', pk=profile.pk) 
    else:
        form = ProfileForm(instance=profile)
    return redirect('profile')

@login_required
def profile_delete(request, pk):
    profile = get_object_or_404(Profile, pk=pk, user=request.user)

    if request.method == 'POST':      
        profile.delete()  
        if request.session.get('selected_profile_id') == pk:
            del request.session['selected_profile_id']
            del request.session['selected_profile_avatar']
            del request.session['selected_profile_name']
    return redirect('profile')

def privacy_policy_view(request):
    return render(request, 'privacy_policy.html') 

def terms(request):
    return render(request, 'terms.html')

def check_username(request):
    username = request.GET.get('username', None)
    response = {
        'is_taken': User.objects.filter(username=username).exists()
    }
    return JsonResponse(response)

from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm

class CustomLoginView(LoginView):
    form_class = AuthenticationForm
    template_name = 'registration/login.html'

    def form_invalid(self, form):
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')

        # 사용자가 존재하는지 확인
        user = User.objects.filter(username=username).first()

        if user is None:
            form.add_error('username', '존재하지 않는 아이디 입니다.')
        else:
            # 사용자가 존재하면 비밀번호가 일치하는지 확인
            if not user.check_password(password):
                form.add_error('password', '비밀번호가 일치하지 않습니다.')
        
        return super().form_invalid(form)