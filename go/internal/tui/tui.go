package tui

import (
	"fmt"
	"github.com/charmbracelet/bubbles/table"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"journal/internal/obsidian"
	"strconv"
	"strings"
	"time"
)

var (
	baseStyle = lipgloss.NewStyle().
			BorderStyle(lipgloss.NormalBorder()).
			BorderForeground(lipgloss.Color("240"))
	highlightStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("205"))
)

type mode int

const (
	normalMode mode = iota
	recordMode
	amendMode
	editStartTimeMode
	editEndTimeMode
)

type model struct {
	// Define your model fields here
	vault       *obsidian.Vault
	section     string
	currentDate string
	currentPage *obsidian.Page

	windowHeight int
	windowWidth  int

	events           table.Model
	err              error
	selectedEventIdx int // Index of the selected event in the table

	// For recording and amending events
	textInput textinput.Model
	mode      mode
}

func NewModel(vault *obsidian.Vault, page string, sectionName string) tea.Model {
	ti := textinput.New()
	ti.Placeholder = "Enter event text..."
	ti.Focus()
	ti.Width = 80

	return model{
		vault:       vault,
		section:     sectionName,
		currentDate: page,
		textInput:   ti,
		mode:        normalMode,
	}
}

type newPageMsg struct {
	page *obsidian.Page
}

func (m model) Init() tea.Cmd {
	return m.loadPage()
}

func (m model) loadPage() tea.Cmd {
	return func() tea.Msg {
		page, err := m.vault.Page(m.currentDate)
		if err != nil {
			return err
		}

		return newPageMsg{
			page: page,
		}
	}
}

type newEventsMsg struct {
	events table.Model
}

func (m model) refreshEvents() tea.Cmd {
	return func() tea.Msg {
		section, err := m.currentPage.FindSection(m.section)
		if err != nil {
			return err
		}

		cols := []table.Column{
			{Title: "Line", Width: 4},
			{Title: "Start", Width: 10},
			{Title: "End", Width: 10},
			{Title: "Duration", Width: 10},
			{Title: "Text", Width: 50},
			{Title: "Tags", Width: 30},
		}
		var rows []table.Row
		for i := section.Start; i < section.End; i++ {
			event := obsidian.MaybeParseEvent(m.currentPage.Content[i])
			if event != nil {
				var duration string
				if event.Duration != 0 {
					duration = event.Duration.String()
				}
				rows = append(rows, table.Row{
					strconv.Itoa(i + 1),
					event.StartTime,
					event.EndTime,
					duration,
					event.Text,
					strings.Join(event.Tags, " "),
				})
			}
		}
		tbl := table.New(
			table.WithColumns(cols),
			table.WithRows(rows),
			table.WithFocused(true),
		)
		s := table.DefaultStyles()
		s.Header = s.Header.
			BorderStyle(lipgloss.NormalBorder()).
			BorderForeground(lipgloss.Color("240")).
			BorderBottom(true).
			Bold(false)
		s.Selected = s.Selected.
			Foreground(lipgloss.Color("229")).
			Background(lipgloss.Color("57")).
			Bold(false)
		tbl.SetStyles(s)

		tbl.SetHeight(m.windowHeight - 4)

		return newEventsMsg{
			events: tbl,
		}
	}
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.windowHeight = msg.Height
		m.windowWidth = msg.Width
		m.events.SetHeight(m.windowHeight - 4)
	case tea.KeyMsg:
		switch m.mode {
		case normalMode:
			switch msg.String() {
			case "ctrl+c", "q":
				return m, tea.Quit
			case "left":
				// decrement the current date by one day
				date, err := obsidian.DateFromPage(m.currentDate)
				if err != nil {
					m.err = err
					return m, nil
				}
				date = date.AddDate(0, 0, -1)
				m.currentDate = obsidian.DateToPage(date)
				return m, m.loadPage()
			case "right":
				// increment the current date by one day
				date, err := obsidian.DateFromPage(m.currentDate)
				if err != nil {
					m.err = err
					return m, nil
				}
				date = date.AddDate(0, 0, 1)
				m.currentDate = obsidian.DateToPage(date)
				return m, m.loadPage()
			case "r":
				// Enter record mode
				m.mode = recordMode
				m.textInput.Focus()
				m.textInput.SetValue("")
				return m, nil
			case "a":
				// Enter amend mode
				if len(m.events.Rows()) == 0 {
					m.err = fmt.Errorf("No events to amend")
					return m, nil
				}
				m.selectedEventIdx = m.events.Cursor()
				m.mode = amendMode
				m.textInput.Focus()

				// Get the selected event's text
				row := m.events.SelectedRow()
				m.textInput.SetValue(row[4]) // Text is in column 4

				return m, nil
			case "s":
				// Enter edit start time mode
				if len(m.events.Rows()) == 0 {
					m.err = fmt.Errorf("No events to edit")
					return m, nil
				}
				m.selectedEventIdx = m.events.Cursor()
				m.mode = editStartTimeMode
				m.textInput.Focus()

				// Get the selected event's start time
				row := m.events.SelectedRow()
				m.textInput.SetValue(row[1]) // Start time is in column 1
				return m, nil
			case "e":
				// Enter edit end time mode
				if len(m.events.Rows()) == 0 {
					m.err = fmt.Errorf("No events to edit")
					return m, nil
				}
				m.selectedEventIdx = m.events.Cursor()
				m.mode = editEndTimeMode
				m.textInput.Focus()

				// Get the selected event's end time
				row := m.events.SelectedRow()
				m.textInput.SetValue(row[2]) // End time is in column 2
				return m, nil
			}
		case recordMode, amendMode, editStartTimeMode, editEndTimeMode:
			switch msg.String() {
			case "esc":
				// Cancel and return to normal mode
				m.mode = normalMode
				m.textInput.Blur()
				return m, nil
			case "enter":
				// Submit the text input and record or amend an event
				if m.mode == recordMode {
					return m, m.recordEvent(m.textInput.Value())
				} else if m.mode == amendMode {
					return m, m.amendEvent(m.textInput.Value())
				} else if m.mode == editStartTimeMode {
					return m, m.editStartTime(m.textInput.Value())
				} else if m.mode == editEndTimeMode {
					return m, m.editEndTime(m.textInput.Value())
				}
			}

			// Handle text input
			m.textInput, cmd = m.textInput.Update(msg)
			return m, cmd
		}
	case error:
		m.err = msg
	case newPageMsg:
		m.currentPage = msg.page
		m.err = nil
		return m, m.refreshEvents()
	case newEventsMsg:
		m.events = msg.events
		m.err = nil
		m.mode = normalMode
	}

	m.events, cmd = m.events.Update(msg)
	return m, cmd
}

