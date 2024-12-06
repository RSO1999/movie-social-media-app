FROM python:3

WORKDIR /src

ENV TMDB_API_KEY=''
ENV DJANGO_SUPERUSER_USERNAME='admin'
ENV DJANGO_SUPERUSER_EMAIL='admin@team5.com'
ENV DJANGO_SUPERUSER_PASSWORD='admin'
ENV WATCHMODE_API_KEY=''

COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT ["./start-crossover.sh"]