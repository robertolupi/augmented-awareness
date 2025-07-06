package mcptools

import (
	_ "embed"
	"github.com/mark3labs/mcp-go/server"
)

//go:embed instructions.md
var instructions string

func NewServer() *server.MCPServer {
	s := server.NewMCPServer(
		"Augmented Awareness",
		"1.0.0",
		server.WithToolCapabilities(true),
		server.WithResourceCapabilities(false, true),
		server.WithInstructions(instructions))

	addDateTimeTool(s)
	addPagesToolAndResources(s)
	addJournalTool(s)
	addTasksTool(s)

	return s
}
