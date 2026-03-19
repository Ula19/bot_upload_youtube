FROM python:3.12-slim

# ffmpeg для конвертации, wget+unzip для плагина POT и deno
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg wget unzip curl && \
    rm -rf /var/lib/apt/lists/*

# deno — JS-рантайм для yt-dlp (YouTube challenge + POT)
RUN curl -fsSL https://dl.deno.land/release/latest/download/deno-x86_64-unknown-linux-gnu.zip \
    -o /tmp/deno.zip && \
    unzip /tmp/deno.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/deno && \
    rm /tmp/deno.zip

WORKDIR /app

# сначала зависимости (кэшируется Docker слоем)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# плагин PO Token для yt-dlp (стандартный путь плагинов yt-dlp)
RUN mkdir -p /root/.config/yt-dlp/plugins/pot && \
    wget -qO /tmp/pot-plugin.zip \
    https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs/releases/latest/download/bgutil-ytdlp-pot-provider-rs.zip && \
    unzip -o /tmp/pot-plugin.zip -d /root/.config/yt-dlp/plugins/pot/ && \
    rm /tmp/pot-plugin.zip

# потом код
COPY bot/ bot/

CMD ["python", "-m", "bot.main"]
