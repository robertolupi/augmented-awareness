package obsidian

import (
	"github.com/stretchr/testify/assert"
	"testing"
)

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
