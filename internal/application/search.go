package application

import (
	"journal/internal/obsidian"
	"journal/internal/search"
)

func (a *App) Search(query string) ([]*obsidian.Page, error) {
	index, err := search.NewIndex(a.DataPath)
	if err != nil {
		return nil, err
	}
	defer index.Close()

	results, err := index.Search(query)
	if err != nil {
		return nil, err
	}

	pages := make([]*obsidian.Page, 0, len(results.Hits))
	for _, hit := range results.Hits {
		page, err := a.Vault.PageByPath(hit.ID)
		if err != nil {
			return nil, err
		}
		pages = append(pages, page)
	}

	return pages, nil
}
