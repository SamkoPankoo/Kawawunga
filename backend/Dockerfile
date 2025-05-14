# backend/Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

# Inštalovať netcat pre čakanie na port
RUN apk add --no-cache netcat-openbsd

RUN npm install

# Skopírovať wait-for-it.sh
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

COPY . .

EXPOSE 3000

# Použiť wait-for-it.sh ako entrypoint
ENTRYPOINT ["/wait-for-it.sh"]
CMD ["npm", "run", "dev"]