func (m model) recordEvent(text string) tea.Cmd {
	return func() tea.Msg {
		section, err := m.currentPage.FindSection(m.section)
		if err != nil {
			return err
		}

		var event *obsidian.Event
		var i int
		for i = section.End - 1; i >= section.Start; i-- {
			event = obsidian.MaybeParseEvent(m.currentPage.Content[i])
			if event != nil {
				break
			}
		}
		if event != nil {
			if event.EndTime == "" {
				event.EndTime = time.Now().Format("15:04")
				m.currentPage.Content[i] = event.String()
			}
		}

		newEvent := &obsidian.Event{
			StartTime: time.Now().Format("15:04"),
			Text:      text,
		}

		m.currentPage.Content = append(m.currentPage.Content[:section.End], append([]string{newEvent.String()}, m.currentPage.Content[section.End:]...)...)

		if err := m.currentPage.Save(); err != nil {
			return err
		}

		// Reset mode and refresh events
		m.mode = normalMode
		m.textInput.Blur()
		return m.refreshEvents()()
	}
}

func (m model) amendEvent(text string) tea.Cmd {
	return func() tea.Msg {
		// Get the selected event
		rows := m.events.Rows()
		if m.selectedEventIdx >= len(rows) {
			return fmt.Errorf("Selected event not found")
		}

		row := rows[m.selectedEventIdx]
		lineStr := row[0]
		lineNum, err := strconv.Atoi(lineStr)
		if err != nil {
			return fmt.Errorf("Invalid line number: %s", lineStr)
		}

		// Line numbers in the table are 1-based, but content array is 0-based
		lineNum--

		// Parse the event
		event := obsidian.MaybeParseEvent(m.currentPage.Content[lineNum])
		if event == nil {
			return fmt.Errorf("Event not found at line %d", lineNum+1)
		}

		event.Text = text
		m.currentPage.Content[lineNum] = event.String()

		if err := m.currentPage.Save(); err != nil {
			return err
		}

		// Reset mode and refresh events
		m.mode = normalMode
		m.textInput.Blur()
		return m.refreshEvents()()
	}
}

// parseTimeString parses a time string which can be either:
// 1. A standard time in format "15:04" (HH:MM)
// 2. A relative adjustment like "+45" or "-15" (minutes)
func parseTimeString(timeStr string, referenceTime string) (string, error) {
	// Check if it's a relative adjustment
	if len(timeStr) > 0 && (timeStr[0] == '+' || timeStr[0] == '-') {
		// Parse the minutes to adjust
		minutes, err := strconv.Atoi(timeStr)
		if err != nil {
			return "", fmt.Errorf("Invalid relative time format. Use +MM or -MM")
		}

		// Parse the reference time
		refTime, err := time.Parse("15:04", referenceTime)
		if err != nil {
			return "", fmt.Errorf("Invalid reference time format")
		}

		// Apply the adjustment
		adjustedTime := refTime.Add(time.Duration(minutes) * time.Minute)

		// Return the adjusted time in the required format
		return adjustedTime.Format("15:04"), nil
	}

	// It's a standard time format, validate it
	parsedTime, err := time.Parse("15:04", timeStr)
	if err != nil {
		return "", fmt.Errorf("Invalid time format. Please use HH:MM (24-hour format) or +/-MM for relative adjustments")
	}

	return parsedTime.Format("15:04"), nil
}

