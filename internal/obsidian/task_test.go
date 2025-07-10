package obsidian

import (
	"testing"
)

func TestParseTask(t *testing.T) {
	tests := []struct {
		name        string
		input       string
		expected    *Task
		expectNil   bool
		description string
	}{
		{
			name:      "Basic task",
			input:     "- [ ] Basic task",
			expectNil: false,
			expected: &Task{
				Status:      " ",
				Description: "Basic task",
			},
			description: "Should parse a basic task with empty status",
		},
		{
			name:      "Completed task",
			input:     "- [x] Completed task",
			expectNil: false,
			expected: &Task{
				Status:      "x",
				Description: "Completed task",
			},
			description: "Should parse a completed task",
		},
		{
			name:      "Task with due date",
			input:     "- [ ] Task with due date 📅 2023-01-01",
			expectNil: false,
			expected: &Task{
				Status:      " ",
				Description: "Task with due date",
				Due:         "2023-01-01",
			},
			description: "Should parse a task with a due date",
		},
		{
			name:      "Task with multiple dates",
			input:     "- [ ] Task with dates ✅ 2023-01-01 ➕ 2023-01-02 📅 2023-01-03 🛫 2023-01-04 ⏳ 2023-01-05",
			expectNil: false,
			expected: &Task{
				Status:      " ",
				Description: "Task with dates",
				Completed:   "2023-01-01",
				Created:     "2023-01-02",
				Due:         "2023-01-03",
				Started:     "2023-01-04",
				Scheduled:   "2023-01-05",
			},
			description: "Should parse a task with multiple dates",
		},
		{
			name:      "Task with recurrence",
			input:     "- [ ] Task with recurrence 🔁 every week",
			expectNil: false,
			expected: &Task{
				Status:      " ",
				Description: "Task with recurrence",
				Recurrence:  "every week",
			},
			description: "Should parse a task with recurrence",
		},
		{
			name:      "Task with on-completion action",
			input:     "- [ ] Task with on-completion action 🏁 delete",
			expectNil: false,
			expected: &Task{
				Status:       " ",
				Description:  "Task with on-completion action",
				OnCompletion: "delete",
			},
			description: "Should parse a task with on-completion action",
		},
		{
			name:        "Not a task",
			input:       "This is not a task",
			expectNil:   true,
			description: "Should return nil for non-task lines",
		},
		{
			name:        "Empty line",
			input:       "",
			expectNil:   true,
			description: "Should return nil for empty lines",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			task := ParseTask("PageName", 1, tt.input)
			if tt.expectNil {
				if task != nil {
					t.Errorf("Expected nil, got %v", task)
				}
				return
			}
			if task == nil {
				t.Fatalf("Expected task, got nil")
			}
			if task.Status != tt.expected.Status {
				t.Errorf("Expected Status %q, got %q", tt.expected.Status, task.Status)
			}
			if task.Description != tt.expected.Description {
				t.Errorf("Expected Description %q, got %q", tt.expected.Description, task.Description)
			}
			if string(task.Completed) != string(tt.expected.Completed) {
				t.Errorf("Expected Completed %q, got %q", tt.expected.Completed, task.Completed)
			}
			if string(task.Created) != string(tt.expected.Created) {
				t.Errorf("Expected Created %q, got %q", tt.expected.Created, task.Created)
			}
			if string(task.Due) != string(tt.expected.Due) {
				t.Errorf("Expected Due %q, got %q", tt.expected.Due, task.Due)
			}
			if string(task.Started) != string(tt.expected.Started) {
				t.Errorf("Expected Started %q, got %q", tt.expected.Started, task.Started)
			}
			if string(task.Scheduled) != string(tt.expected.Scheduled) {
				t.Errorf("Expected Scheduled %q, got %q", tt.expected.Scheduled, task.Scheduled)
			}
			if task.Recurrence != tt.expected.Recurrence {
				t.Errorf("Expected Recurrence %q, got %q", tt.expected.Recurrence, task.Recurrence)
			}
			if task.OnCompletion != tt.expected.OnCompletion {
				t.Errorf("Expected OnCompletion %q, got %q", tt.expected.OnCompletion, task.OnCompletion)
			}
		})
	}
}

func TestTaskIsDone(t *testing.T) {
	tests := []struct {
		name     string
		status   string
		expected bool
	}{
		{
			name:     "Empty status",
			status:   " ",
			expected: false,
		},
		{
			name:     "Lowercase x",
			status:   "x",
			expected: true,
		},
		{
			name:     "Uppercase X",
			status:   "X",
			expected: true,
		},
		{
			name:     "Other character",
			status:   "-",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			task := Task{Status: tt.status}
			if task.IsDone() != tt.expected {
				t.Errorf("Expected IsDone() to return %v, got %v", tt.expected, task.IsDone())
			}
		})
	}
}

func TestTaskString(t *testing.T) {
	tests := []struct {
		name     string
		task     Task
		expected string
	}{
		{
			name: "Basic task",
			task: Task{
				Status:      " ",
				Description: "Basic task",
			},
			expected: "[ ] Basic task",
		},
		{
			name: "Completed task",
			task: Task{
				Status:      "x",
				Description: "Completed task",
			},
			expected: "[x] Completed task",
		},
		{
			name: "Task with due date",
			task: Task{
				Status:      " ",
				Description: "Task with due date",
				Due:         "2023-01-01",
			},
			expected: "[ ] Task with due date 📅 2023-01-01",
		},
		{
			name: "Task with multiple dates",
			task: Task{
				Status:      " ",
				Description: "Task with dates",
				Completed:   "2023-01-01",
				Created:     "2023-01-02",
				Due:         "2023-01-03",
				Started:     "2023-01-04",
				Scheduled:   "2023-01-05",
			},
			expected: "[ ] Task with dates ✅ 2023-01-01 ➕ 2023-01-02 📅 2023-01-03 🛫 2023-01-04 ⏳ 2023-01-05",
		},
		{
			name: "Task with recurrence",
			task: Task{
				Status:      " ",
				Description: "Task with recurrence",
				Recurrence:  "every week",
			},
			expected: "[ ] Task with recurrence 🔁 every week",
		},
		{
			name: "Task with on-completion action",
			task: Task{
				Status:       " ",
				Description:  "Task with on-completion action",
				OnCompletion: "delete",
			},
			expected: "[ ] Task with on-completion action 🏁 delete",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.task.String()
			if result != tt.expected {
				t.Errorf("Expected %q, got %q", tt.expected, result)
			}
		})
	}
}
