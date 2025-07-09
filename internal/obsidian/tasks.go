package obsidian

import (
	"sort"
)

// PageProvider is an interface for retrieving pages by date
type PageProvider interface {
	Page(date string) (*Page, error)
}

// TasksInDateRange retrieves all tasks in the given date range from the vault.
// If skipDone is true, completed tasks are skipped.
func TasksInDateRange(vault PageProvider, dateRange []Date, skipDone bool) ([]Task, error) {
	tasks := map[Task]struct{}{}

	for _, date := range dateRange {
		page, err := vault.Page(date.String())
		if err != nil {
			continue
		}
		for _, task := range page.Tasks() {
			if skipDone && task.IsDone() {
				continue
			}
			tasks[task] = struct{}{}
		}
	}

	sortedTasks := make([]Task, 0, len(tasks))
	for task := range tasks {
		sortedTasks = append(sortedTasks, task)
	}
	SortTasks(sortedTasks)

	return sortedTasks, nil
}

// SortTasks sorts the given tasks by description.
func SortTasks(tasks []Task) {
	sort.Slice(tasks, func(i, j int) bool {
		return tasks[i].Description < tasks[j].Description
	})
}
