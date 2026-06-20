FROM golang:1.21-alpine AS builder
RUN apk add --no-cache gcc musl-dev
WORKDIR /app
COPY configs/go.mod .
COPY src/ ./src/
RUN cd src && go build -o /maroon-tube main.go

FROM alpine:3.19
RUN apk add --no-cache ffmpeg ca-certificates
COPY --from=builder /maroon-tube /usr/local/bin/
EXPOSE 8080
USER nobody
CMD ["maroon-tube"]
