package obsidian

import (
	"fmt"
	"io/fs"
	"regexp"
	"strings"
)

func (v *Vault) Search(text string) ([]*Page, error) {
	var pages []*Page
	// Use a regular expression to match the text in the page title
	re := regexp.MustCompile("(?i)" + text)

	err := fs.WalkDir(v.FS, ".", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() || !strings.HasSuffix(d.Name(), ".md") {
			return nil
		}

		if re.MatchString(d.Name()) {
			page, err := v.Page(strings.TrimSuffix(d.Name(), ".md"))
			if err != nil {
				return fmt.Errorf("failed to get page: %w", err)
			}
			pages = append(pages, page)
		}
		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to search pages: %w", err)
	}

	return pages, nil
}
