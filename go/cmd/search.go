package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"log"
	"strings"
)

var (
	searchCmd = &cobra.Command{
		Use:   "search",
		Short: "Search for pages in the journal",
		Long:  `Search for pages in the journal based on text they contain in their title.`,
		Run: func(cmd *cobra.Command, args []string) {
			if err := initVault(); err != nil {
				log.Fatalf("Failed to initialize vault: %v", err)
			}

			pages, err := vault.Search(strings.Join(args, "|"))
			if err != nil {
				log.Fatalf("Failed to search journal pages: %v", err)
			}

			if len(pages) == 0 {
				log.Println("No pages found matching the search criteria.")
				return
			}

			for _, page := range pages {
				fmt.Println(page.Name())
			}
		},
	}
)

func initSearchCmd() {
	rootCmd.AddCommand(searchCmd)
}
