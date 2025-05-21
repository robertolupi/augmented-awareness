package cmd

import (
	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"
	"journal/internal/tui"
	"log"
)

var (
	uiCmd = &cobra.Command{
		Use:   "tui",
		Short: "Start the TUI",
		Long:  `Start the TUI`,
		Run: func(cmd *cobra.Command, args []string) {
			if err := initVault(); err != nil {
				log.Fatalf("Failed to initialize vault: %v", err)
			}
			p := tea.NewProgram(tui.NewPageEditor(vault, today(), journalSection), tea.WithAltScreen())
			if _, err := p.Run(); err != nil {
				log.Fatalf("Error running program: %v", err)
			}
		},
	}
)

func initUiCmd() {
	rootCmd.AddCommand(uiCmd)
}
