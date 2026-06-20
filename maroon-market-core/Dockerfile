FROM node:20-slim
WORKDIR /app
COPY package.json tsconfig.json ./
RUN npm install
COPY src/ ./src/
COPY medusa-config.js .
RUN npx tsc
EXPOSE 9000
USER nobody
CMD ["medusa", "start"]
