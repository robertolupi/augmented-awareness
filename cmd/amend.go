package cmd

import (
	"github.com/spf13/cobra"
	"log"
	"strings"
)

var (
	amendCmd = &cobra.Command{
		Use:   "amend",
		Short: "Amend the last journal entry",
		Long:  `Amend the last journal entry in the Obsidian vault.`,
		Run: func(cmd *cobra.Command, args []string) {
			page, err := vault.Page(recordDate)
			if err != nil {
				log.Fatalf("Failed to get journal page: %v", err)
			}

			section, err := page.FindSection(journalSection)
			if err != nil {
				log.Fatalf("Failed to find section %s in journal page: %v", journalSection, err)
			}

			events, err := section.Events()
			if err != nil {
				log.Fatalf("Failed to get events from section %s: %v", journalSection, err)
			}

			if len(events) == 0 {
				log.Fatalf("No events found in section %s", journalSection)
			}

			event := events[len(events)-1]

			event.Text = strings.Join(args, " ")

			if err := section.AmendEvent(event); err != nil {
				log.Fatalf("Failed to amend event: %v", err)
			}

			if err := page.Save(); err != nil {
				log.Fatalf("Failed to save page: %v", err)
			}
		},
	}
)

func initAmendCmd() {
	rootCmd.AddCommand(amendCmd)

	amendCmd.Args = cobra.MinimumNArgs(1)
}
