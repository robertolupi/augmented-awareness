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
	"time"
)

type Vault struct {
	Path string
	FS   fs.FS
}

func NewVault(path string) (*Vault, error) {
	if path == "" {
		return nil, fmt.Errorf("vault path cannot be empty")
	}

	// Expand ~ in the path
	if path[0] == '~' {
		homeDir, err := os.UserHomeDir()
		if err != nil {
			return nil, fmt.Errorf("failed to get home directory: %w", err)
		}
		path = homeDir + path[1:]
	}

	// Check if the path exists
	info, err := os.Stat(path)
	if err != nil {
		return nil, fmt.Errorf("failed to stat vault path: %w", err)
	}
	if !info.IsDir() {
		return nil, fmt.Errorf("vault path is not a directory")
	}

	// Check if the .obsidian directory exists
	obsidianDir := path + "/.obsidian"
	if _, err := os.Stat(obsidianDir); os.IsNotExist(err) {
		return nil, fmt.Errorf(".obsidian directory does not exist in the vault path")
	}

	return &Vault{
		Path: path,
		FS:   os.DirFS(path),
	}, nil
}

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
			fmt.Printf("failed to close file: %w\n", err)
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
			fmt.Printf("failed to close file: %w\n", closeErr)

		}
	}()

	_, err = file.WriteString(contentBuilder.String())
	if err != nil {
		return fmt.Errorf("failed to write page content to file: %w", err)
	}

	return nil
}

// Events return all events in the given section of the page.
func (p *Page) Events(sectionHeader string) ([]Event, error) {
	section, err := p.FindSection(sectionHeader)
	if err != nil {
		return nil, err
	}

	var events []Event
	for i := section.Start; i < section.End; i++ {
		event := MaybeParseEvent(i, p.Content[i])
		if event != nil {
			events = append(events, *event)
		}
	}

	return events, nil
}

type Section struct {
	// Start and End line of the section in the page content
	Page  *Page
	Start int
	End   int
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

	return Section{Page: p, Start: start, End: end}, nil
}

type Event struct {
	Line      int
	StartTime string
	EndTime   string
	Start     time.Time
	Duration  time.Duration
	Text      string
	Tags      []string
}

func (event Event) String() string {
	var sb strings.Builder
	sb.WriteString(event.StartTime)
	if event.EndTime != "" {
		sb.WriteString(" - ")
		sb.WriteString(event.EndTime)
	}
	sb.WriteString(" ")
	sb.WriteString(event.Text)
	return sb.String()
}

// Events are lines that look like this:
// 03:00 - 04:00 #tag1 #tag2 Some text
// 03:00 Some text #tag1 #tag2

var eventRegex = regexp.MustCompile(`^(\d{2}:\d{2})\s*(-\s*(\d{2}:\d{2}))?\s*(.*?)$`)

func MaybeParseEvent(lineNo int, line string) *Event {
	matches := eventRegex.FindStringSubmatch(line)
	if matches == nil {
		return nil
	}

	startTime := matches[1]
	endTime := matches[3]
	var duration time.Duration
	var start time.Time
	var err error

	if endTime != "" {
		start, err = time.Parse("15:04", startTime)
		if err != nil {
			return nil
		}
		end, err := time.Parse("15:04", endTime)
		if err != nil {
			return nil
		}
		duration = end.Sub(start)
		if duration < 0 {
			return nil
		}
	}
	text := strings.TrimSpace(matches[4])

	var tags []string
	fields := strings.Fields(text)
	for _, field := range fields {
		if strings.HasPrefix(field, "#") {
			tags = append(tags, field[1:])
		}
	}

	return &Event{
		Line:      lineNo,
		StartTime: startTime,
		EndTime:   endTime,
		Start:     start,
		Duration:  duration,
		Text:      text,
		Tags:      tags,
	}
}
