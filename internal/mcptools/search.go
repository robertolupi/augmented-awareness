package mcptools

import (
	"context"
	"errors"
	"fmt"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func addSearchTool(s *server.MCPServer) {
	searchTool := mcp.NewTool("search-pages",
		mcp.WithDescription("Search for pages in the vault."),
		mcp.WithIdempotentHintAnnotation(true),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithString("query",
			mcp.Description("The regexp query to search for in page names."),
			mcp.Required()))

	s.AddTool(searchTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		query := request.GetString("query", "")
		if query == "" {
			return nil, errors.New("search query cannot be empty")
		}

		pages, err := app.Search(query)
		if err != nil {
			return nil, fmt.Errorf("failed to search pages: %w", err)
		}

		if len(pages) == 0 {
			return mcp.NewToolResultText("No pages found matching your search query."), nil
		}

		return returnPages(ctx, pages)
	})
}
