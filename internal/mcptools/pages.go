package mcptools

import (
	"context"
	"fmt"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"journal/internal/obsidian"
	"strings"
)

func addPageResources(s *server.MCPServer) {
	s.AddResource(
		mcp.NewResource(
			"file://{page_name}",
			"Vault Page",
			mcp.WithResourceDescription("A page in the vault, identified by its name."),
			mcp.WithMIMEType("text/markdown"),
		),
		handlePageResource,
	)
}

// trimPageName transforms page names like pages/2023-10-01 or [[2023-10-01]] to just 2023-10-01
func trimPageName(pageName string) string {
	pageName = strings.TrimPrefix(pageName, "file://")
	pageName = strings.TrimPrefix(pageName, "[[")
	pageName = strings.TrimSuffix(pageName, "]]")
	return pageName
}

func returnPages(ctx context.Context, pages []*obsidian.Page) (*mcp.CallToolResult, error) {
	return returnPagesWithMsg(ctx, pages, "Found the requested pages:")
}

func returnPagesWithMsg(ctx context.Context, pages []*obsidian.Page, msg string) (*mcp.CallToolResult, error) {
	if len(pages) == 0 {
		return mcp.NewToolResultText("No pages found matching your request."), nil
	}

	existing := make([]mcp.EmbeddedResource, 0, len(pages))
	for _, page := range pages {
		if page == nil {
			continue
		}
		resource := mcp.NewEmbeddedResource(mcp.TextResourceContents{
			URI:      "file://" + page.Name(),
			MIMEType: "text/markdown",
			Text:     pageContent(page),
		})
		existing = append(existing, resource)
	}

	content := []mcp.Content{mcp.NewTextContent(msg)}
	for _, link := range existing {
		content = append(content, link)
	}

	return &mcp.CallToolResult{Content: content}, nil
}

func returnExistingPagesByName(ctx context.Context, pages []string) (*mcp.CallToolResult, error) {
	existing := make([]*obsidian.Page, 0, len(pages))
	for _, name := range pages {
		name = trimPageName(name)
		if name == "" {
			continue
		}
		page, err := app.Vault.Page(name)
		if err != nil || page == nil {
			continue
		}
		existing = append(existing, page)
	}
	if len(existing) == 0 {
		return mcp.NewToolResultText("No pages found matching your request."), nil
	}

	return returnPages(ctx, existing)
}

func handlePageResource(ctx context.Context, req mcp.ReadResourceRequest) ([]mcp.ResourceContents, error) {
	parts := strings.Split(req.Params.URI, "://")
	if len(parts) != 2 || parts[0] != "file" {
		return nil, fmt.Errorf("invalid resource URI: %s", req.Params.URI)
	}
	pageName := trimPageName(req.Params.URI)
	page, err := app.Vault.Page(pageName)
	if err != nil {
		return nil, fmt.Errorf("error retrieving page: %w", err)
	}
	if page == nil {
		return nil, fmt.Errorf("page not found: %s", pageName)
	}

	return []mcp.ResourceContents{
		mcp.TextResourceContents{
			URI:      req.Params.URI,
			MIMEType: "text/markdown",
			Text:     pageContent(page),
		},
	}, nil
}

func pageContent(page *obsidian.Page) string {
	return strings.Join(obsidian.SkipCodeBlocks(page.Content), "\n")
}
