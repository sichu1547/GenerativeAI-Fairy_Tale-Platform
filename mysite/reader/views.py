from django.shortcuts import render, get_object_or_404
from .models import *

# Create your views here.
def index(request):
    return render(request, 'reader/index.html')

def list(request):
    story_list = Story.objects.all()
    search_key = request.GET.get('keyword')
    if search_key :
        story_list = Story.objects.filter(title__contains=search_key)
    return render(request, 'reader/list.html', {'story_all': story_list})

def detail(request, id):
    story = get_object_or_404(Story, id=id)
    tag_list = story.tag.all()
    
    return render(request, 'blog/detail.html', {'post': story, 'tag_list': tag_list})