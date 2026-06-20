FROM node:20-slim
WORKDIR /app
COPY configs/package.json .
RUN npm install
COPY src/ ./src/
EXPOSE 4000
USER nobody
CMD ["node", "src/index.js"]
