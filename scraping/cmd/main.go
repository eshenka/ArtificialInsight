package main

import (
	"log"
	"net"

	//pb "art/scraping/pkg/proto"
	"google.golang.org/grpc"
)

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("не удалось прослушать: %v", err)
	}

	grpcServer := grpc.NewServer()

	//pb.RegisterScraperServiceServer(grpcServer, &scraperHandler.ScraperHandler{})

	log.Println("gRPC сервер запущен на :50051")
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("не удалось запустить сервер: %v", err)
	}
}
