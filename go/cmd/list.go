package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/obsidian"
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
				log.Fatalf("Failed to find section %s in journal page: %v", journalSection, err)
			}

			for i := section.Start; i < section.End; i++ {
				event := obsidian.MaybeParseEvent(page.Content[i])
				if event != nil {
					fmt.Printf("%5s %5s\t%10s\t%s\n", event.StartTime, event.EndTime, event.Duration, event.Text)
				}
			}
		},
	}
)

func initListCmd() {
	rootCmd.AddCommand(listCmd)
}
