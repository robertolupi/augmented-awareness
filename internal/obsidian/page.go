package obsidian

import (
	"fmt"
	"gopkg.in/yaml.v3"
	"io"
	"io/fs"
	"os"
	"path"
	"regexp"
	"strings"
)

type Page struct {
	Vault       *Vault
	Path        string
	Frontmatter map[string]interface{}
	Content     []string
}

func (v *Vault) PageByPath(pagePath string) (*Page, error) {
	file, err := v.FS.Open(pagePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open page: %w", err)
	}
	defer func() {
		if err := file.Close(); err != nil {
			fmt.Printf("failed to close file: %v\n", err)
		}
	}()

	content, err := io.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("failed to read page content: %w", err)
	}

	page := &Page{
		Vault:       v,
		Path:        pagePath,
		Frontmatter: make(map[string]interface{}),
	}

	fileContent := string(content)
	if strings.HasPrefix(fileContent, "---\n") {
		parts := strings.SplitN(fileContent[4:], "---", 2)
		if len(parts) == 2 {
			if err := yaml.Unmarshal([]byte(parts[0]), &page.Frontmatter); err != nil {
				return nil, fmt.Errorf("failed to parse frontmatter: %w", err)
			}
			fileContent = strings.TrimPrefix(parts[1], "\n")
		}
	}

	page.Content = strings.Split(fileContent, "\n")

	return page, nil
}

func (v *Vault) WalkPages(fn fs.WalkDirFunc) error {
	if v.FS == nil {
		return fmt.Errorf("vault filesystem is not initialized")
	}

	return fs.WalkDir(v.FS, ".", func(filePath string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() || !strings.HasSuffix(d.Name(), ".md") {
			return nil
		}
		return fn(filePath, d, nil)
	})
}

