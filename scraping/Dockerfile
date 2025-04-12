FROM golang:1.23.1-alpine

WORKDIR /app

COPY ./scraping ./scraping
WORKDIR /app/scraping

RUN go mod tidy && go build -o main ./cmd/main.go

CMD ["./main"]
#ENTRYPOINT ["top", "-b"]