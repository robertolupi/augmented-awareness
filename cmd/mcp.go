package cmd

import (
	"github.com/mark3labs/mcp-go/server"
	"github.com/spf13/cobra"
	"journal/internal/mcptools"
	"log"
)

var (
	mcpCmd = &cobra.Command{
		Use:   "mcp",
		Short: "Run as a MCP (Master Control Program) server",
		Long:  `Run as a MCP (Master Control Program) server, allowing LLMs to read journal entries and tasks.`,
		Run: func(cmd *cobra.Command, args []string) {
			// https://mcp-go.dev/getting-started

			mcptools.SetVault(vault)
			mcptools.SetJournalSection(journalSection)
			mcptools.SetDataPath(dataPath)

			s := mcptools.NewServer()

			if err := server.ServeStdio(s); err != nil {
				log.Fatalf("Error: %v\n", err)
			}
		},
	}
)

func initMcpCmd() {
	rootCmd.AddCommand(mcpCmd)
}
