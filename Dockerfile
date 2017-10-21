FROM debian:stable-slim
RUN apt-get update && apt-get install -y nginx python3 python3-pip
EXPOSE 8080
EXPOSE 3128
WORKDIR /usr/src/app
COPY kalamari/ ./
ENTRYPOINT ["python3", "./kalamari.py"]