FROM nginx:1.27.4-perl as deploy

WORKDIR /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY dist/ ./
EXPOSE 80

