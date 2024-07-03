from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from quiz.views import QuizView
import re
from django.db.models import Q

def index(request):
    return render(request, 'reader/index.html')
def search(request):
    keyword = request.GET.get('keyword')
    search_type = request.GET.get('search_type', 'title')
    if keyword:
        if search_type == 'title':
            stories = Story.objects.filter(title__icontains=keyword)
        else:
            stories = Story.objects.filter(category__icontains=keyword)
    else:
        stories = Story.objects.all()      
         
    return render(request, 'reader/search_results.html', {'stories': stories, 'keyword': keyword})
def list(request):
    story_list = Story.objects.all()
    search_key = request.GET.get('keyword')
    if search_key :
        story_list = Story.objects.filter(title__contains=search_key)
    return render(request, 'reader/index.html', {'story_all': story_list})

def detail(request, id):
    story = get_object_or_404(Story, id=id)
    tag_list = story.tag.all()
    
    return render(request, 'reader/detail.html', {'story': story, 'tag_list': tag_list})

def search(request):
    keyword = request.GET.get('keyword')

    if keyword:
        # if search_type == 'title':
        #     stories = Story.objects.filter(title__icontains=keyword)
        # else:
        #     stories = Story.objects.filter(category__icontains=keyword)
        stories = Story.objects.filter(Q(title__icontains=keyword) | Q(category__icontains=keyword))
    else:
        stories = Story.objects.all()      

    return render(request, 'reader/search_results.html', {'stories': stories, 'keyword': keyword})

def story_detail(request, id):
    story = get_object_or_404(Story, id=id)
    keyword = request.GET.get('keyword')
    paragraphs = story.body.split('\n\n') 
    sentences = []
    for paragraph in paragraphs:
        sentences.extend(re.split(r'(?<=\.) ', paragraph))
    QuizView.m_context = {}
    return render(request, 'reader/story_detail.html', {'story': sentences, 'keyword': keyword, 'title': story.title, 'id': id})

def redirect_to_quiz(request, id):
    keyword = request.GET.get('keyword')

    return redirect(f"{reverse('quiz:quiz_view', args=[id])}?keyword={keyword}")