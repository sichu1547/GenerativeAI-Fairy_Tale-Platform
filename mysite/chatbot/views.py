from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth import authenticate, get_user
from datetime import datetime

from langchain_community.chat_models import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document

from django.db.models import Min, Max
from .models import Chat
import json

# Embeddings 설정
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

# Database 설정
persist_directory = "./database"
database = Chroma(persist_directory=persist_directory,
                  embedding_function=embeddings)

# Create your views here.
@csrf_exempt
# @login_required
def chat_view(request):
    if request.method == 'GET' and 'reset' in request.GET:
        if request.user.is_authenticated:
            current_user = get_user(request)
            request.session.flush()  # Clear the session
            new_session = request.session = SessionStore()  # Create a new session
            request.session['chat_history'] = []
            request.session['_auth_user_id'] = current_user.id
            request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
            request.session['_auth_user_hash'] = current_user.get_session_auth_hash()
            new_session.save()
            return redirect(f"{request.path}?session_key={new_session.session_key}")
        else:
            request.session.flush()  # Clear the session for anonymous user
            # request.session = SessionStore()  # Create a new session
            # request.session['chat_history'] = []
            
            new_session = request.session = SessionStore()  # Create a new session
            new_session['chat_history'] = []
            new_session.save()
            return redirect(f"{request.path}?session_key={new_session.session_key}")

    selected_session_key = request.GET.get('session_key', request.session.session_key)
 
    if request.method == 'POST':
        question = request.POST.get('question')
        if question:
            # Handle the question and generate the result
            result = handle_chat(question, request, selected_session_key)
            # Append question and result to chat history
            request.session['chat_history'] = request.session.get(
                'chat_history', []) + [{'question': question, 'result': result}]
            request.session.modified = True
    
    chat_history = Chat.objects.filter(
        user=request.user,
        session=selected_session_key
    ).order_by('datetime')

    session_keys = Chat.objects.filter(user=request.user).values_list('session', flat=True).distinct()
    
    session_data = (
        Chat.objects.filter(user=request.user)
        .values('session')
        .annotate(last_question=Max('user_question'))
        .order_by('session')
    )

    return render(request, 'chatbot/chat.html', {
        'chat_history': chat_history,
        'user': request.user,
        'current_session_key': request.session.session_key,
        'selected_session_key': selected_session_key,
        'session_data': session_data,
    })

def chatbot_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question = data.get('question')

        # 챗봇 응답 생성
        response = handle_chat(question, request, request.session.session_key)
        return JsonResponse({'response': response})

def handle_chat(query, request, session_key):
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # chatgpt API 및 lang chain을 사용을 위한 선언
    chat = ChatOpenAI(model="gpt-3.5-turbo")
    k = 3
    retriever = database.as_retriever(search_kwargs={"k": k})

    memory = ConversationBufferMemory(
        memory_key="chat_history", input_key="question", output_key="answer", return_messages=True)

    qa = ConversationalRetrievalChain.from_llm(
        llm=chat, retriever=retriever, memory=memory, return_source_documents=True, output_key="answer")

    result = qa({"question": query})

    sim_db = database.similarity_search_with_score(query, k=k)

    # 대화 기록을 데이터베이스에 저장
    chat_record = Chat(
        datetime=time,
        user = request.user,
        session = session_key,
        user_question=query,
        chat_answer=result["answer"],
        sim1=sim_db[0][1],
        sim2=sim_db[1][1],
        sim3=sim_db[2][1]
    )
    chat_record.save()

    return result["answer"]
