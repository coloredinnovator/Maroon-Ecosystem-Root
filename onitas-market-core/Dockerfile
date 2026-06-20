FROM node:20-slim AS build
WORKDIR /app
COPY package.json .
RUN npm install
COPY src/ ./src/
COPY public/ ./public/ 2>/dev/null || true
RUN npm run build 2>/dev/null || echo "Build step optional"

FROM node:20-slim
WORKDIR /app
COPY --from=build /app .
EXPOSE 3000
USER nobody
CMD ["npm", "start"]
