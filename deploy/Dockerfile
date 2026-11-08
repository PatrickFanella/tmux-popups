FROM nginxinc/nginx-unprivileged:stable-alpine
COPY site/index.html site/404.html site/style.css site/app.js site/robots.txt site/sitemap.xml /usr/share/nginx/html/
COPY site/docs/ /usr/share/nginx/html/docs/
COPY site/assets/ /usr/share/nginx/html/assets/
COPY site/fonts/ /usr/share/nginx/html/fonts/
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
