package mcptools

import (
	"context"
	"errors"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"journal/internal/obsidian"
	"strings"
)

func addPagesToolAndResources(s *server.MCPServer) {
	pagesTool := mcp.NewTool("read-page",
		mcp.WithDescription("Read one or more pages from the vault, and return their content in markdown format."),
		mcp.WithIdempotentHintAnnotation(true),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithArray("pages",
			mcp.Description("names of pages to read, e.g. 2023-10-01 or [[2023-10-01]]."),
			mcp.Required()),
	)

	s.AddTool(pagesTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		pageNames := request.GetStringSlice("pages", nil)
		var sb strings.Builder

		for _, pageName := range pageNames {
			pageName = trimPageName(pageName)
			if pageName == "" {
				return nil, errors.New("invalid page name provided")
			}

			page, err := vault.Page(pageName)
			if err != nil {
				return nil, errors.New("error retrieving page: " + err.Error())
			}
			if page == nil {
				return nil, errors.New("page not found: " + pageName)
			}
			sb.WriteString("<page name=" + pageName + ">\n")
			sb.WriteString(pageContent(page))
			sb.WriteString("</page>\n\n")
		}

		return mcp.NewToolResultText(sb.String()), nil
	})
}

// trimPageName transforms page names like journal://pages/2023-10-01 or [[2023-10-01]] to just 2023-10-01
func trimPageName(pageName string) string {
	pageName = strings.TrimPrefix(pageName, "journal://pages/")
	pageName = strings.TrimPrefix(pageName, "[[")
	pageName = strings.TrimSuffix(pageName, "]]")
	return pageName
}

func pageContent(page *obsidian.Page) string {
	return "Page [[" + page.Name() + "]]:\n" + strings.Join(obsidian.SkipCodeBlocks(page.Content), "\n")
}
