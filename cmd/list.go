package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/datetime"
)

var (
	listCmd = &cobra.Command{
		Use:   "list",
		Short: "List today events",
		Long:  `List today events in the journal.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			page, err := app.Vault.Page(datetime.Today().String())
			if err != nil {
				return fmt.Errorf("failed to get journal page: %w", err)
			}

			section, err := page.FindSection(journalSection)
			if err != nil {
				return fmt.Errorf("failed to find journal section: %w", err)
			}

			events, err := section.Events()
			if err != nil {
				return fmt.Errorf("failed to get events from journal page: %w", err)
			}

			for _, event := range events {
				fmt.Printf("%5s %5s\t%10s\t%s\n", event.StartTime, event.EndTime, event.Duration, event.Text)
			}
			return nil
		},
	}
)

func initListCmd() {
	rootCmd.AddCommand(listCmd)
}
