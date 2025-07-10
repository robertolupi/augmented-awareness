package obsidian

import (
	"github.com/stretchr/testify/assert"
	"io/fs"
	"testing"
)

func TestVault_WalkPages(t *testing.T) {
	allPages := make(map[string]bool)
	vault := NewTestVault(t)
	err := vault.WalkPages(func(pagePath string, d fs.DirEntry, err error) error {
		allPages[d.Name()] = true
		return nil
	})
	if err != nil {
		t.Fatalf("Failed to walk pages: %v", err)
	}
	assert.NotEmpty(t, allPages, "expected to find at least one page in the vault")

	expectedPages := map[string]bool{
		"index.md":      true,
		"2025-03-30.md": true,
		"2025-04-01.md": true,
	}

	for pageName := range expectedPages {
		if _, exists := allPages[pageName]; !exists {
			t.Errorf("Expected page %s not found in vault", pageName)
		}
	}

	assert.Equal(t, len(expectedPages), len(allPages), "expected number of pages does not match actual number of pages found")
}

func TestVault_PageByPath(t *testing.T) {
	vault := NewTestVault(t)
	page, err := vault.PageByPath("2025-04-01.md")
	if err != nil {
		t.Fatalf("Failed to get page by path: %v", err)
	}
	assert.NotNil(t, page)
	assert.Equal(t, page.Frontmatter, map[string]interface{}{"stress": 5})
	assert.NotEmpty(t, page.Content)
	assert.Equal(t, page.Content[0], "# 2025-04-01")
}

func TestVault_Page(t *testing.T) {
	vault := NewTestVault(t)

	page, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get index page: %v", err)
	}

	assert.NotNil(t, page)
	assert.Equal(t, page.Frontmatter, map[string]interface{}{"stress": 5})
	assert.NotEmpty(t, page.Content)
	assert.Equal(t, page.Content[0], "# 2025-04-01")
}

func TestVault_PageNotFound(t *testing.T) {
	vault := NewTestVault(t)

	_, err := vault.Page("non-existent-page")
	if err == nil {
		t.Fatal("Expected error when accessing non-existent page, but got none")
	}

	assert.ErrorContainsf(t, err, "non-existent-page", "expected error should contain missing page name")
}

func TestVault_PageRange(t *testing.T) {
	vault := NewTestVault(t)
	pages, err := vault.PageRange("2025-03-30", "2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get page range: %v", err)
	}
	assert.NotNil(t, pages)
	assert.Len(t, pages, 2, "expected 2 pages in the range")
	assert.Equal(t, pages[0].Name(), "2025-03-30")
	assert.Equal(t, pages[1].Name(), "2025-04-01")
}

func TestPage_Date(t *testing.T) {
	vault := NewTestVault(t)
	page, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get page: %v", err)
	}

	assert.Equal(t, page.Name(), "2025-04-01")
	date, err := page.Date()
	if err != nil {
		t.Fatalf("Failed to get page date: %v", err)
	}
	assert.Equal(t, date.String(), "2025-04-01")
}

func TestPage_String(t *testing.T) {
	vault := NewTestVault(t)
	page, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get page: %v", err)
	}

	expectedString := "2025-04-01"
	assert.Equal(t, expectedString, page.String(), "expected string representation of the page to match")
}

func TestPage_DateError(t *testing.T) {
	vault := NewTestVault(t)
	page, err := vault.Page("index")
	if err != nil {
		t.Fatalf("Failed to get page: %v", err)
	}

	_, err = page.Date()
	assert.Error(t, err, "expected error when page name is not a date")
}

func TestPage_Tasks(t *testing.T) {
	vault := NewTestVault(t)
	page, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get page: %v", err)
	}

	tasks := page.Tasks()

	assert.NotNil(t, tasks)
	assert.Len(t, tasks, 1)
}

func TestPage_FindSection(t *testing.T) {
	vault := NewTestVault(t)
	page, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get page: %v", err)
	}

	section, err := page.FindSection("Schedule")
	if err != nil {
		t.Fatalf("Failed to find section: %v", err)
	}

	assert.NotNil(t, section)
	assert.Equal(t, 8, section.Start)
	assert.Equal(t, 26, section.End)

	events, err := section.Events()
	assert.NoError(t, err, "expected no error when getting events from section")
	assert.NotEmpty(t, events, "expected events to be found in section")
}

func TestPage_Save(t *testing.T) {
	vault := NewTempVault(t)
	page, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get page: %v", err)
	}

	page.Content[0] = "# Updated Content"
	err = page.Save()
	if err != nil {
		t.Fatalf("Failed to save page: %v", err)
	}

	// Reload the page to verify changes
	updatedPage, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to reload page: %v", err)
	}

	assert.Equal(t, updatedPage.Content[0], "# Updated Content", "expected content to be updated")
}

func TestPage_AmendEvent(t *testing.T) {
	vault := NewTempVault(t)
	page, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get page: %v", err)
	}

	section, err := page.FindSection("Schedule")
	if err != nil {
		t.Fatalf("Failed to find section: %v", err)
	}

	events, err := section.Events()
	if err != nil {
		t.Fatalf("Failed to get events from section: %v", err)
	}

	assert.NotEmpty(t, events, "expected events to be found in section")

	event := events[0]
	event.Text = "Updated Event Text"
	err = section.AmendEvent(event)
	if err != nil {
		t.Fatalf("Failed to amend event: %v", err)
	}

	assert.Equal(t, "06:04 Updated Event Text", page.Content[event.Line], "expected event text to be updated in page content")
}

func TestPage_AmendEventError(t *testing.T) {
	vault := NewTempVault(t)
	page, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get page: %v", err)
	}

	section, err := page.FindSection("Schedule")
	if err != nil {
		t.Fatalf("Failed to find section: %v", err)
	}

	// Create an event that does not exist in the section, and doesn't have a valid line number
	event := Event{
		Text: "Non-existent Event",
	}

	err = section.AmendEvent(event)
	assert.Error(t, err, "expected error when amending non-existent event")
}

func TestPage_AddEvent(t *testing.T) {
	vault := NewTempVault(t)
	page, err := vault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get page: %v", err)
	}

	section, err := page.FindSection("Schedule")
	if err != nil {
		t.Fatalf("Failed to find section: %v", err)
	}

	newEvent := Event{
		Text:      "New Event",
		StartTime: mustTimeFromString(t, "14:00"),
		EndTime:   mustTimeFromString(t, "15:00"),
	}

	err = section.AddEvent(newEvent)
	if err != nil {
		t.Fatalf("Failed to add event: %v", err)
	}

	assert.Equal(t, page.Content[section.End], "14:00 - 15:00 New Event")
}
