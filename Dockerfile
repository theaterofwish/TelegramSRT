FROM python:3.9

WORKDIR /app

COPY requirements.txt .
COPY Dockerfile .
COPY bot.py .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg


CMD ["python", "bot.py"]
