package obsidian

import (
	"journal/internal/datetime"
	"regexp"
	"strings"
)

type Task struct {
	PageName   string
	LineNumber int

	Description string
	Status      string

	Completed    datetime.Date
	Created      datetime.Date
	Due          datetime.Date
	Started      datetime.Date
	Scheduled    datetime.Date
	Recurrence   string
	OnCompletion string
}

func (t Task) IsDone() bool {
	return t.Status == "x" || t.Status == "X"
}

func (t Task) String() string {
	var sb strings.Builder
	sb.WriteString("[" + t.Status + "] " + t.Description)

	if !t.Completed.IsEmpty() {
		sb.WriteString(" ✅ " + t.Completed.String())
	}
	if !t.Created.IsEmpty() {
		sb.WriteString(" ➕ " + t.Created.String())
	}
	if !t.Due.IsEmpty() {
		sb.WriteString(" 📅 " + t.Due.String())
	}
	if !t.Started.IsEmpty() {
		sb.WriteString(" 🛫 " + t.Started.String())
	}
	if !t.Scheduled.IsEmpty() {
		sb.WriteString(" ⏳ " + t.Scheduled.String())
	}
	if t.Recurrence != "" {
		sb.WriteString(" 🔁 " + t.Recurrence)
	}
	if t.OnCompletion != "" {
		sb.WriteString(" 🏁 " + t.OnCompletion)
	}

	return sb.String()
}

var (
	// taskRe matches the task Status and captures the Description.
	taskRe = regexp.MustCompile(`^(\[[ xX]])\s+`)

	// dateCompletedRe matches the Completed date emoji and captures the date.
	// e.g., ✅ 2024-05-21
	dateCompletedRe = regexp.MustCompile(`✅\s+(\d{4}-\d{2}-\d{2})`)

	// dateCreatedRe matches the Created date emoji and captures the date.
	// e.g., ➕ 2024-05-21
	dateCreatedRe = regexp.MustCompile(`➕\s+(\d{4}-\d{2}-\d{2})`)

	// dateDueRe matches the Due date emoji and captures the date.
	// e.g., 📅 2024-05-21
	dateDueRe = regexp.MustCompile(`📅\s+(\d{4}-\d{2}-\d{2})`)

	// dateStartedRe matches the start date emoji and captures the date.
	// e.g., 🛫 2024-05-21
	dateStartedRe = regexp.MustCompile(`🛫\s+(\d{4}-\d{2}-\d{2})`)

	// dateScheduledRe matches the Scheduled date emoji and captures the date.
	// e.g., ⏳ 2024-05-21
	dateScheduledRe = regexp.MustCompile(`⏳\s+(\d{4}-\d{2}-\d{2})`)

	// recurrenceRe matches the Recurrence emoji and captures the Recurrence rule.
	// e.g., 🔁 every week
	recurrenceRe = regexp.MustCompile(`🔁\s+(.+)`)

	// onCompletionActionRe matches the on-completion action.
	// e.g., 🏁 delete
	onCompletionActionRe = regexp.MustCompile(`🏁 (\w+)`)

	redundantSpacesRe = regexp.MustCompile(`\s+`)
)

func ParseTask(pageName string, lineNo int, line string) *Task {
	if !strings.HasPrefix(line, "- [") {
		return nil // Not a task line
	}
	line = strings.TrimPrefix(line, "- ")

	s := taskRe.FindString(line)
	if s == "" {
		return nil // Not a task line
	}
	status := s[1:2] // Extract the Status from [x] or [ ]
	line = strings.TrimPrefix(line, s)

	task := &Task{
		PageName:   pageName,
		LineNumber: lineNo,
		Status:     status,
	}

	completed := dateCompletedRe.FindStringSubmatch(line)
	if len(completed) > 1 {
		task.Completed = datetime.Date(completed[1])
		line = dateCompletedRe.ReplaceAllString(line, "")
	}
	created := dateCreatedRe.FindStringSubmatch(line)
	if len(created) > 1 {
		task.Created = datetime.Date(created[1])
		line = dateCreatedRe.ReplaceAllString(line, "")
	}
	due := dateDueRe.FindStringSubmatch(line)
	if len(due) > 1 {
		task.Due = datetime.Date(due[1])
		line = dateDueRe.ReplaceAllString(line, "")
	}
	started := dateStartedRe.FindStringSubmatch(line)
	if len(started) > 1 {
		task.Started = datetime.Date(started[1])
		line = dateStartedRe.ReplaceAllString(line, "")
	}
	scheduled := dateScheduledRe.FindStringSubmatch(line)
	if len(scheduled) > 1 {
		task.Scheduled = datetime.Date(scheduled[1])
		line = dateScheduledRe.ReplaceAllString(line, "")
	}
	recurrence := recurrenceRe.FindStringSubmatch(line)
	if len(recurrence) > 1 {
		task.Recurrence = recurrence[1]
		line = recurrenceRe.ReplaceAllString(line, "")
	}
	onCompletion := onCompletionActionRe.FindStringSubmatch(line)
	if len(onCompletion) > 0 {
		task.OnCompletion = onCompletion[1]
		line = onCompletionActionRe.ReplaceAllString(line, "")
	}

	line = redundantSpacesRe.ReplaceAllString(line, " ")
	task.Description = strings.TrimSpace(line)
	return task
}
