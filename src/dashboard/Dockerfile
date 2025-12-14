FROM node:20.15

WORKDIR /usr/src/app/
USER root
COPY . .
RUN export NODE_OPTIONS=--openssl-legacy-provider && yarn --network-timeout 600000 && yarn run build

FROM nginx:1.15.12
COPY --from=0 /usr/src/app/dist /usr/share/nginx/html
COPY cello.conf /etc/nginx/conf.d/

EXPOSE 8081

CMD ["bash", "-c", "nginx -g 'daemon off;'"]
