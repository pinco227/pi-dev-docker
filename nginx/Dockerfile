FROM nginx:1.19.6-alpine

LABEL MAINTAINER="Paul Istratoaie <p4ul.gg@gmail.com>"

RUN mkdir /etc/nginx/templates
COPY conf.d/app.conf.template /etc/nginx/templates

RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]