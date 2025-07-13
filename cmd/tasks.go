package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/datetime"
	"journal/internal/obsidian"
	"log"
)

var (
	taskStartDate string
	taskEndDate   string

	tasksCmd = &cobra.Command{
		Use:   "tasks",
		Short: "List tasks in the given date range",
		Long:  `List tasks in the given date range from the journal.`,
		Run: func(cmd *cobra.Command, args []string) {

			pages, err := app.Vault.PageRange(taskStartDate, taskEndDate)
			if err != nil {
				log.Fatalf("Failed to parse pages in date range: %v", err)
			}

			tasks, err := obsidian.TasksInPages(pages, true)
			if err != nil {
				log.Fatalf("Failed to retrieve tasks: %v", err)
			}

			for _, task := range tasks {
				fmt.Println(task.String())
			}
		},
	}
)

func initTasksCmd() {
	rootCmd.AddCommand(tasksCmd)

	tasksCmd.Flags().StringVarP(&taskStartDate, "start", "s", datetime.OneMonthAgo().String(), "Start date for the task range (YYYY-MM-DD)")
	tasksCmd.Flags().StringVarP(&taskEndDate, "end", "e", datetime.Today().String(), "End date for the task range (YYYY-MM-DD)")
}
