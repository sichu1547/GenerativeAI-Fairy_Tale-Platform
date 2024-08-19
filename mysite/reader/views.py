from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from quiz.views import QuizView
import re
from django.db.models import Q
from django.http import HttpResponse
import io
import sqlite3
import requests
from django.conf import settings
from django.core.files.base import ContentFile

from django.contrib.auth.decorators import login_required
from django.views import View
from myaccount.models import Profile
from myaccount.models import ReadingHistory
from django.utils.decorators import method_decorator
from .utils import *
    
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Story, LogEntry
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
import os
from django.http import HttpResponseRedirect
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from .models import Story
from myaccount.models import ReadingHistory, Profile
import random
from generator.models import GenStory
import mysql.connector

def list(request):
    story_list = Story.objects.all()
    search_key = request.GET.get('keyword')
    if search_key :
        story_list = Story.objects.filter(title__contains=search_key)
        
    # 가장 많이 읽은 동화의 장르 가져오기
    stories = Story.objects.all()
    data = {
        '제목': [i.title for i in stories],
        '내용': [i.body for i in stories],
        '장르': [i.category for i in stories],
        '본 횟수':[i.starcount for i in stories]
    }
    # 제목과 내용을 새로운 데이터프레임으로 저장
    df = pd.DataFrame(data)
    max_tale = df['본 횟수'].groupby(df['장르']).sum()
    max_tale = max_tale.sort_values(ascending=False).index[0]
    # max_tale = df['장르'].value_counts().index[0]
    text = f'가장 많이 읽은 동화 카테고리는 {max_tale}입니다.'
    return render(request, 'reader/index.html', {'story_all': story_list, 'text':text})

def search(request):
    keyword = request.GET.get('keyword', '')
    
    if keyword:
        if keyword == 'Generative':
            stories = GenStory.objects.all()
        else:
            stories = Story.objects.filter(Q(title__icontains=keyword) | Q(category__icontains=keyword))
    else:
        stories = Story.objects.all()

    option = request.GET.get('options', 'high-rating')
    
    # 옵션에 따른 정렬
    if option == 'high-rating':
        stories = stories.order_by('-starpoint')
    elif option == 'low-rating':
        stories = stories.order_by('starpoint')
    elif option == 'name':
        stories = stories.order_by('title')
    elif option == 'random':
        stories = stories.order_by('?')
        
    # 검색 결과가 없는 경우를 확인
    no_results = len(stories) == 0

    return render(request, 'reader/search_results.html', {'stories': stories, 'keyword': keyword, 'selected_option': option, 'no_results': no_results})

