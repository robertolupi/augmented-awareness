package mcptools

import (
	"context"
	"errors"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"strings"
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

		results, err := vault.Search(query)
		if err != nil {
			return nil, errors.New("error performing search: " + err.Error())
		}

		var sb strings.Builder
		for _, result := range results {
			sb.WriteString("[[" + result.Name() + "]]\n")
		}

		return mcp.NewToolResultText(sb.String()), nil
	})
}
