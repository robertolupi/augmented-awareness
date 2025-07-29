package mcptools

import (
	"context"
	"fmt"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"strings"
	"time"
)

func addDateTimeTool(s *server.MCPServer) {
	currentDateTool := mcp.NewTool("today",
		mcp.WithDescription("Get the date and time as of today."),
		mcp.WithIdempotentHintAnnotation(true),
		mcp.WithReadOnlyHintAnnotation(true))
	s.AddTool(currentDateTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return mcp.NewToolResultText(currentDateTime()), nil
	})
}

func currentDateTime() string {
	var sb strings.Builder

	today := time.Now()
	sb.WriteString("Now is ")
	sb.WriteString(today.Format("Monday, 2006-01-02 15:04:05"))

	sb.WriteString("\n")

	sb.WriteString("The pages relevant to today are:\n")
	sb.WriteString(" - Year: [[Y" + today.Format("2006") + "]]\n")
	sb.WriteString(" - Month: [[" + today.Format("2006-01") + "]]\n")
	sb.WriteString(" - Day: [[" + today.Format("2006-01-02") + "]]\\n")
	year, week := today.ISOWeek()
	sb.WriteString(" - Week: [[" + fmt.Sprintf("%d-W%02d", year, week) + "]]\n")
	return sb.String()
}
