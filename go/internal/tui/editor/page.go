package editor

import (
	"fmt"
	"github.com/charmbracelet/bubbles/table"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"journal/internal/obsidian"
	"journal/internal/tui/messages"
	"journal/internal/tui/styles"
	"strconv"
	"strings"
	"time"
)

type mode int

const (
	normalMode mode = iota
	recordMode
	amendMode
	editStartTimeMode
	editEndTimeMode
)

type Model struct {
	// Define your Model fields here
	vault       *obsidian.Vault
	section     string
	currentDate string
	currentPage *obsidian.Page

	height int
	width  int

	events           table.Model
	err              error
	selectedEventIdx int // Index of the selected event in the table

	// For recording and amending events
	textInput textinput.Model
	mode      mode
}

func New(vault *obsidian.Vault, sectionName string) Model {
	ti := textinput.New()
	ti.Placeholder = "Enter event text..."
	ti.Focus()
	ti.Width = 80

	return Model{
		vault:     vault,
		section:   sectionName,
		textInput: ti,
		mode:      normalMode,
		width:     80,
		height:    24,
	}
}

func (m Model) Init() tea.Cmd {
	return nil
}

type updateEventsMsg struct{}

type newEventsMsg struct {
	events table.Model
}

func (m *Model) updateEvents() error {
	section, err := m.currentPage.FindSection(m.section)
	if err != nil {
		return err
	}
	events, err := section.Events()
	if err != nil {
		return err
	}

	cols := []table.Column{
		{Title: "Line", Width: 4},
		{Title: "Start", Width: 10},
		{Title: "End", Width: 10},
		{Title: "Histogram", Width: 10},
		{Title: "Text", Width: 50},
		{Title: "Tags", Width: 30},
	}
	var rows []table.Row
	for _, event := range events {
		var duration string
		if event.Duration != 0 {
			duration = event.Duration.String()
		}
		rows = append(rows, table.Row{
			strconv.Itoa(event.Line + 1),
			event.StartTime.String(),
			event.EndTime.String(),
			duration,
			event.Text,
			strings.Join(event.Tags, " "),
		})
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

	tbl.SetHeight(m.height - 4)

	m.events = tbl
	return nil

}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case messages.ResizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.events.SetHeight(m.height - 4)
	case messages.LoadPageMsg:
		m.currentDate = msg.Date.String()
		m.currentPage = msg.Page
		m.err = msg.Error
		m.mode = normalMode
		if m.err == nil && m.currentPage != nil {
			m.err = m.updateEvents()
		}
		return m, nil
	case updateEventsMsg:
		m.err = m.updateEvents()
		m.mode = normalMode
		return m, nil
	case tea.KeyMsg:
		switch m.mode {
		case normalMode:
			switch msg.String() {
			case "ctrl+c", "q":
				return m, tea.Quit
			case "left":
				return m, messages.PreviousPageCmd()
			case "right":
				return m, messages.NextPageCmd()
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
			case "ctrl+c":
				// Quit the application
				return m, tea.Quit
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
	}

	m.events, cmd = m.events.Update(msg)
	return m, cmd
}

func (m Model) recordEvent(text string) tea.Cmd {
	return func() tea.Msg {
		section, err := m.currentPage.FindSection(m.section)
		if err != nil {
			return err
		}

		var event *obsidian.Event
		var i int
		for i = section.End - 1; i >= section.Start; i-- {
			event = obsidian.MaybeParseEvent(i, m.currentPage.Content[i])
			if event != nil {
				break
			}
		}
		if event != nil {
			if event.EndTime == "" {
				event.EndTime = obsidian.TimeNow()
				m.currentPage.Content[i] = event.String()
			}
		}

		newEvent := &obsidian.Event{
			StartTime: obsidian.TimeNow(),
			Text:      text,
		}

		m.currentPage.Content = append(m.currentPage.Content[:section.End], append([]string{newEvent.String()}, m.currentPage.Content[section.End:]...)...)

		if err := m.currentPage.Save(); err != nil {
			return err
		}

		// Reset mode and refresh events
		m.mode = normalMode
		m.textInput.Blur()
		return updateEventsMsg{}
	}
}

func (m Model) amendEvent(text string) tea.Cmd {
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
		event := obsidian.MaybeParseEvent(lineNum, m.currentPage.Content[lineNum])
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
		return updateEventsMsg{}
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

// editEventTime is a helper function to edit either the start or end time of an event
func (m Model) editEventTime(newTime string, isStartTime bool) tea.Cmd {
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
		event := obsidian.MaybeParseEvent(lineNum, m.currentPage.Content[lineNum])
		if event == nil {
			return fmt.Errorf("Event not found at line %d", lineNum+1)
		}

		// Parse and update the time based on whether it's start or end time
		var currentTime string
		if isStartTime {
			currentTime = event.StartTime.String()
		} else {
			currentTime = event.EndTime.String()
		}

		parsedTime, err := parseTimeString(newTime, currentTime)
		if err != nil {
			return err
		}

		// Update the appropriate time field
		if isStartTime {
			event.StartTime, err = obsidian.TimeFromString(parsedTime)
			if err != nil {
				return fmt.Errorf("Invalid start time format")
			}
		} else {
			event.EndTime, err = obsidian.TimeFromString(parsedTime)
			if err != nil {
				return fmt.Errorf("Invalid end time format")
			}
		}

		// Recalculate duration if both start and end times exist
		if event.StartTime != "" && event.EndTime != "" {
			start := event.StartTime.Time()
			end := event.EndTime.Time()
			event.Duration = end.Sub(start)
			if event.Duration < 0 {
				if isStartTime {
					return fmt.Errorf("Start time must be before end time")
				} else {
					return fmt.Errorf("End time must be after start time")
				}
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
		return updateEventsMsg{}
	}
}

func (m Model) editStartTime(newTime string) tea.Cmd {
	return m.editEventTime(newTime, true)
}

func (m Model) editEndTime(newTime string) tea.Cmd {
	return m.editEventTime(newTime, false)
}

func (m Model) View() string {
	if m.err != nil {
		return m.err.Error() + "\n"
	}
	var sb strings.Builder

	switch m.mode {
	case normalMode:
		sb.WriteString("Press ")
		binding := func(key, help string) {
			sb.WriteString(styles.Key(key) + help)
		}
		binding("r", " to record, ")
		binding("a", " to amend, ")
		binding("s", " to edit start time, ")
		binding("e", " to edit end time, ")
		binding("←", "/")
		binding("→", " to switch pages, ")
		binding("tab", " to switch to page view, ")
		binding("Ctrl+c", " or ")
		binding("q", " to quit.\n")
		sb.WriteString(styles.BaseStyle.Render(m.events.View()) + "\n")
	case recordMode:
		sb.WriteString("Recording a new event. Press Enter to submit, Esc to cancel.\n")
		sb.WriteString(styles.BaseStyle.Render(m.events.View()) + "\n")
		sb.WriteString(m.textInput.View())
	case amendMode:
		sb.WriteString("Amending the selected event. Press Enter to submit, Esc to cancel.\n")
		sb.WriteString(styles.BaseStyle.Render(m.events.View()) + "\n")
		sb.WriteString(m.textInput.View())
	case editStartTimeMode:
		sb.WriteString("Editing start time. Format: HH:MM (24-hour) or +/-MM for relative adjustments. Press Enter to submit, Esc to cancel.\n")
		sb.WriteString(styles.BaseStyle.Render(m.events.View()) + "\n")
		sb.WriteString(m.textInput.View())
	case editEndTimeMode:
		sb.WriteString("Editing end time. Format: HH:MM (24-hour) or +/-MM for relative adjustments. Press Enter to submit, Esc to cancel.\n")
		sb.WriteString(styles.BaseStyle.Render(m.events.View()) + "\n")
		sb.WriteString(m.textInput.View())
	}

	return sb.String()
}
