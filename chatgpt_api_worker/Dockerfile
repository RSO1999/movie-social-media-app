FROM python:3

WORKDIR /src

ENV OPENAI_API_KEY=''
ENV TMDB_API_KEY=''

COPY . .
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["./start-api.sh"]