func (m model) editStartTime(newTime string) tea.Cmd {
	return func() tea.Msg {
		// Get the selected event
		rows := m.events.Rows()
		if m.selectedEventIdx >= len(rows) {
			return fmt.Errorf("Selected event not found")
		}

		row := rows[m.selectedEventIdx]
		lineStr := row[0]
		lineNum, err := strconv.Atoi(lineStr)
		if err != nil {
			return fmt.Errorf("Invalid line number: %s", lineStr)
		}

		// Line numbers in the table are 1-based, but content array is 0-based
		lineNum--

		// Parse the event
		event := obsidian.MaybeParseEvent(m.currentPage.Content[lineNum])
		if event == nil {
			return fmt.Errorf("Event not found at line %d", lineNum+1)
		}

		// Parse and update the start time
		parsedTime, err := parseTimeString(newTime, event.StartTime)
		if err != nil {
			return err
		}
		event.StartTime = parsedTime

		// If end time exists, recalculate duration
		if event.EndTime != "" {
			start, _ := time.Parse("15:04", event.StartTime)
			end, _ := time.Parse("15:04", event.EndTime)
			event.Duration = end.Sub(start)
			if event.Duration < 0 {
				return fmt.Errorf("Start time must be before end time")
			}
		}

		// Update the content
		m.currentPage.Content[lineNum] = event.String()

		// Save the changes
		if err := m.currentPage.Save(); err != nil {
			return err
		}

		// Reset mode and refresh events
		m.mode = normalMode
		m.textInput.Blur()
		return m.refreshEvents()()
	}
}

func (m model) editEndTime(newTime string) tea.Cmd {
	return func() tea.Msg {
		// Get the selected event
		rows := m.events.Rows()
		if m.selectedEventIdx >= len(rows) {
			return fmt.Errorf("Selected event not found")
		}

		row := rows[m.selectedEventIdx]
		lineStr := row[0]
		lineNum, err := strconv.Atoi(lineStr)
		if err != nil {
			return fmt.Errorf("Invalid line number: %s", lineStr)
		}

		// Line numbers in the table are 1-based, but content array is 0-based
		lineNum--

		// Parse the event
		event := obsidian.MaybeParseEvent(m.currentPage.Content[lineNum])
		if event == nil {
			return fmt.Errorf("Event not found at line %d", lineNum+1)
		}

		// Parse and update the end time
		parsedTime, err := parseTimeString(newTime, event.EndTime)
		if err != nil {
			return err
		}
		event.EndTime = parsedTime

		// Recalculate duration
		start, _ := time.Parse("15:04", event.StartTime)
		end, _ := time.Parse("15:04", event.EndTime)
		event.Duration = end.Sub(start)
		if event.Duration < 0 {
			return fmt.Errorf("End time must be after start time")
		}

		// Update the content
		m.currentPage.Content[lineNum] = event.String()

		// Save the changes
		if err := m.currentPage.Save(); err != nil {
			return err
		}

		// Reset mode and refresh events
		m.mode = normalMode
		m.textInput.Blur()
		return m.refreshEvents()()
	}
}

func (m model) View() string {
	if m.err != nil {
		return m.err.Error() + "\n"
	}
	var sb strings.Builder
	sb.WriteString("Journal Entry for " + highlightStyle.Render(m.currentDate) + ". ")
	sb.WriteString("Section: " + highlightStyle.Render(m.section) + ". ")

	switch m.mode {
	case normalMode:
		sb.WriteString("Press r to record, a to amend, s to edit start time, e to edit end time, Ctrl+C or q to quit.\n")
		sb.WriteString(baseStyle.Render(m.events.View()) + "\n")
	case recordMode:
		sb.WriteString("Recording a new event. Press Enter to submit, Esc to cancel.\n")
		sb.WriteString(baseStyle.Render(m.events.View()) + "\n")
		sb.WriteString(m.textInput.View())
	case amendMode:
		sb.WriteString("Amending the selected event. Press Enter to submit, Esc to cancel.\n")
		sb.WriteString(baseStyle.Render(m.events.View()) + "\n")
		sb.WriteString(m.textInput.View())
	case editStartTimeMode:
		sb.WriteString("Editing start time. Format: HH:MM (24-hour) or +/-MM for relative adjustments. Press Enter to submit, Esc to cancel.\n")
		sb.WriteString(baseStyle.Render(m.events.View()) + "\n")
		sb.WriteString(m.textInput.View())
	case editEndTimeMode:
		sb.WriteString("Editing end time. Format: HH:MM (24-hour) or +/-MM for relative adjustments. Press Enter to submit, Esc to cancel.\n")
		sb.WriteString(baseStyle.Render(m.events.View()) + "\n")
		sb.WriteString(m.textInput.View())
	}

	return sb.String()
}
