FROM python:3.12-slim

# ffmpeg для конвертации, nodejs для yt-dlp, wget для загрузки бинарников
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg nodejs wget && \
    rm -rf /var/lib/apt/lists/*

# rustypipe-botguard — генерирует PO Token для YouTube (без браузера)
RUN wget -qO /usr/local/bin/rustypipe-botguard \
    https://github.com/nicholasgasior/rustypipe-botguard/releases/latest/download/rustypipe-botguard-x86_64-unknown-linux-gnu && \
    chmod +x /usr/local/bin/rustypipe-botguard

WORKDIR /app

# сначала зависимости (кэшируется Docker слоем)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# потом код
COPY bot/ bot/

CMD ["python", "-m", "bot.main"]
