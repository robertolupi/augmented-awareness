package cmd

import (
	"github.com/mark3labs/mcp-go/server"
	"github.com/spf13/cobra"
	"journal/internal/mcptools"
)

var (
	mcpCmd = &cobra.Command{
		Use:   "mcp",
		Short: "Run as a MCP server",
		Long:  `Run as a MCP (Model Context Protocol) server, allowing LLMs to read journal entries and tasks.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			// https://mcp-go.dev/getting-started

			mcptools.SetApp(app)

			s := mcptools.NewServer()

			if err := server.ServeStdio(s); err != nil {
				return err
			}
			return nil
		},
	}
)

func initMcpCmd() {
	rootCmd.AddCommand(mcpCmd)
}
