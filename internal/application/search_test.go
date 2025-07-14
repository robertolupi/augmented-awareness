package application

import (
	"journal/internal/search"
	"testing"

	"github.com/stretchr/testify/assert"
)

func AppForIndexTesting(t *testing.T) *App {
	app := AppForTesting(t)

	index, err := search.NewIndex(app.DataPath)
	if err != nil {
		t.Fatalf("Failed to create search index: %v", err)
	}
	defer index.Close()

	pages := []string{"index", "2025-03-30", "2025-04-01"}
	for _, pageName := range pages {
		page, err := app.Vault.Page(pageName)
		if err != nil {
			t.Fatalf("Failed to get page %s: %v", pageName, err)
		}
		if err := index.IndexPage(page); err != nil {
			t.Fatalf("Failed to add page %s to index: %v", pageName, err)
		}
	}

	return app
}

func TestApp_Search(t *testing.T) {
	app := AppForIndexTesting(t)

	results, err := app.Search("Schedule")
	if err != nil {
		t.Fatalf("Search failed: %v", err)
	}
	assert.Len(t, results, 2, "Expected 2 results for 'Schedule' search")
	pages := []string{}
	for _, result := range results {
		pages = append(pages, result.Name())
	}
	assert.Contains(t, pages, "2025-03-30", "Expected to find '2025-03-30' in search results")
	assert.Contains(t, pages, "2025-04-01", "Expected to find '2025-04-01' in search results")
	assert.NotContains(t, pages, "index", "Expected 'index' not to be in search results")
}
