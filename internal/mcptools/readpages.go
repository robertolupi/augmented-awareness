package mcptools

import (
	"context"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func addReadPageTool(s *server.MCPServer) {
	pagesTool := mcp.NewTool("read-page",
		mcp.WithDescription("Read one or more pages from the vault, and return their content in markdown format."),
		mcp.WithIdempotentHintAnnotation(true),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithArray("pages",
			mcp.Description("names of pages to read, e.g. 2023-10-01 or [[2023-10-01]]."),
			mcp.WithStringItems(mcp.MinLength(1)),
			mcp.Required()),
	)

	s.AddTool(pagesTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		pageNames := request.GetStringSlice("pages", nil)
		return returnExistingPagesByName(ctx, pageNames)
	})
}
