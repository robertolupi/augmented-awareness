package mcptools

import (
	"context"
	"fmt"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"strings"
	"time"
)

func addTasksTool(s *server.MCPServer) {
	tasksTool := mcp.NewTool("read-tasks",
		mcp.WithDescription("Read tasks for a given date range."),
		mcp.WithIdempotentHintAnnotation(true),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithString("start",
			mcp.Description("Start date for the task range (YYYY-MM-DD). Defaults to one week ago.")),
		mcp.WithString("end",
			mcp.Description("End date for the task range (YYYY-MM-DD). Defaults to today.")),
		mcp.WithString("include_done",
			mcp.Description("Whether to include completed tasks (true/false). Defaults to false.")))

	s.AddTool(tasksTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		startDate := request.GetString("start", "")
		if startDate == "" {
			startDate = time.Now().AddDate(0, 0, -6).Format("2006-01-02")
		}

		endDate := request.GetString("end", "")
		if endDate == "" {
			endDate = time.Now().Format("2006-01-02")
		}

		includeDoneStr := request.GetString("include_done", "false")
		includeDone := includeDoneStr == "true"

		tasks, err := app.TasksInDateRange(startDate, endDate, includeDone)
		if err != nil {
			return nil, fmt.Errorf("failed to retrieve tasks: %w", err)
		}

		var content strings.Builder
		content.WriteString("# Tasks from " + startDate + " to " + endDate + "\n\n")

		if len(tasks) == 0 {
			content.WriteString("No tasks found in the specified date range.\n")
		} else {
			for _, task := range tasks {
				content.WriteString("- " + task.String() + "\n")
			}
		}

		return mcp.NewToolResultText(content.String()), nil
	})
}
