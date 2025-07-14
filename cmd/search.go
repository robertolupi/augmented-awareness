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
			if len(args) == 0 {
				log.Println("Please provide a search term.")
				return
			}

			pages, err := app.Search(strings.Join(args, " "))
			if err != nil {
				log.Fatalf("Failed to search pages: %v", err)
			}

			if len(pages) == 0 {
				fmt.Println("No pages found matching the search term.")
				return
			}

			fmt.Println("Found pages:")
			for _, page := range pages {
				fmt.Println(page.Name())
			}
		},
	}
)

func initSearchCmd() {
	rootCmd.AddCommand(searchCmd)
}
