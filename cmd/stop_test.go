package cmd

import (
	"journal/internal/datetime"
	"journal/internal/obsidian"
	"os"
	"testing"
)

func TestStopCurrentEvent(t *testing.T) {
	vault := newTempVault(t)

	page, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get page: %v", err)
	}

	section, err := page.FindSection("Schedule")
	if err != nil {
		t.Fatalf("Failed to find section: %v", err)
	}

	event := obsidian.Event{
		StartTime: mustTimeFromString(t, "10:15"),
		Text:      "Focus session",
	}

	if err := section.AddEvent(event); err != nil {
		t.Fatalf("Failed to add event: %v", err)
	}

	if err := page.Save(); err != nil {
		t.Fatalf("Failed to save page: %v", err)
	}

	pageAfterAdd, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to reload page: %v", err)
	}

	sectionAfterAdd, err := pageAfterAdd.FindSection("Schedule")
	if err != nil {
		t.Fatalf("Failed to find section after add: %v", err)
	}

	eventsBefore, err := sectionAfterAdd.Events()
	if err != nil {
		t.Fatalf("Failed to list events before stop: %v", err)
	}

	if err := stopCurrentEvent(vault, "Schedule", "2025-04-01"); err != nil {
		t.Fatalf("Failed to stop current event: %v", err)
	}

	pageAfterStop, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to reload page after stop: %v", err)
	}

	sectionAfterStop, err := pageAfterStop.FindSection("Schedule")
	if err != nil {
		t.Fatalf("Failed to find section after stop: %v", err)
	}

	eventsAfter, err := sectionAfterStop.Events()
	if err != nil {
		t.Fatalf("Failed to list events after stop: %v", err)
	}

	if len(eventsAfter) != len(eventsBefore) {
		t.Fatalf("Expected event count to remain the same, got %d before and %d after", len(eventsBefore), len(eventsAfter))
	}

	lastEvent := eventsAfter[len(eventsAfter)-1]
	if lastEvent.Text != "Focus session" {
		t.Fatalf("Expected last event text to be updated event, got %q", lastEvent.Text)
	}
	if lastEvent.EndTime.IsEmpty() {
		t.Fatalf("Expected last event to have an end time")
	}
}

func newTempVault(t *testing.T) *obsidian.Vault {
	t.Helper()

	tempDir := t.TempDir()

	testVault, err := obsidian.NewVault("../test_vault")
	if err != nil {
		t.Fatalf("Failed to load test vault: %v", err)
	}

	if err := os.CopyFS(tempDir, testVault.FS); err != nil {
		t.Fatalf("Failed to copy test vault: %v", err)
	}

	vault, err := obsidian.NewVault(tempDir)
	if err != nil {
		t.Fatalf("Failed to load temp vault: %v", err)
	}

	return vault
}

func mustTimeFromString(t *testing.T, value string) datetime.Time {
	t.Helper()

	parsed, err := datetime.TimeFromString(value)
	if err != nil {
		t.Fatalf("Failed to parse time %q: %v", value, err)
	}

	return parsed
}
