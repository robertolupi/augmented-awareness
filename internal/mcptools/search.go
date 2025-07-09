package mcptools

import (
	"context"
	"errors"
	"fmt"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"journal/internal/search"
	"path"
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

		index, err := search.NewIndex(dataPath)
		if err != nil {
			return nil, fmt.Errorf("failed to open or create index", err)
		}
		defer index.Close()

		results, err := index.Search(query)
		if err != nil {
			return nil, fmt.Errorf("failed to search index: %w", err)
		}
		if len(results.Hits) == 0 {
			return mcp.NewToolResultText("No pages found matching your search query."), nil
		}

		var sb strings.Builder
		sb.WriteString("The following pages match your search query:\n\n")
		for _, result := range results.Hits {
			_, pageFile := path.Split(result.ID)
			pageName := strings.TrimSuffix(pageFile, ".md")
			sb.WriteString("[[" + pageName + "]]\n")
		}

		return mcp.NewToolResultText(sb.String()), nil
	})
}
