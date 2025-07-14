package application

import (
	"journal/internal/obsidian"
	"sort"
)

func (a *App) TasksInDateRange(start, end string, skipDone bool) ([]obsidian.Task, error) {
	// Get pages in the specified date range
	pages, err := a.Vault.PageRange(start, end)
	if err != nil {
		return nil, err
	}

	// Retrieve tasks from the pages
	tasks := map[string]obsidian.Task{}

	for _, page := range pages {
		for _, task := range page.Tasks() {
			if skipDone && task.IsDone() {
				continue
			}
			tasks[task.String()] = task
		}
	}

	sortedTasks := make([]obsidian.Task, 0, len(tasks))
	for _, task := range tasks {
		sortedTasks = append(sortedTasks, task)
	}
	sort.Slice(sortedTasks, func(i, j int) bool {
		return sortedTasks[i].Description < sortedTasks[j].Description
	})

	return sortedTasks, nil
}
