package cmd

import (
	"github.com/spf13/cobra"
	"journal/internal/obsidian"
	"log"
	"strings"
	"time"
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

			var event *obsidian.Event
			var i int
			for i = section.End - 1; i >= section.Start; i-- {
				event = obsidian.MaybeParseEvent(i, page.Content[i])
				if event != nil {
					break
				}
			}
			if event != nil {
				if event.EndTime == "" {
					event.EndTime = time.Now().Format("15:04")
					page.Content[i] = event.String()
				}
			}

			newEvent := &obsidian.Event{
				StartTime: time.Now().Format("15:04"),
				Text:      strings.Join(args, " "),
			}

			page.Content = append(page.Content[:section.End], append([]string{newEvent.String()}, page.Content[section.End:]...)...)

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
