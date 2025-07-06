package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
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
			if err := initVault(); err != nil {
				log.Fatalf("Failed to initialize vault: %v", err)
			}

			dateRange, err := obsidian.DateRange(taskStartDate, taskEndDate)
			if err != nil {
				log.Fatalf("Failed to parse date range: %v", err)
			}

			tasks, err := obsidian.TasksInDateRange(vault, dateRange, true)
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

	tasksCmd.Flags().StringVarP(&taskStartDate, "start", "s", oneWeekAgo(), "Start date for the task range (YYYY-MM-DD)")
	tasksCmd.Flags().StringVarP(&taskEndDate, "end", "e", today(), "End date for the task range (YYYY-MM-DD)")
}