def story_detail(request, id):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    keyword = request.GET.get('keyword')

    story = get_object_or_404(Story, id=id)
    profile_id = request.session.get('selected_profile_id')
    profile = None
    if profile_id:
        try:
            profile = get_object_or_404(Profile, id=profile_id, user=request.user)
            ReadingHistory.objects.get_or_create(user=request.user, profile=profile, story_title=story.title, story_id=story.id)
            print("Reading history saved successfully")
        except Exception as e:
            print(f"Error saving reading history: {e}")
    else:
        print("Profile ID not found in session")

    patterns = r'\r\n\r\n\r\n|\r\n\r\n \r\n|\r\n \r\n \r\n|\r\n \r\n\r\n'
    sentences = re.split(patterns, story.body)
    
    # 이미지 썸네일 가져오기
    image_urls = [story.image.url] if story.image else []
    request.session['image_urls'] = image_urls

    # TTS
    if 'tts' in request.GET:
        print("Here's Story TTS")
        print(request.GET)
        print(story.title)
        text = request.GET.get('text', '')

        if text == 'full':
            text = story.title+'<break time="1s"/>'+story.body
        
        ssml_text = f"""<speak>{text}</speak>"""

        return generate_tts(request, ssml_text)

    previous_story_id = request.session.get('previous_story_id')

    if previous_story_id != id:
        QuizView.m_context = {}
        conn = mysql.connector.connect(
            host = settings.DB_HOST,
            user = settings.DB_USER,
            password = settings.DB_PASSWORD,
            database = settings.DB_NAME
        )   
        cursor = conn.cursor()
        cursor.execute('DELETE FROM quiz_history')
        conn.commit()
        conn.close()    
        request.session['previous_story_id'] = id
        
    ########################################################################################################    
    # 장고 모델에서 모든 스토리 데이터 로드
    
    story = get_object_or_404(Story, id=id)
    
    stories = Story.objects.all()
    data = {
        '제목': [i.title for i in stories],
        '내용': [i.body for i in stories]
    }
    # 제목과 내용을 새로운 데이터프레임으로 저장
    df = pd.DataFrame(data)
    
    len_story = len(df)

    # 모델에서 id가 해당 동화인 데이터 가져오기
    # 제목만 따로 저장하기
    tale_title = story.title

    if not tale_title:
        return HttpResponse("Please provide a tale title.")  # 제목이 없으면 메시지 반환

    tfidf = TfidfVectorizer()
    dtm = tfidf.fit_transform(df['내용'])
    dtm = pd.DataFrame(dtm.todense(), columns=tfidf.get_feature_names_out())

    nn = NearestNeighbors(n_neighbors=6, algorithm='kd_tree')
    nn.fit(dtm)

    try:
        idx = df[df['제목'] == tale_title].index[0]
    except IndexError:
        return HttpResponse("Tale title not found.")  # 제목이 데이터베이스에 없으면 메시지 반환

    result = nn.kneighbors([dtm.iloc[idx]])
    random_value = random.randint(1,5)
    recommended_title = df['제목'].iloc[result[1][0][random_value]]
    story = Story.objects.filter(title=recommended_title).first()
    recommended_id = story.id

    return render(request, 'reader/story_detail.html', {'story': sentences, 'keyword': keyword, 'title': tale_title, 'id': id, 'image_urls': image_urls, 'rec_title':recommended_title, 'rec_id':recommended_id, 'profile' : profile, 'len_story' : len_story})
    ########################################################################################################    

def redirect_to_quiz(request, id):
    keyword = request.GET.get('keyword')

    return redirect(f"{reverse('quiz:quiz_view', args=[id])}?keyword={keyword}")

from django.http import JsonResponse

def generate_image_view(request):
    sentence = request.GET.get('sentence')
    if sentence:
        image_url = generate_image(sentence)
        return JsonResponse({'image_url': image_url})
    return JsonResponse({'error': 'No sentence provided'}, status=400)


############################ 읽기 챗봇 ############################
# Initialize the chat model
chat = ChatOpenAI(model="gpt-4o")

# Initialize the memory with the correct keys
memory = ConversationBufferMemory(memory_key="history", input_key="input", output_key="response", return_messages=True)

# Create the conversation chain
qa = ConversationChain(llm=chat, memory=memory)

