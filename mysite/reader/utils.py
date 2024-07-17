import io
from django.http import HttpResponse
from google.cloud import texttospeech
from django.conf import settings
from openai import OpenAI

def generate_image(sentence):
    print('생성중')
    api_key = settings.OPENAI_API_KEY
    client = OpenAI(api_key = api_key)
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Here is the text of a fairy tale: {sentence}. Create a friendly and cute fairy tale scene image based on this sentence. There are no letters, symbols, or any kind of text in the image. Design this scene to look inviting and welcoming to children with a cute and joyful atmosphere. The image must come out as one scene in one image.",
            #prompt=f"Here is the text of a fairy tale: {sentence}. Based on this text, create an illustration for the story. Draw in a hand-drawn style with soft colors, simplified shapes.",
            size="1024x1024",
            n=1,
            quality="standard",
            style="vivid"
        )
        image_url = response.data[0].url
        print('성공')
        return image_url

    except Exception as e:
        print('실패', e)
    return ""

def generate_tts(request, ssml_text):
    try:
        # Google TTS 클라이언트 설정
        client = texttospeech.TextToSpeechClient.from_service_account_json('service_account.json')
        
        # 선택된 목소리 가져오기
        selected_voice = request.GET.get('voice', 'ko-KR-Standard-A')

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