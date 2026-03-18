package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"strings"
)

var (
	searchCmd = &cobra.Command{
		Use:   "search",
		Short: "Search for pages in the journal",
		Long:  `Search for pages in the journal based on text they contain in their title.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) == 0 {
				return fmt.Errorf("please provide a search term")
			}

			pages, err := app.Search(strings.Join(args, " "))
			if err != nil {
				return fmt.Errorf("failed to search pages: %w", err)
			}

			if len(pages) == 0 {
				fmt.Println("No pages found matching the search term.")
				return nil
			}

			fmt.Println("Found pages:")
			for _, page := range pages {
				fmt.Println(page.Name())
			}
			return nil
		},
	}
)

func initSearchCmd() {
	rootCmd.AddCommand(searchCmd)
}
