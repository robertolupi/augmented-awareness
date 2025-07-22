package mcptools

import (
	"context"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"strings"
	"time"
)

func addJournalTool(s *server.MCPServer) {
	journalTool := mcp.NewTool("weekly-journal",
		mcp.WithDescription("Read journal for the past week, up to and including today."),
		mcp.WithIdempotentHintAnnotation(true),
		mcp.WithReadOnlyHintAnnotation(false))

	s.AddTool(journalTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		var dateRange []string
		start := time.Now().AddDate(0, 0, -6)
		for i := 0; i < 7; i++ {
			date := start.AddDate(0, 0, i).Format("2006-01-02")
			dateRange = append(dateRange, date)
		}

		var content strings.Builder

		content.WriteString(currentDateTime())

		content.WriteString("The user journal for the past week is as follows:\n\n")

		pageNames := []string{}

		for _, date := range dateRange {
			pageNames = append(pageNames, date)
			pageNames = append(pageNames, "r"+date)
		}

		return returnExistingPagesByName(ctx, pageNames)
	})
}
