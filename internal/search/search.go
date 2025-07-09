package search

import (
	"github.com/blevesearch/bleve/v2"
	"strings"
)

func (i *Index) Search(query string) (*bleve.SearchResult, error) {
	request := bleve.NewSearchRequest(bleve.NewTermQuery(strings.ToLower(query)))
	return i.Index.Search(request)
}
