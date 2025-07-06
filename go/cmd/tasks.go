package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/obsidian"
	"log"
	"sort"
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

			tasks := map[obsidian.Task]struct{}{}

			for _, date := range dateRange {
				page, err := vault.Page(date.String())
				if err != nil {
					continue
				}
				for _, task := range page.Tasks() {
					if task.IsDone() {
						continue
					}
					tasks[task] = struct{}{}
				}
			}

			sortedTasks := make(SortedTasks, 0, len(tasks))
			for task := range tasks {
				sortedTasks = append(sortedTasks, task)
			}
			sort.Sort(sortedTasks)

			for _, task := range sortedTasks {
				fmt.Println(task.String())
			}
		},
	}
)

type SortedTasks []obsidian.Task

func (s SortedTasks) Len() int {
	return len(s)
}

func (s SortedTasks) Less(i, j int) bool {
	return s[i].Description < s[j].Description
}
func (s SortedTasks) Swap(i, j int) {
	s[i], s[j] = s[j], s[i]
}

func initTasksCmd() {
	rootCmd.AddCommand(tasksCmd)

	tasksCmd.Flags().StringVarP(&taskStartDate, "start", "s", oneWeekAgo(), "Start date for the task range (YYYY-MM-DD)")
	tasksCmd.Flags().StringVarP(&taskEndDate, "end", "e", today(), "End date for the task range (YYYY-MM-DD)")
}
