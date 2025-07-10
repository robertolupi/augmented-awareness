package obsidian

import (
	"sort"
)

func TasksInPages(pages []*Page, skipDone bool) ([]Task, error) {
	tasks := map[Task]struct{}{}

	for _, page := range pages {
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
	sort.Slice(sortedTasks, func(i, j int) bool {
		return sortedTasks[i].Description < sortedTasks[j].Description
	})

	return sortedTasks, nil
}
