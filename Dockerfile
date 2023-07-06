FROM python:3.8

COPY requirements.txt /server_env/

RUN pip3 install --upgrade pip
RUN pip3 install -r /server_env/requirements.txt
RUN apt-get update && apt-get install -y netcat

COPY *.py start_server.sh /server/
WORKDIR /server

RUN chmod +x start_server.sh
EXPOSE 5000

CMD ["./start_server.sh"]
