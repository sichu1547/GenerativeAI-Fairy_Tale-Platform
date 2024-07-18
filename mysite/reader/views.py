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
from langchain_openai import OpenAIEmbeddings
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

# def search(request):
#     keyword = request.GET.get('keyword')
#     search_type = request.GET.get('search_type', 'title')
#     if keyword:
#         if search_type == 'title':
#             stories = Story.objects.filter(title__icontains=keyword)
#         else:
#             stories = Story.objects.filter(category__icontains=keyword)
#     else:
#         stories = Story.objects.all() 
#    # 정수형 필드에 대해 정렬 적용
#     stories = stories.order_by('starpoint')
        
#     return render(request, 'reader/search_results.html', {'stories': stories, 'keyword': keyword})

def list(request):
    story_list = Story.objects.all()
    search_key = request.GET.get('keyword')
    if search_key :
        story_list = Story.objects.filter(title__contains=search_key)
    return render(request, 'reader/index.html', {'story_all': story_list})

def search(request):
    keyword = request.GET.get('keyword')
    if keyword:
        if keyword == 'Generative':
            stories = GenStory.objects.all()
        else:
            stories = Story.objects.filter(Q(title__icontains=keyword) | Q(category__icontains=keyword))
    else:
        stories = Story.objects.all()      
    stories = stories.order_by('-starpoint')

    return render(request, 'reader/search_results.html', {'stories': stories, 'keyword': keyword})

def story_detail(request, id):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    keyword = request.GET.get('keyword')

    if keyword == 'Generative':
        story = get_object_or_404(GenStory, id=id)        
        patterns = r'\r\n\r\n|\r\n \r\n'
        sentences = re.split(patterns, story.body)     

        return render(request, 'reader/genstory_detail.html', {'story': sentences, 'id' : id, 'keyword': keyword, 'title' : story.title})
    else:
        story = get_object_or_404(Story, id=id)
        profile_id = request.session.get('selected_profile_id')

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
            print("Let's go TTS")
            text = request.GET.get('text', '')

            if text == 'full':
                text = story.title+'<break time="1s"/>'+story.body
            
            ssml_text = f"""<speak>{text}</speak>"""

            return generate_tts(request, ssml_text)

        previous_story_id = request.session.get('previous_story_id')

        if previous_story_id != id:
            QuizView.m_context = {}
            path = './db.sqlite3'
            conn = sqlite3.connect(path)
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

        return render(request, 'reader/story_detail.html', {'story': sentences, 'keyword': keyword, 'title': tale_title, 'id': id, 'image_urls': image_urls, 'rec_title':recommended_title, 'rec_id':recommended_id, 'profile' : profile})
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
# Initialize OpenAI embeddings, Chroma database, and ChatOpenAI model
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
persist_directory = os.path.join(settings.BASE_DIR, 'database')
database = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

chat = ChatOpenAI(model="gpt-4o")
retriever = database.as_retriever(search_kwargs={"k": 1})

memory = ConversationBufferMemory(memory_key="chat_history", input_key="question", output_key="answer", return_messages=True)

qa = ConversationalRetrievalChain.from_llm(
    llm=chat, retriever=retriever, memory=memory, 
    return_source_documents=True, output_key="answer")

@csrf_exempt
def answer_question(request, story_id):
    if request.method == 'POST':
        profile_id = request.POST.get('profile_id')
        question = request.POST.get('question', None)
        profile = get_object_or_404(Profile, id=profile_id, user=request.user)

        if question and story_id:
            story = get_object_or_404(Story, pk=story_id)

            role = "당신은 어린아이의 질문에 친절하게 답변해주는 선생님입니다."
            temp = story.body.split('.')
            sentences = '. '.join(temp[:1]) + '.'
            full_query = f"{role} '{sentences}'로 시작하는 동화 '{story}'에 대한 질문은 다음과 같습니다. 어린아이가 잘 이해할 수 있도록 250자 이하로 대답해주세요.\n{question}"
        
            memory_content = memory.load_memory_variables({})

            # Perform the query
            result = qa.invoke({"question": full_query, "chat_history": memory_content["chat_history"]})
            print(result)

            # Output the answer obtained from LangChain
            answer = result["answer"]
            if result['source_documents'] != []:
                src_doc = result['source_documents'][0].page_content.split('\n')[0]
            else:
                src_doc = 'Got No Source Document'
            # print('Question:', question)
            # print('Answer:', answer)
            print('Source Document:', src_doc)

            # Save to memory
            memory.save_context({"question": full_query}, {"answer": answer})

            # Save to the database
            save_to_database(story.title, question, answer, profile_id, request.user)

            # Answer TTS
            ssml_text = f"""<speak>{answer}</speak>"""
            tts_response = generate_tts(request, ssml_text)

            if tts_response.status_code == 200:
                audio_content = tts_response.content.decode('latin1')
                return JsonResponse({
                    'answer': answer,
                    'audio_content': audio_content  # Binary data를 문자열로 인코딩
                })
            else:
                return JsonResponse({'answer': answer, 'error': 'TTS 생성 실패'})

            # print(memory.load_memory_variables({})["chat_history"])

    return JsonResponse({'error': 'Invalid request'})

def save_to_database(story_title, question, answer, profile_id, user):
    try:
        log_entry = LogEntry.objects.create(
            profile_id=profile_id,
            story_title=story_title,
            question=question,
            answer=answer,
            user = user
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
                #return HttpResponse(status=200)
            except ValueError:
                pass
    if keyword:
        return HttpResponseRedirect(reverse('reader:search') + f'?keyword={keyword}')
    else:
        return HttpResponseRedirect(reverse('reader:search'))
        
def genstory_detail(request, story_id):
    story = get_object_or_404(GenStory, id=story_id)
    return render(request, 'reader/genstory_detail.html', {'story': story})