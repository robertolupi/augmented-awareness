package mcptools

import (
	"context"
	"errors"
	"fmt"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func addMemoryTool(s *server.MCPServer) {
	rememberTool := mcp.NewTool("remember",
		mcp.WithDescription("Remember a fact or piece of information. Facts will be stored in a page called 'aww-scratchpad' in the vault."),
		mcp.WithIdempotentHintAnnotation(false),
		mcp.WithReadOnlyHintAnnotation(false),
		mcp.WithString("fact",
			mcp.Description("The fact or information to remember."),
			mcp.Required(),
		),
	)

	s.AddTool(rememberTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		fact := request.GetString("fact", "")
		if fact == "" {
			return nil, errors.New("fact is required")
		}

		page, err := vault.Page("aww-scratchpad")
		if err != nil {
			return nil, fmt.Errorf("failed to retrieve scratchpad page: %w", err)
		}

		page.Content = append(page.Content, fact)

		err = page.Save()
		if err != nil {
			return nil, fmt.Errorf("failed to save scratchpad page: %w", err)
		}

		return mcp.NewToolResultText("Fact remembered successfully!"), nil
	})

}
