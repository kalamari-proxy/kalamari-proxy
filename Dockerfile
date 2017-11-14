FROM debian:stable-slim
RUN apt-get update && apt-get install -y nginx python3 python3-pip
EXPOSE 8080
EXPOSE 3128
COPY configuration/nginx_config /etc/nginx/sites-available/default
COPY cached /var/www/cached
WORKDIR /usr/src/app
COPY src/ ./
CMD ["./entrypoint.sh"]
