package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/datetime"
)

var (
	taskStartDate string
	taskEndDate   string
	tasksSkipDone bool

	tasksCmd = &cobra.Command{
		Use:   "tasks",
		Short: "List tasks in the given date range",
		Long:  `List tasks in the given date range from the journal.`,
		RunE: func(cmd *cobra.Command, args []string) error {

			tasks, err := app.TasksInDateRange(taskStartDate, taskEndDate, tasksSkipDone)
			if err != nil {
				return fmt.Errorf("failed to retrieve tasks: %w", err)
			}

			for _, task := range tasks {
				fmt.Println(task.String())
			}
			return nil
		},
	}
)

func initTasksCmd() {
	rootCmd.AddCommand(tasksCmd)

	tasksCmd.Flags().StringVarP(&taskStartDate, "start", "s", datetime.OneMonthAgo().String(), "Start date for the task range (YYYY-MM-DD)")
	tasksCmd.Flags().StringVarP(&taskEndDate, "end", "e", datetime.Today().String(), "End date for the task range (YYYY-MM-DD)")
	tasksCmd.Flags().BoolVarP(&tasksSkipDone, "skip-done", "d", true, "Skip done tasks in the output")
}
