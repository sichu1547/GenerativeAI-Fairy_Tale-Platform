from django.shortcuts import render
from django.views import View
from .models import ReaderStory
from konlpy.tag import Okt
import random
import re
#import pdb
class QuizView(View):
    m_context = {}
    
    def __init__(self):       
        self.pronouns = [
            '나', '너', '그', '그녀', '우리', '너희', '그들',
            '나를', '너를', '그를', '그녀를', '우리를', '너희를', '그들을',
            '나의', '너의', '그의', '그녀의', '우리의', '너희의', '그들의',
            '나 자신', '너 자신', '그 자신', '그녀 자신', '우리 자신', '너희 자신', '그들 자신'
        ]
        self.korean_adverbs = [
            '매우', '아주', '몹시', '너무', '정말', '참', '진짜', '거의', '대부분', '항상', '자주', '가끔',
            '종종', '별로', '전혀', '결코', '절대로', '특히', '더욱', '더', '덜', '그나마', '다행히', '당장',
            '곧', '금방', '이미', '벌써', '지금', '이제', '방금', '마침', '결국', '드디어', '끝내', '점점',
            '차츰', '천천히', '갑자기', '문득', '가만히', '고요히', '살짝', '서서히', '조금', '한참', '꽤',
            '아예', '일찍', '늦게', '나중에', '미리', '빠르게', '느리게', '온전히', '가득', '다소', '대체로',
            '전부', '모두', '전혀', '적극적으로', '부지런히', '게으르게', '성실히', '거의', '항상', '계속',
            '잠시', '이따가', '모처럼', '결코', '종일', '불과', '방금', '끝내', '간신히', '차라리', '오히려',
            '함께', '따로', '다시', '새로', '확실히', '마구', '꼭', '절대', '제발', '별로', '약간', '대충',
            '충분히', '가령', '비교적', '무척', '진정', '과연', '혹시', '어쩌면', '마치', '따라서', '또는',
            '그리고', '그렇지만', '그러나', '그래서', '그러므로', '게다가', '그런데', '하지만', '따라서',
            '더구나', '즉', '이른바', '곧', '이내', '역시', '바로', '일단', '종종', '우선', '결국', '다시',
            '계속', '당연히', '절대로', '결코', '과연', '오히려', '마치', '하필', '함부로', '저절로', '따로',
            '대신', '똑같이', '비록', '심지어', '잦다', '즉시', '천천히', '대개', '아마도', '상당히', '과감히'
        ]
        self.pronoun_pattern = re.compile('|'.join(self.pronouns))
        self.adverbs_pattern = re.compile('|'.join(self.korean_adverbs))
    def get(self, request):
        if 'quizzes' in QuizView.m_context:
            return render(request, 'quiz/quiz.html', QuizView.m_context)
        else:    
            story = ReaderStory.objects.first()
            if not story:
                return render(request, 'quiz/no_story.html') 
            paragraphs = story.body.split('\n\n')  # 문단으로 분리
            quizze = [self.create_quiz_sentence(p) for p in paragraphs]
        
            for story, _, _ in quizze:
                quizzes = story.split('\r\n\r\n')   
            answer = quizze[0][1]      
            example = quizze[0][2]  
            context = {'quizzes': quizzes, 'answer' : answer, 'example' : example}
            QuizView.m_context = context
            #pdb.set_trace()
            return render(request, 'quiz/quiz.html', context)

    def post(self, request):
        answer = request.POST.get('answer')
        correct_answer = request.POST.get('correct_answer')

        if answer == correct_answer:
            result = "정답입니다!"
            QuizView.m_context = {}
        else:
            result = f"틀렸습니다. 정답은 {correct_answer}입니다."           

        return render(request, 'quiz/quiz_result.html', {'result': result})

    def extract_nouns(self, sentence):
        okt = Okt()
        nouns = okt.pos(sentence)
        filtered_nouns = [word for word, pos in nouns if pos in ['Noun'] and not self.is_valid_noun(word) and len(word) > 1]
        #pdb.set_trace()
        return filtered_nouns
    
    def is_valid_noun(self, word):
        return bool(self.pronoun_pattern.match(word) or self.adverbs_pattern.match(word))
    
    def create_quiz_sentence(self, paragraph):
        nouns = self.extract_nouns(paragraph)
        if not nouns:
            return paragraph, None, []
        chosen_noun = random.choice(nouns)
        other_nouns = list(set([n for n in nouns if n != chosen_noun]))
        other_nouns = random.sample(other_nouns, min(2, len(other_nouns)))
        quiz_sentence = paragraph.replace(chosen_noun, "____", 1)
        choices = [chosen_noun] + other_nouns
        random.shuffle(choices)
        return quiz_sentence, chosen_noun, choices

