package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/datetime"
	"log"
)

var (
	taskCleanupStartDate string
	taskCleanupEndDate   string
	tasksCleanupCmd      = &cobra.Command{
		Use:   "tasks-cleanup",
		Short: "Cleanup incomplete tasks (marked as delete) in the journal",
		Long:  `This command will remove incomplete tasks that are marked for deletion from the journal files.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			pages, err := app.Vault.PageRange(taskCleanupStartDate, taskCleanupEndDate)
			if err != nil {
				return fmt.Errorf("failed to parse pages in date range: %w", err)
			}

			for _, page := range pages {
				tasks := page.Tasks()
				if len(tasks) == 0 {
					continue
				}
				linesToRemove := make([]int, 0)
				for _, task := range tasks {
					if task.OnCompletion == "delete" && !task.IsDone() {
						linesToRemove = append(linesToRemove, task.LineNumber)
					}
				}
				if len(linesToRemove) > 0 {
					for i := len(linesToRemove) - 1; i >= 0; i-- {
						page.Content = append(page.Content[:linesToRemove[i]], page.Content[linesToRemove[i]+1:]...)
					}
				}
				err := page.Save()
				if err != nil {
					return fmt.Errorf("failed to save page %s after cleanup: %w", page.Name(), err)
				}
				log.Printf("Cleaned up %d tasks marked for deletion in page %s", len(linesToRemove), page.Name())
			}
			return nil
		},
	}
)

func initTasksCleanupCmd() {
	rootCmd.AddCommand(tasksCleanupCmd)

	tasksCleanupCmd.Flags().StringVarP(&taskCleanupStartDate, "start", "s", datetime.OneMonthAgo().String(), "Start date for the task cleanup range (YYYY-MM-DD)")
	tasksCleanupCmd.Flags().StringVarP(&taskCleanupEndDate, "end", "e", datetime.SixDaysAgo().String(), "End date for the task cleanup range (YYYY-MM-DD)")
}
