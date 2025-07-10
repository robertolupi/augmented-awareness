package obsidian

import (
	"sort"
)

// TasksInPages returns a list of tasks from the provided pages, merging duplicates.
func TasksInPages(pages []*Page, skipDone bool) ([]Task, error) {
	tasks := map[string]Task{}

	for _, page := range pages {
		for _, task := range page.Tasks() {
			if skipDone && task.IsDone() {
				continue
			}
			tasks[task.String()] = task
		}
	}

	sortedTasks := make([]Task, 0, len(tasks))
	for _, task := range tasks {
		sortedTasks = append(sortedTasks, task)
	}
	sort.Slice(sortedTasks, func(i, j int) bool {
		return sortedTasks[i].Description < sortedTasks[j].Description
	})

	return sortedTasks, nil
}
