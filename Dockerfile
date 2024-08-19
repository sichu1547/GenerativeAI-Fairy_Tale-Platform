FROM python:3.11.9

WORKDIR /app
# 이 문장은 작업 디렉토리를 '/usr/src/app'으로 설정합니다. 이 디렉토리는 이미지 내에서 모든 작업이 수행될 위치입니다.
# 쉽게는 manage.py를 가지고 있는 폴더의 위치라고 생각하면 됩니다.

# set envireonment variables -.pyc 파일을 생성하지 않도록 하고, 버퍼링없이 출력하게 함
ENV PYTHONDONTWRITEBYECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./mysite/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
# 이 문장은 Django를 이미지내에서 실행시키기 위해 pip으로 설치해야할 내용들을 설치하는 명령을 실행합니다. 
# requirements.txt에 적혀있는 pip들을 설치하게 됩니다.

COPY ./mysite /app

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "mysite.wsgi:application"]
# 이 문장은 컨테이너가 실행될 때 기본으로 실행할 명령을 지정합니다. WORKDIR에서 지정한 디렉터리에서 실행되는 문장입니다. 
# 만약 gunicorn을 사용한다면 CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"] 이 CMD를 사용합니다.

EXPOSE 8000
# django 서버의 포트를 8000으로 지정하였으므로 Docker의 컨테이너 또한 8000 포트를 열어줍니다.
# 참고로 장고의 기본 포트번호는 8000입니다.