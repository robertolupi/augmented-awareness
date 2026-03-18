package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/datetime"
	"journal/internal/obsidian"
	"strings"
)

var (
	recordDate string

	recordCmd = &cobra.Command{
		Use:   "record",
		Short: "Record a new journal entry",
		Long:  `Record a new journal entry in the Obsidian vault.`,
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

			if len(events) > 0 {
				event := events[len(events)-1]
				if event.EndTime == "" {
					event.EndTime = datetime.TimeNow()
					if err := section.AmendEvent(event); err != nil {
						return fmt.Errorf("failed to amend event: %w", err)
					}
				}
			}

			newEvent := obsidian.Event{
				StartTime: datetime.TimeNow(),
				Text:      strings.Join(args, " "),
			}

			if err := section.AddEvent(newEvent); err != nil {
				return fmt.Errorf("failed to add new event: %w", err)
			}

			if err := page.Save(); err != nil {
				return fmt.Errorf("failed to save page: %w", err)
			}
			return nil
		},
	}
)

func initRecordCmd() {
	rootCmd.AddCommand(recordCmd)

	recordCmd.Flags().StringVar(&recordDate, "date", datetime.Today().String(), "Date of the journal entry (YYYY-MM-DD)")
	recordCmd.Args = cobra.MinimumNArgs(1)
}
