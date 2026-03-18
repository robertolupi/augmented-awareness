package cmd

import (
	"fmt"
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
		RunE: func(cmd *cobra.Command, args []string) error {
			index, err := search.NewIndex(dataPath)
			if err != nil {
				return fmt.Errorf("failed to create index at %s: %w", dataPath, err)
			}
			defer index.Close()

			var allPaths []string
			err = app.Vault.WalkPages(func(pagePath string, d os.DirEntry, err error) error {
				allPaths = append(allPaths, pagePath)
				return nil
			})
			if err != nil {
				return fmt.Errorf("failed to walk pages in vault: %w", err)
			}

			err = tui.ShowProgress(func(setProgress tui.SetProgressFunc, reportError tui.ReportErrorFunc) error {
				for i, pagePath := range allPaths {
					page, err := app.Vault.PageByPath(pagePath)
					if err != nil {
						log.Printf("Failed to get page by path %q: %v", pagePath, err)
						reportError(err)
						continue
					}
					if page == nil {
						log.Printf("No page found at path %q", pagePath)
						reportError(fmt.Errorf("no page found at path %q", pagePath))
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
				return fmt.Errorf("failed to index journal pages: %w", err)
			}
			return nil
		},
	}
)

func initIndexCmd() {
	rootCmd.AddCommand(indexCmd)
}
