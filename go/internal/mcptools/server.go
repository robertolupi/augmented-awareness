package mcptools

import (
	"github.com/mark3labs/mcp-go/server"
)

func NewServer() *server.MCPServer {
	s := server.NewMCPServer(
		"Augmented Awareness",
		"1.0.0",
		server.WithToolCapabilities(true),
		server.WithResourceCapabilities(false, true))

	addDateTimeTool(s)
	addPagesToolAndResources(s)
	addJournalTool(s)
	addTasksTool(s)

	return s
}
