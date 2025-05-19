package cmd

import (
	"github.com/spf13/cobra"
	"journal/internal/obsidian"
	"log"
	"strings"
)

var (
	amendCmd = &cobra.Command{
		Use:   "amend",
		Short: "Amend the last journal entry",
		Long:  `Amend the last journal entry in the Obsidian vault.`,
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
			if event == nil {
				log.Fatalf("No event found to amend")
			}

			event.Text = strings.Join(args, " ")
			page.Content[i] = event.String()

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
