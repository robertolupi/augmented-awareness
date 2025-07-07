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
		mcp.WithDescription("Read a page from the vault, and return its content in markdown format."),
		mcp.WithIdempotentHintAnnotation(true),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithString("page",
			mcp.Description("The name of the page to read, e.g. 2023-10-01 or [[2023-10-01]]."),
			mcp.Required()))

	s.AddResourceTemplate(
		mcp.NewResourceTemplate("journal://pages/{page}",
			"A journal page",
			mcp.WithTemplateDescription("A page in the journal vault."),
			mcp.WithTemplateMIMEType("text/markdown"),
		),
		func(ctx context.Context, request mcp.ReadResourceRequest) ([]mcp.ResourceContents, error) {
			pageName := trimPageName(request.Params.URI)
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
			return []mcp.ResourceContents{
				mcp.TextResourceContents{
					URI:      request.Params.URI,
					MIMEType: "text/markdown",
					Text:     pageContent(page),
				},
			}, nil
		})

	s.AddTool(pagesTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		pageName := request.GetString("page", "")
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

		return mcp.NewToolResultText(pageContent(page)), nil
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
	return strings.Join(obsidian.SkipCodeBlocks(page.Content), "\n")
}
