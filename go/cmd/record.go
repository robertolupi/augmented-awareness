package cmd

import (
	"github.com/spf13/cobra"
	"journal/internal/obsidian"
	"log"
	"strings"
)

var (
	recordDate string

	recordCmd = &cobra.Command{
		Use:   "record",
		Short: "Record a new journal entry",
		Long:  `Record a new journal entry in the Obsidian vault.`,
		Run: func(cmd *cobra.Command, args []string) {
			if err := initVault(); err != nil {
				log.Fatalf("Failed to initialize vault: %v", err)
			}

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

			if len(events) > 0 {
				event := events[len(events)-1]
				if event.EndTime == "" {
					event.EndTime = obsidian.TimeNow()
					if err := section.AmendEvent(event); err != nil {
						log.Fatalf("Failed to amend event: %v", err)
					}
				}
			}

			newEvent := obsidian.Event{
				StartTime: obsidian.TimeNow(),
				Text:      strings.Join(args, " "),
			}

			if err := section.AddEvent(newEvent); err != nil {
				log.Fatalf("Failed to add new event: %v", err)
			}

			if err := page.Save(); err != nil {
				log.Fatalf("Failed to save page: %v", err)
			}
		},
	}
)

func initRecordCmd() {
	rootCmd.AddCommand(recordCmd)

	recordCmd.Flags().StringVar(&recordDate, "date", today(), "Date of the journal entry (YYYY-MM-DD)")
	recordCmd.Args = cobra.MinimumNArgs(1)
}
