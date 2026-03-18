package cmd

import (
	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"
	"journal/internal/tui"
)

var (
	uiCmd = &cobra.Command{
		Use:   "tui",
		Short: "Start the TUI",
		Long:  `Start the TUI`,
		RunE: func(cmd *cobra.Command, args []string) error {
			p := tea.NewProgram(tui.New(app.Vault, app.JournalSection), tea.WithAltScreen())
			if _, err := p.Run(); err != nil {
				return err
			}
			return nil
		},
	}
)

func initUiCmd() {
	rootCmd.AddCommand(uiCmd)
}
