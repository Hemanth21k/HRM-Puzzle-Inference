FROM nginx:alpine

# Copy frontend files to nginx html directory
COPY index.html /usr/share/nginx/html/
COPY scripts.js /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]