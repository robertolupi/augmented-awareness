package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/datetime"
	"journal/internal/obsidian"
	"log"
)

var (
	stopDate string

	stopCmd = &cobra.Command{
		Use:   "stop",
		Short: "Stop the current journal event",
		Long:  "Stop the current journal event in the Obsidian vault.",
		Run: func(cmd *cobra.Command, args []string) {
			if err := stopCurrentEvent(app.Vault, journalSection, stopDate); err != nil {
				log.Fatalf("Failed to stop event: %v", err)
			}
		},
	}
)

func initStopCmd() {
	rootCmd.AddCommand(stopCmd)

	stopCmd.Flags().StringVar(&stopDate, "date", datetime.Today().String(), "Date of the journal entry (YYYY-MM-DD)")
}

func stopCurrentEvent(vault *obsidian.Vault, sectionName, date string) error {
	page, err := vault.Page(date)
	if err != nil {
		return fmt.Errorf("failed to get journal page: %w", err)
	}

	section, err := page.FindSection(sectionName)
	if err != nil {
		return fmt.Errorf("failed to find section %s in journal page: %w", sectionName, err)
	}

	events, err := section.Events()
	if err != nil {
		return fmt.Errorf("failed to get events from section %s: %w", sectionName, err)
	}

	if len(events) == 0 {
		return fmt.Errorf("no events found in section %s", sectionName)
	}

	event := events[len(events)-1]
	if !event.EndTime.IsEmpty() {
		return fmt.Errorf("last event already ended at %s", event.EndTime)
	}

	event.EndTime = datetime.TimeNow()
	if err := section.AmendEvent(event); err != nil {
		return fmt.Errorf("failed to amend event: %w", err)
	}

	if err := page.Save(); err != nil {
		return fmt.Errorf("failed to save page: %w", err)
	}

	return nil
}
