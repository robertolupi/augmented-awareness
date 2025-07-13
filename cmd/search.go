package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/search"
	"log"
	"path"
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

			index, err := search.NewIndex(app.DataPath)
			if err != nil {
				log.Fatalf("Failed to open or create index at %s: %v", dataPath, err)
			}
			defer index.Close()

			results, err := index.Search(strings.Join(args, " "))
			if err != nil {
				log.Fatalf("Failed to search index: %v", err)
			}

			for _, result := range results.Hits {
				_, pageFile := path.Split(result.ID)
				pageName := strings.TrimSuffix(pageFile, ".md")
				fmt.Println(pageName)
			}
		},
	}
)

func initSearchCmd() {
	rootCmd.AddCommand(searchCmd)
}
