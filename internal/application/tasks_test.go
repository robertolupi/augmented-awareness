package application

import (
	"github.com/stretchr/testify/assert"
	"journal/internal/obsidian"
	"testing"
)

func TestApp_TasksInDateRange(t *testing.T) {
	app := AppForTesting(t)

	tasks, err := app.TasksInDateRange("2025-03-30", "2025-04-01", false)
	if err != nil {
		t.Fatalf("Failed to retrieve tasks: %v", err)
	}

	expected := []obsidian.Task{
		{
			PageName:    "2025-04-01",
			LineNumber:  6,
			Description: "some task #tag3/with-parts and `some code`",
			Status:      " ",
		},
		{
			PageName:    "2025-03-30",
			LineNumber:  13,
			Description: "task 1",
			Status:      " ",
		},
		{
			PageName:    "2025-03-30",
			LineNumber:  14,
			Description: "task 2",
			Status:      "x",
		},
		{
			PageName:     "2025-03-30",
			LineNumber:   15,
			Description:  "task 3",
			Status:       "x",
			Completed:    "2025-04-04",
			Created:      "2025-04-03",
			Due:          "2025-04-06",
			Started:      "2025-04-04",
			Scheduled:    "2025-04-03",
			Recurrence:   "every day when done",
			OnCompletion: "",
		},
	}

	assert.Equal(t, expected, tasks, "Tasks in date range do not match expected output")
}
