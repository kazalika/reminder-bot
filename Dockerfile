FROM python:3.10.4-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

CMD [ "python3", "bot.py" ]
