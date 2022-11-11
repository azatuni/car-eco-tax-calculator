FROM python:alpine3.16
WORKDIR /opt/cartax-calulcator
COPY . ./
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3", "telegram_bot.py"]