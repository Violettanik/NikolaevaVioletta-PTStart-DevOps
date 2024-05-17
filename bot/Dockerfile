FROM python:latest

WORKDIR /bot

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /bot

CMD ["python", "bot.py"]
