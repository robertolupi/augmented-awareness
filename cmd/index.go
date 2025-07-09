package cmd

import (
	"github.com/spf13/cobra"
	"journal/internal/search"
	"journal/internal/tui"
	"log"
	"os"
)

var (
	indexCmd = &cobra.Command{
		Use:   "index",
		Short: "Index the journal pages",
		Long:  `Index the journal pages to enable fast searching based on their content.`,
		Run: func(cmd *cobra.Command, args []string) {
			if err := initVault(); err != nil {
				log.Fatalf("Failed to initialize vault: %v", err)
			}

			index, err := search.NewIndex(dataPath)
			if err != nil {
				log.Fatalf("Failed to create index at %s: %v", dataPath, err)
			}
			defer index.Close()

			var allPaths []string
			err = vault.WalkPages(func(pagePath string, d os.DirEntry, err error) error {
				allPaths = append(allPaths, pagePath)
				return nil
			})
			if err != nil {
				log.Fatalf("Failed to walk pages in vault: %v", err)
			}

			err = tui.ShowProgress(func(setProgress tui.SetProgressFunc, reportError tui.ReportErrorFunc) error {
				for i, pagePath := range allPaths {
					page, err := vault.PageByPath(pagePath)
					if err != nil {
						log.Printf("Failed to get page by path %q: %v", pagePath, err)
						reportError(err)
						continue
					}
					if page == nil {
						log.Printf("No page found at path %q", pagePath)
						reportError(err)
						continue
					}
					if err := index.IndexPage(page); err != nil {
						log.Printf("Failed to index page %q: %v", page.Path, err)
						reportError(err)
					}

					// Update progress
					setProgress(page.Name(), float64(i+1)/float64(len(allPaths)))
				}
				return nil
			})
			if err != nil {
				log.Fatalf("Failed to index journal pages: %v", err)
			}
		},
	}
)

func initIndexCmd() {
	rootCmd.AddCommand(indexCmd)
}
