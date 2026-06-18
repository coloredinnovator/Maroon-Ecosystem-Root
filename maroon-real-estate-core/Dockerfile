FROM node:20-slim
WORKDIR /app
COPY package.json .
RUN npm install --production
COPY src/ ./src/
EXPOSE 8003
CMD ["node", "src/app.js"]
