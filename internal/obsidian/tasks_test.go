package obsidian

import (
	"testing"
)

func TestTasksInDateRange(t *testing.T) {
	// Create a mock vault
	pages := []*Page{
		{
			Content: []string{
				"- [ ] Task 1",
				"- [x] Task 2",
			},
		},
		{
			Content: []string{
				"- [ ] Task 3",
				"- [ ] Task 4",
			},
		},
		{
			Content: []string{
				"- [x] Task 5",
				"- [ ] Task 6",
			},
		},
	}
	// Test with skipDone = true
	tasks, err := TasksInPages(pages, true)
	if err != nil {
		t.Fatalf("TasksInDateRange returned an error: %v", err)
	}

	// Check that only non-done tasks are returned
	if len(tasks) != 4 {
		t.Errorf("Expected 4 tasks, got %d", len(tasks))
	}

	// Check that tasks are sorted by description
	if len(tasks) > 0 && tasks[0].Description != "Task 1" {
		t.Errorf("Expected first task to be 'Task 1', got '%s'", tasks[0].Description)
	}

	// Test with skipDone = false
	tasks, err = TasksInPages(pages, false)
	if err != nil {
		t.Fatalf("TasksInDateRange returned an error: %v", err)
	}

	// Check that all tasks are returned
	if len(tasks) != 6 {
		t.Errorf("Expected 6 tasks, got %d", len(tasks))
	}
}
