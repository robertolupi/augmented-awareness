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

func (v *Vault) Page(date string) (*Page, error) {
	var pagePath string
	// Search the whole vault recursively for the journal page
	err := fs.WalkDir(v.FS, ".", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			return nil
		}
		if d.Name() == date+".md" {
			pagePath = path
			return fs.SkipAll
		}
		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to walk the vault: %w", err)
	}

	if pagePath == "" {
		return nil, fmt.Errorf("page not found for date: %s", date)
	}

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
	for _, line := range p.Content {
		task := ParseTask(line)
		if task != nil {
			tasks = append(tasks, *task)
		}
	}
	return tasks
}
