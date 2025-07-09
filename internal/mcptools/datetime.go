package mcptools

import (
	"context"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"time"
)

func addDateTimeTool(s *server.MCPServer) {
	currentDateTool := mcp.NewTool("current-date-time",
		mcp.WithDescription("Get the current date and time."),
		mcp.WithIdempotentHintAnnotation(true),
		mcp.WithReadOnlyHintAnnotation(true))
	s.AddTool(currentDateTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return mcp.NewToolResultText("Today is " + time.Now().Format("Monday, 2006-01-02 15:04:05")), nil
	})
}
