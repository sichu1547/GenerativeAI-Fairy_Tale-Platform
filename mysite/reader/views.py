from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from quiz.views import QuizView
import re
from django.db.models import Q
from django.http import HttpResponse
from google.cloud import texttospeech
import io
import sqlite3
from openai import OpenAI
import requests
from django.conf import settings
from django.core.files.base import ContentFile

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
    print('======================================')
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

def generate_image(sentence):
    api_key = settings.OPENAI_API_KEY_FOR_IMAGE_GEN
    client = OpenAI(api_key = api_key)
    print(api_key)
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"다음은 동화 내용이야: {sentence}. 이 내용을 기반으로 그림을 그려줘. 귀여운 그림체로 부드러운 색조와 간단한 형태를 사용해 그려줘.",
            #prompt=f"Here is the text of a fairy tale: {sentence}. Based on this text, create an illustration for the story. Draw in a hand-drawn style with soft colors, simplified shapes.",
            size="1024x1024",
            n=1,
            quality="standard",
            style="natural"
        )
        image_url = response.data[0].url
        return image_url

    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)

def story_detail(request, id):
    
    story = get_object_or_404(Story, id=id)
    keyword = request.GET.get('keyword')
    paragraphs = story.body.split('\n\n') 
    sentences = []
    for paragraph in paragraphs:
        sentences.extend(re.split(r'(?<=\.) ', paragraph))
    
    # 이미지
    image_urls = [generate_image(sentence) for sentence in sentences]

    if 'tts' in request.GET:
        try:
            # Google TTS 클라이언트 설정
            client = texttospeech.TextToSpeechClient.from_service_account_json('service_account.json')

            # 선택된 목소리 가져오기
            selected_voice = request.GET.get('voice', 'ko-KR-Standard-A')
            text = request.GET.get('text', '')
            if text == 'full':
                text = story.title+'<break time="1s"/>'+story.body

            ssml_text = f"""<speak>{text}</speak>"""
            # ssml_text = f"""<speak>{story.title+'<break time="1s"/>'+story.body}</speak>"""

            # TTS 요청 설정
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
            voice = texttospeech.VoiceSelectionParams(language_code="ko-KR", name=selected_voice, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

            # TTS 요청 실행
            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

            # 음성 데이터를 메모리에 저장
            audio_stream = io.BytesIO(response.audio_content)

            # 음성 데이터를 HTTP 응답으로 반환
            return HttpResponse(audio_stream.getvalue(), content_type='audio/mpeg')
        except Exception as e:
            return HttpResponse(f"Error: {e}", status=500)

    previous_story_id = request.session.get('previous_story_id')

    if previous_story_id != id:
        QuizView.m_context = {}
        path = './database/quiz_history.db'
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM history')
        conn.commit()
        conn.close()    
        request.session['previous_story_id'] = id

    return render(request, 'reader/story_detail.html', {'story': sentences, 'keyword': keyword, 'title': story.title, 'id': id, 'image_urls': image_urls})
    #return render(request, 'reader/story_detail.html', {'story': sentences, 'keyword': keyword, 'title': story.title, 'id': id})

def redirect_to_quiz(request, id):
    keyword = request.GET.get('keyword')

    return redirect(f"{reverse('quiz:quiz_view', args=[id])}?keyword={keyword}")