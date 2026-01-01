package search

import (
	"github.com/blevesearch/bleve/v2"
)

func (i *Index) Search(query string) (*bleve.SearchResult, error) {
	request := bleve.NewSearchRequest(bleve.NewQueryStringQuery(query))
	request.Fields = []string{"name"}
	return i.Index.Search(request)
}
