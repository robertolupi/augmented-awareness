package mcptools

import (
	"context"
	"fmt"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"journal/internal/datetime"
	"journal/internal/obsidian"
)

func addRetroTool(s *server.MCPServer) {
	retroTool := mcp.NewTool("read-retrospectives",
		mcp.WithDescription("Read yearly/monthly/weekly/daily retrospectives for the given date."),
		mcp.WithIdempotentHintAnnotation(true),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithString("date",
			mcp.Description("optional date to read retrospectives for (format YYYY-MM-DD), if not specified defaults to the current date (today).")))

	s.AddTool(retroTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		dateString := request.GetString("date", datetime.Today().String())
		if dateString == "" {
			dateString = datetime.Today().String() // Default to today if no date is provided
		}

		date, err := datetime.DateFromString(dateString)
		if err != nil {
			return nil, fmt.Errorf("invalid date format: %s", err.Error())
		}

		pages := []string{
			obsidian.DailyRetroPageName(date),
			obsidian.WeeklyRetroPageName(date),
			obsidian.MonthlyRetroPageName(date),
			obsidian.YearlyRetroPageName(date),
		}

		return returnExistingPagesByName(ctx, pages)
	})
}
