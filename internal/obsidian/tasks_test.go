package obsidian

import (
	"testing"
)

func TestTasksInDateRange(t *testing.T) {
	// Create a mock vault
	mockVault := &MockVault{
		pages: map[string]*Page{
			"2023-01-01": {
				Content: []string{
					"- [ ] Task 1",
					"- [x] Task 2",
				},
			},
			"2023-01-02": {
				Content: []string{
					"- [ ] Task 3",
					"- [ ] Task 4",
				},
			},
			"2023-01-03": {
				Content: []string{
					"- [x] Task 5",
					"- [ ] Task 6",
				},
			},
		},
	}

	// Test with skipDone = true
	dateRange := []Date{"2023-01-01", "2023-01-02", "2023-01-03"}
	tasks, err := TasksInDateRange(mockVault, dateRange, true)
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
	tasks, err = TasksInDateRange(mockVault, dateRange, false)
	if err != nil {
		t.Fatalf("TasksInDateRange returned an error: %v", err)
	}

	// Check that all tasks are returned
	if len(tasks) != 6 {
		t.Errorf("Expected 6 tasks, got %d", len(tasks))
	}
}

func TestSortTasks(t *testing.T) {
	tasks := []Task{
		{Description: "C Task"},
		{Description: "A Task"},
		{Description: "B Task"},
	}

	SortTasks(tasks)

	// Check that tasks are sorted by description
	if tasks[0].Description != "A Task" {
		t.Errorf("Expected first task to be 'A Task', got '%s'", tasks[0].Description)
	}
	if tasks[1].Description != "B Task" {
		t.Errorf("Expected second task to be 'B Task', got '%s'", tasks[1].Description)
	}
	if tasks[2].Description != "C Task" {
		t.Errorf("Expected third task to be 'C Task', got '%s'", tasks[2].Description)
	}
}

// MockVault is a mock implementation of the Vault interface for testing
type MockVault struct {
	pages map[string]*Page
}

func (m *MockVault) Page(date string) (*Page, error) {
	page, ok := m.pages[date]
	if !ok {
		return nil, nil
	}
	return page, nil
}
