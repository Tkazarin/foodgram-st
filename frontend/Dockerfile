FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
RUN mkdir -p /usr/share/nginx/html && cp -a build/. /usr/share/nginx/html/
CMD ["sh", "-c", "echo 'Frontend built!' && tail -f /dev/null"]