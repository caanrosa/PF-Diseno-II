FROM nginx:1.27-alpine
# Solo se sustituyen las variables FRONT_* (el resto de $ de nginx queda intacto)
ENV NGINX_ENVSUBST_FILTER=^FRONT_ \
    FRONT_AUTH_ENABLED=false \
    FRONT_OIDC_ISSUER=http://localhost:8081/realms/gestion \
    FRONT_OIDC_CLIENT=gestion-frontend \
    FRONT_N8N_URL=http://localhost:5678
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY index.html /usr/share/nginx/html/index.html
