package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"strings"
)

var (
	amendCmd = &cobra.Command{
		Use:   "amend",
		Short: "Amend the last journal entry",
		Long:  `Amend the last journal entry in the Obsidian vault.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			page, err := app.Vault.Page(recordDate)
			if err != nil {
				return fmt.Errorf("failed to get journal page: %w", err)
			}

			section, err := page.FindSection(journalSection)
			if err != nil {
				return fmt.Errorf("failed to find section %s in journal page: %w", journalSection, err)
			}

			events, err := section.Events()
			if err != nil {
				return fmt.Errorf("failed to get events from section %s: %w", journalSection, err)
			}

			if len(events) == 0 {
				return fmt.Errorf("no events found in section %s", journalSection)
			}

			event := events[len(events)-1]

			event.Text = strings.Join(args, " ")

			if err := section.AmendEvent(event); err != nil {
				return fmt.Errorf("failed to amend event: %w", err)
			}

			if err := page.Save(); err != nil {
				return fmt.Errorf("failed to save page: %w", err)
			}
			return nil
		},
	}
)

func initAmendCmd() {
	rootCmd.AddCommand(amendCmd)

	amendCmd.Args = cobra.MinimumNArgs(1)
}