# @csrf_exempt
def answer_question(request, story_id):
    if request.method == 'POST':
        profile_id = request.POST.get('profile_id')
        question = request.POST.get('question', None)
        profile = get_object_or_404(Profile, id=profile_id, user=request.user)

        if question and story_id:
            if request.POST.get('keyword') == 'Generative':
                story = get_object_or_404(GenStory, pk=story_id)
            else:
                story = get_object_or_404(Story, pk=story_id)

            role = "당신은 어린아이의 질문에 친절하게 답변해주는 캐릭터 '밀키'입니다."
            full_query = (
                f"{role} "
                f"질문: '{question}'은 동화 '{story.title}'에 대한 질문입니다. "
                f"동화 내용: '{story.body}' "
                f"어린아이가 잘 이해할 수 있도록 200글자 이하로만 답변하세요. "
                f"어려운 단어를 사용하지 말고 아이들의 수준에 맞춰 답변하세요. "
                f"참고: 질문으로 인사가 들어올때는 동화 내용 없이 인사로만 답변하세요. "
                f"단어 의미를 물어볼 때는 동화 내용 없이 단어의 의미만 답변하세요. "
                f"동화 내용에 대한 답변을 해줄 때 맨 앞에 인사를 붙이지 마세요."
                f"동화 내용을 요약 해달라는 요구가 없으면 답변에 동화 내용 요약을 붙이지 마세요. "
                f"존댓말과 반말을 섞어서 사용하지말고 통일해서 답변하세요. "
                f"물어본 내용에 대해서만 답변하세요. 임의로 답변을 추가하지마세요. "
                f"질문이 이상하다면 무슨 말인지 모르겠으니 다시 물어봐달라고 말하세요."
                f"프롬프트 내용을 답변에 포함하지 마세요. "
            )

            memory_content = memory.load_memory_variables({})

            # Perform the query
            result = qa.invoke({"input": full_query, "history": memory_content["history"]})

            # Output the answer obtained from LangChain
            answer = result["response"]

            # Save to memory
            memory.save_context({"input": full_query}, {"response": answer})

            # Save to the database
            save_to_database(story.title, question, answer, profile_id, profile.name, request.user)  # request.user 전달

            # Answer TTS
            ssml_text = f"""<speak>{answer}</speak>"""
            tts_response = generate_tts(request, ssml_text)

            if tts_response.status_code == 200:
                audio_content = tts_response.content.decode('latin1')
                return JsonResponse({
                    'answer': answer,
                    'audio_content': audio_content
                })
            else:
                return JsonResponse({'answer': answer, 'error': 'TTS 생성 실패'})

    return JsonResponse({'error': 'Invalid request'})

def save_to_database(story_title, question, answer, profile_id, profile_name, user):
    try:
        log_entry = LogEntry.objects.create(
            user=user,  # 현재 요청 사용자
            profile_id=profile_id,
            profile_name=profile_name,
            story_title=story_title,
            question=question,
            answer=answer
        )
        log_entry.save()
    except Exception as e:
        print(f"Error saving to database: {e}")
        
def rate_story(request, id):
    keyword = request.GET.get('keyword')

    if keyword == 'Generative':
        story = get_object_or_404(GenStory, id=id)   
    else:
        story = get_object_or_404(Story, id=id)

    if request.method == 'POST':
        starpoint = request.POST.get('starpoint')
        if starpoint:
            try:
                starpoint = int(starpoint)
                if 1 <= starpoint <= 5:
                    story.starcount += 1
                    story.starsum += starpoint
                    story.starpoint = story.starsum / story.starcount
                    story.save()
                    return HttpResponse(status=204)
            except ValueError:
                print('wrong value of point')
    if keyword:
        return HttpResponseRedirect(reverse('reader:search') + f'?keyword={keyword}')
    else:
        return HttpResponseRedirect(reverse('reader:search'))
    
        
def genstory_detail(request, story_id):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    story = get_object_or_404(GenStory, id=story_id)   
    patterns = r'\r\n\r\n\r\n|\r\n \r\n \r\n'
    sentences = re.split(patterns, story.body)
    keyword = request.GET.get('keyword')
    profile_id = request.session.get('selected_profile_id')
    
    if profile_id:
        profile = get_object_or_404(Profile, id=profile_id, user=request.user)
 
    # TTS
    if 'tts' in request.GET:
        print("Here's GenStory TTS")
        text = request.GET.get('text', '')

        if text == 'full':
            text = story.title+'<break time="1s"/>'+story.body
            
        ssml_text = f"""<speak>{text}</speak>"""

        return generate_tts(request, ssml_text)
    if profile_id:
        return render(request, 'reader/genstory_detail.html', {'story': sentences, 'id' : story_id, 'keyword': keyword, 'title' : story.title, 'profile' : profile})
    else:
        return render(request, 'reader/genstory_detail.html', {'story': sentences, 'id' : story_id, 'keyword': keyword, 'title' : story.title})


import json

def update_image_session(request):
    if request.method == "POST":
        image_urls = json.loads(request.POST.get('image_urls', '[]'))
        image_urls = [url for url in image_urls if url is not None]
        print(image_urls)
        request.session['image_urls'] = image_urls
     
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)

def get_image_session(request):
    image_urls = request.session.get('image_urls', [])

    return JsonResponse({'image_urls': image_urls})