from django.utils.deprecation import MiddlewareMixin
from .models import UserSessionData  # account.models에서 UserSessionData 임포트

class UserSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            # 사용자 아이디와 인덱스를 세션 데이터에 추가
            user_session, created = UserSessionData.objects.get_or_create(user=request.user)
            # 세션 데이터 불러오기
            session_data = user_session.session_data
            session_data['user_id'] = request.user.id
            session_data['session_index'] = user_session.id
            request.session.update(session_data)
    
    def process_response(self, request, response):
        if request.user.is_authenticated:
            user_session, created = UserSessionData.objects.get_or_create(user=request.user)
            # 현재 세션 데이터를 저장
            session_data = dict(request.session)
            session_data['user_id'] = request.user.id
            session_data['session_index'] = user_session.id
            user_session.session_data = session_data
            user_session.save()
        return response
