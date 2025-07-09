package search

import (
	"github.com/stretchr/testify/assert"
	"io/fs"
	"journal/internal/obsidian"
	"testing"
)

func NewTestIndex(t *testing.T) *Index {
	t.Helper()

	index, err := NewIndex(t.TempDir())
	if err != nil {
		t.Fatalf("NewIndex returned an error: %v", err)
	}

	vault, err := obsidian.NewVault("../../test_vault")
	if err != nil {
		t.Fatalf("NewVault returned an error: %v", err)
	}

	err = vault.WalkPages(func(path string, d fs.DirEntry, err error) error {
		page, err := vault.PageByPath(path)
		if err != nil {
			t.Fatalf("Failed to get page by path %q: %v", path, err)
		}
		if page == nil {
			t.Fatalf("No page found at path %q", path)
		}
		if err := index.IndexPage(page); err != nil {
			t.Fatalf("IndexPage returned an error for page %q: %v", page.Path, err)
		}
		return nil
	})
	if err != nil {
		t.Fatalf("WalkPages returned an error: %v", err)
	}

	return index
}

func TestNewIndex(t *testing.T) {
	index := NewTestIndex(t)
	defer func() {
		if err := index.Close(); err != nil {
			t.Errorf("Error closing index: %v", err)
		}
	}()

	if index.Index == nil {
		t.Fatal("Index is nil after creation")
	}
}

func TestIndex_Search(t *testing.T) {
	index := NewTestIndex(t)
	defer func() {
		if err := index.Close(); err != nil {
			t.Errorf("Error closing index: %v", err)
		}
	}()

	// TODO: understand why this is not working, but the program works
	results, err := index.Search("did some personal development")
	assert.NoError(t, err)
	assert.NotNil(t, results)
	assert.NotZero(t, len(results.Hits))
	assert.Equal(t, "2025-04-01.md", results.Hits[0].ID)
	assert.Equal(t, "2025-04-01", results.Hits[0].Fields["name"])
}
