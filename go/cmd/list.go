package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"log"
)

var (
	listCmd = &cobra.Command{
		Use:   "list",
		Short: "List today events",
		Long:  `List today events in the journal.`,
		Run: func(cmd *cobra.Command, args []string) {
			if err := initVault(); err != nil {
				log.Fatalf("Failed to initialize vault: %v", err)
			}

			page, err := vault.Page(today())
			if err != nil {
				log.Fatalf("Failed to get journal page: %v", err)
			}

			section, err := page.FindSection(journalSection)
			if err != nil {
				log.Fatalf("Failed to find journal section: %v", err)
			}

			events, err := section.Events()
			if err != nil {
				log.Fatalf("Failed to get events from journal page: %v", err)
			}

			for _, event := range events {
				fmt.Printf("%5s %5s\t%10s\t%s\n", event.StartTime, event.EndTime, event.Duration, event.Text)
			}
		},
	}
)

func initListCmd() {
	rootCmd.AddCommand(listCmd)
}
