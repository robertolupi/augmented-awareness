package search

import (
	"errors"
	"fmt"
	"github.com/blevesearch/bleve/v2"
	"journal/internal/obsidian"
	"log"
	"os"
	"path/filepath"
	"strings"
)

type Index struct {
	bleve.Index
}

// NewIndex creates a new search index using the provided path.
func NewIndex(dataPath string) (*Index, error) {

	indexPath := filepath.Join(dataPath, "journal_index.bleve")
	if indexPath[0] == '~' {
		// Expand the tilde to the home directory
		homeDir, err := os.UserHomeDir()
		if err != nil {
			return nil, fmt.Errorf("failed to get home directory: %w", err)
		}
		indexPath = filepath.Join(homeDir, strings.TrimPrefix(indexPath, "~"))
	}

	indexPath = filepath.Clean(indexPath)

	index, err := bleve.Open(indexPath)
	if errors.Is(err, bleve.ErrorIndexPathDoesNotExist) {
		indexMapping := bleve.NewIndexMapping()
		// Set up the index mapping for the fields we want to index
		indexMapping.DefaultAnalyzer = "standard"
		pageMapping := bleve.NewDocumentMapping()
		pageMapping.AddFieldMappingsAt("name", bleve.NewTextFieldMapping())
		pageMapping.AddFieldMappingsAt("content", bleve.NewTextFieldMapping())
		indexMapping.AddDocumentMapping("page", pageMapping)
		index, err = bleve.New(indexPath, indexMapping)
	}
	if err != nil {
		return nil, fmt.Errorf("error creating or opening search index at dataPath %q: %w", dataPath, err)
	}
	return &Index{Index: index}, nil
}

// Close closes the search index.
func (i *Index) Close() error {
	if i.Index == nil {
		return nil
	}
	err := i.Index.Close()
	if err != nil {
		log.Println("Error closing search index:", err)
	}
	i.Index = nil // Prevent further use after closing
	return err
}

func (i *Index) IndexPage(page *obsidian.Page) error {
	if i.Index == nil {
		return errors.New("search index is not initialized")
	}
	if page == nil {
		return errors.New("cannot index a nil page")
	}

	doc := map[string]interface{}{
		"name":    page.Name(),
		"content": page.Content,
	}

	err := i.Index.Index(page.Path, doc)
	if err != nil {
		return fmt.Errorf("error indexing page %q: %w", page.Path, err)
	}
	return nil
}
