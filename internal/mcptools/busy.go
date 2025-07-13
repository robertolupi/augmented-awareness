package mcptools

import (
	"context"
	"fmt"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"journal/internal/stats"
	"strings"
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

		pages, err := app.Vault.PageRange(startDate, endDate)
		if err != nil {
			return nil, fmt.Errorf("failed to read pages: %w", err)
		}

		report, err := stats.NewBusyReport(stats.PeriodDaily, bucketSize)
		if err != nil {
			return nil, fmt.Errorf("failed to create busy report: %w", err)
		}

		for _, page := range pages {
			section, err := page.FindSection(app.JournalSection)
			if err != nil {
				continue
			}

			events, err := section.Events()
			if err != nil {
				continue
			}

			for _, event := range events {
				err := report.AddEvent(event.StartTime.Time(), event.Duration, event.Tags)
				if err != nil {
					return nil, fmt.Errorf("failed to add event to report: %w", err)
				}
			}
		}

		if expandTags {
			report.ExpandTags()
		}

		var content strings.Builder
		content.WriteString(fmt.Sprintf("# Busy report from %s to %s\n\n", startDate, endDate))
		content.WriteString(fmt.Sprintf("Found %d journal pages: %v\n\n", len(pages), pages))

		sortedTags := report.SortedTags()
		formatString := "%-40s\t%s  %.2f%%\n"
		content.WriteString(fmt.Sprintf(formatString, "Total", report.Total, 100.0))
		if report.Total.Duration > 0 {
			content.WriteString(fmt.Sprintf(formatString, "No tags", report.NoTags, float64(report.NoTags.Duration)/float64(report.Total.Duration)*100))
		} else {
			content.WriteString(fmt.Sprintf(formatString, "No tags", report.NoTags, 0.0))
		}

		content.WriteString("\nTags sorted by duration:\n")
		for _, tagDuration := range sortedTags {
			content.WriteString(fmt.Sprintf(formatString, tagDuration.Tag, tagDuration.Histogram, tagDuration.Percent))
		}

		return mcp.NewToolResultText(content.String()), nil
	})
}
