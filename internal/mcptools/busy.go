package mcptools

import (
	"context"
	"fmt"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"time"
)

func addBusyTool(s *server.MCPServer) {
	busyTool := mcp.NewTool("past-activities",
		mcp.WithDescription("Read a report of how the user spent their time for a given date range."),
		mcp.WithIdempotentHintAnnotation(true),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithString("start",
			mcp.Description("Start date for the report (YYYY-MM-DD). Defaults to one week ago.")),
		mcp.WithString("end",
			mcp.Description("End date for the report (YYYY-MM-DD). Defaults to today.")),
		mcp.WithString("expand_tags",
			mcp.Description("Whether to expand tags (true/false). Defaults to false.")),
		mcp.WithString("bucket_size",
			mcp.Description("Bucket size for the histogram (e.g. '30m'). Defaults to '30m'.")))

	s.AddTool(busyTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {

		startDate := request.GetString("start", "")
		if startDate == "" {
			startDate = time.Now().AddDate(0, 0, -6).Format("2006-01-02")
		}

		endDate := request.GetString("end", "")
		if endDate == "" {
			endDate = time.Now().Format("2006-01-02")
		}

		expandTagsStr := request.GetString("expand_tags", "false")
		expandTags := expandTagsStr == "true"

		bucketSizeStr := request.GetString("bucket_size", "30m")
		bucketSize, err := time.ParseDuration(bucketSizeStr)
		if err != nil {
			return nil, fmt.Errorf("failed to parse bucket size: %w", err)
		}

		report, err := app.BusyReport(startDate, endDate, expandTags, bucketSize)
		if err != nil {
			return nil, fmt.Errorf("failed to generate busy report: %w", err)
		}

		return mcp.NewToolResultText(report), nil
	})
}