func (v *Vault) PageRange(startDate, endDate string) ([]*Page, error) {
	var pages []*Page

	dateRange, err := DateRange(startDate, endDate)
	if err != nil {
		return nil, fmt.Errorf("failed to parse date range: %w", err)
	}

	dates := map[string]bool{}
	for _, date := range dateRange {
		dates[date.String()] = true
	}

	err = v.WalkPages(func(filePath string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		pageName := strings.TrimSuffix(d.Name(), ".md")
		if dates[pageName] {
			page, err := v.PageByPath(filePath)
			if err != nil {
				return fmt.Errorf("failed to get page by path %s: %w", filePath, err)
			}
			pages = append(pages, page)
			delete(dates, pageName)
		}

		if len(dates) == 0 {
			return fs.SkipAll // Stop walking if we found all pages in the date range
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to walk pages: %w", err)
	}

	return pages, nil
}

func (v *Vault) Page(title string) (*Page, error) {
	var pagePath string

	err := v.WalkPages(func(filePath string, d fs.DirEntry, err error) error {
		if d.Name() == title+".md" {
			pagePath = filePath
			return fs.SkipAll // Stop walking once we find the page
		}
		return nil
	})

	if pagePath != "" {
		return v.PageByPath(pagePath)
	}

	return nil, fmt.Errorf("page with title %s not found: %v", title, err)
}

func (p *Page) Date() (Date, error) {
	if p.Path == "" {
		return EmptyDate, fmt.Errorf("page path is empty")
	}

	// Extract the date from the page path
	base := path.Base(p.Path)
	if strings.HasSuffix(base, ".md") {
		base = base[:len(base)-3]
	}

	date, err := DateFromString(base)
	if err != nil {
		return EmptyDate, fmt.Errorf("failed to parse date from page path: %w", err)
	}

	return date, nil
}

func (p *Page) Name() string {
	if p.Path == "" {
		return ""
	}

	base := path.Base(p.Path)
	if strings.HasSuffix(base, ".md") {
		return base[:len(base)-3] // Remove the .md extension
	}
	return base
}

func (p *Page) String() string {
	return p.Name()
}

func (p *Page) Save() error {
	var contentBuilder strings.Builder

	// Prepare frontmatter
	if len(p.Frontmatter) > 0 {
		data, err := yaml.Marshal(p.Frontmatter)
		if err != nil {
			return fmt.Errorf("failed to marshal frontmatter: %w", err)
		}
		_, err = contentBuilder.WriteString("---\n")
		if err != nil {
			return fmt.Errorf("failed to write frontmatter start delimiter: %w", err)
		}
		_, err = contentBuilder.Write(data)
		if err != nil {
			return fmt.Errorf("failed to write frontmatter data: %w", err)
		}
		_, err = contentBuilder.WriteString("---\n")
		if err != nil {
			return fmt.Errorf("failed to write frontmatter end delimiter: %w", err)
		}
	}

	// Prepare content
	for _, line := range p.Content {
		_, err := contentBuilder.WriteString(strings.TrimSuffix(line, "\n") + "\n")
		if err != nil {
			return fmt.Errorf("failed to write content line: %w", err)
		}
	}

	fullPath := path.Join(p.Vault.Path, p.Path)
	file, err := os.OpenFile(fullPath, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0644)
	if err != nil {
		return fmt.Errorf("failed to open file for writing: %w", err)
	}
	defer func() {
		if closeErr := file.Close(); closeErr != nil {
			fmt.Printf("failed to close file: %v\n", closeErr)

		}
	}()

	_, err = file.WriteString(contentBuilder.String())
	if err != nil {
		return fmt.Errorf("failed to write page content to file: %w", err)
	}

	return nil
}

type Section struct {
	// Start and End line of the section in the page content
	page  *Page
	Start int
	End   int
}

func (s *Section) Events() ([]Event, error) {
	var events []Event
	for i := s.Start; i < s.End; i++ {
		event := MaybeParseEvent(i, s.page.Content[i])
		if event != nil {
			events = append(events, *event)
		}
	}
	return events, nil
}

var sectionHeaderRegex = regexp.MustCompile(`^(#+)\s+(.*)$`)

// FindSection finds a section in the page content by its header.
// Sections are defined by headers in the markdown file. Header can be of any level (e.g., #, ##, ###).
// It returns the portion of the page until the next header of the same or higher level, or the End of the file.
func (p *Page) FindSection(section string) (Section, error) {
	section = strings.TrimSpace(section)
	if section == "" {
		return Section{}, fmt.Errorf("section name cannot be empty")
	}

	start := 0
	end := len(p.Content)
	var found bool
	var level int

	for i, line := range p.Content {
		if match := sectionHeaderRegex.FindStringSubmatch(line); match != nil {
			headerLevel := len(match[1])
			headerText := strings.TrimSpace(match[2])

			if found && headerLevel <= level {
				end = i
				break
			}
			if !found && headerText == section {
				start = i
				found = true
				level = headerLevel
			} else if found {
				end = i
				break
			}
		}
	}

	if !found {
		return Section{}, fmt.Errorf("section %s not found", section)
	}

	return Section{page: p, Start: start, End: end}, nil
}

func (s *Section) AmendEvent(ev Event) error {
	if s.page == nil {
		return fmt.Errorf("page is nil")
	}

	if ev.Line < s.Start || ev.Line >= s.End {
		return fmt.Errorf("event line number %d is out of section bounds (%d, %d)", ev.Line, s.Start, s.End)
	}

	if ev.StartTime.IsEmpty() {
		return fmt.Errorf("event start time is empty")
	}

	previous := MaybeParseEvent(ev.Line, s.page.Content[ev.Line])
	if previous == nil {
		return fmt.Errorf("no event found at line %d", ev.Line)
	}

	s.page.Content[ev.Line] = ev.String()
	return nil
}

func (s *Section) AddEvent(ev Event) error {
	if s.page == nil {
		return fmt.Errorf("page is nil")
	}

	if ev.StartTime.IsEmpty() {
		return fmt.Errorf("event start time is empty")
	}

	s.page.Content = append(s.page.Content[:s.End], append([]string{ev.String()}, s.page.Content[s.End:]...)...)
	return nil
}

func (p *Page) Tasks() []Task {
	var tasks []Task
	for n, line := range p.Content {
		task := ParseTask(p.Name(), n, line)
		if task != nil {
			tasks = append(tasks, *task)
		}
	}
	return tasks
}
