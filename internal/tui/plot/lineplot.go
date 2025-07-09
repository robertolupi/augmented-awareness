package plot

import (
	"errors"
	"github.com/NimbleMarkets/ntcharts/linechart/timeserieslinechart"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"journal/internal/obsidian"
	"journal/internal/tui/messages"
	"journal/internal/tui/styles"
	"strconv"
	"strings"
)

type mode int

const (
	modePlot mode = iota
	modeMetricName
	modeDays
)

type Model struct {
	vault *obsidian.Vault

	date   obsidian.Date
	metric string
	days   int

	err error

	textInput textinput.Model
	chart     timeserieslinechart.Model
	mode      mode
}

func New(vault *obsidian.Vault) Model {
	ti := textinput.New()
	ti.Placeholder = "Enter metric name"
	ti.CharLimit = 20
	ti.Width = 20

	return Model{
		vault:     vault,
		days:      7,
		metric:    "stress",
		textInput: ti,
		chart:     timeserieslinechart.New(80, 24),
	}
}

func (m *Model) update() {
	m.chart.Clear()
	m.chart.ClearAllData()

	date := m.date.AddDays(-m.days + 1) // Start from the first day in the range
	for i := 0; i < m.days; i++ {
		page, err := m.vault.Page(date.String())
		if err == nil {
			var p timeserieslinechart.TimePoint
			if value, ok := page.Frontmatter[m.metric]; ok {
				switch v := value.(type) {
				case int:
					p = timeserieslinechart.TimePoint{
						Time:  date.Time(),
						Value: float64(v),
					}
				case float64:
					p = timeserieslinechart.TimePoint{
						Time:  date.Time(),
						Value: v,
					}
				case string:
					if f, err := strconv.ParseFloat(v, 64); err == nil {
						p = timeserieslinechart.TimePoint{
							Time:  date.Time(),
							Value: f,
						}
					}
				}
				if !p.Time.IsZero() {
					m.chart.Push(p)
				}
			}
		}
		date = date.AddDays(1)
	}
	m.chart.DrawBraille()
}

func (m Model) Init() tea.Cmd {
	return nil
}

type updateMsg struct{}

func updateCmd() tea.Cmd {
	return func() tea.Msg {
		return updateMsg{}
	}
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	switch msg := msg.(type) {
	case messages.ResizeMsg:
		m.chart.Resize(msg.Width, msg.Height-2)
		m.update()
	case messages.LoadPageMsg:
		m.date = msg.Date
		m.update()
	case updateMsg:
		m.update()
	case tea.KeyMsg:
		switch m.mode {
		case modePlot:
			switch msg.String() {
			case "ctrl+c", "q":
				return m, tea.Quit
			case "m":
				m.mode = modeMetricName
				m.textInput.Focus()
				m.textInput.SetValue(m.metric)
				return m, textinput.Blink
			case "d":
				m.mode = modeDays
				m.textInput.Focus()
				m.textInput.SetValue(strconv.Itoa(m.days))
				return m, textinput.Blink
			}
		case modeMetricName, modeDays:
			switch msg.String() {
			case "ctrl+c":
				return m, tea.Quit
			case "enter":
				if m.mode == modeMetricName {
					m.metric = m.textInput.Value()
					if m.metric == "" {
						m.err = errors.New("Metric name cannot be empty")
						return m, nil
					}
				} else if m.mode == modeDays {
					days, err := strconv.Atoi(m.textInput.Value())
					if err != nil || days <= 0 {
						m.err = errors.New("Invalid number of days")
						return m, nil
					}
					m.days = days
				}
				m.mode = modePlot
				m.textInput.Blur()
				return m, updateCmd()
			case "esc":
				m.mode = modePlot
				m.textInput.Blur()
				return m, updateCmd()
			}
			m.textInput, cmd = m.textInput.Update(msg)
			return m, cmd
		}
	}

	return m, nil
}

func (m Model) View() string {
	var sb strings.Builder

	if m.err != nil {
		sb.WriteString(styles.Error(m.err.Error()) + " ")
		// Clear the error after displaying it
		m.err = nil
	}
	switch m.mode {
	case modePlot:
		sb.WriteString("Metric: " + styles.Highlight(m.metric) + ", Days: " + styles.Highlight(strconv.Itoa(m.days)) + ". ")
		sb.WriteString("Press " + styles.Key("m") + " to enter metric name, ")
		sb.WriteString(styles.Key("d") + " to enter the number of days\n")
		sb.WriteString(m.chart.View())
		sb.WriteString("\n")
	case modeMetricName:
		sb.WriteString("Enter the metric name: ")
		sb.WriteString(m.textInput.View())
	case modeDays:
		sb.WriteString("Enter the number of days: ")
		sb.WriteString(m.textInput.View())
	}
	return sb.String()
}
