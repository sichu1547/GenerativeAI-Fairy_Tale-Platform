# mysite/views.py

from django.shortcuts import render
from django.http import JsonResponse

def main_page(request):
    return render(request, 'index.html')

def search(request):
    query = request.GET.get('q', '')
    # 가짜 데이터로 검색 결과를 생성합니다
    if query:
        results = [{'title': 'Sample Story 1'}, {'title': 'Sample Story 2'}]  # 여기에 실제 검색 로직을 구현할 수 있습니다
    else:
        results = []

    return JsonResponse({'posts': results})
