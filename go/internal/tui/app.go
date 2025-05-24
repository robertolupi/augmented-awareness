package tui

import (
	"fmt"
	tea "github.com/charmbracelet/bubbletea"
	"journal/internal/obsidian"
	"journal/internal/tui/editor"
	"journal/internal/tui/messages"
	"journal/internal/tui/plot"
	"journal/internal/tui/styles"
	"journal/internal/tui/viewer"
	"strings"
)

type mode int

const (
	editorMode mode = iota
	viewerMode
	plotMode
)

type Model struct {
	vault          *obsidian.Vault
	journalSection string
	date           obsidian.Date
	page           *obsidian.Page

	width  int
	height int

	main tea.Model

	mode mode

	error error
}

func New(vault *obsidian.Vault, journalSection string) Model {
	return Model{
		vault:          vault,
		journalSection: journalSection,
		width:          80,
		height:         24,
		main:           editor.New(vault, journalSection),
		mode:           editorMode,
	}
}

func (m Model) Init() tea.Cmd {
	return tea.Batch(
		m.main.Init(),
		messages.LoadPageCmd(m.vault, obsidian.Today()))
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case messages.LoadPageMsg:
		m.date = msg.Date
		if msg.Error != nil {
			m.error = msg.Error
			m.page = nil
		}
		if msg.Page != nil {
			m.page = msg.Page
			m.error = nil
		}
	case messages.PreviousPageMsg:
		date := m.date.AddDays(-1)
		return m, messages.LoadPageCmd(m.vault, date)
	case messages.NextPageMsg:
		date := m.date.AddDays(1)
		return m, messages.LoadPageCmd(m.vault, date)
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, messages.ResizeCmd(msg.Width, msg.Height-1)
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c":
			return m, tea.Quit
		case "tab":
			if m.page == nil {
				m.error = fmt.Errorf("no page loaded")
				break
			}
			date, err := m.page.Date()
			if err != nil {
				m.error = err
				break
			}
			switch m.mode {
			case editorMode:
				m.mode = viewerMode
				m.main = viewer.New(m.vault)
			case viewerMode:
				m.mode = plotMode
				m.main = plot.New(m.vault)
			case plotMode:
				m.mode = editorMode
				m.main = editor.New(m.vault, m.journalSection)
			}
			cmd = tea.Batch(m.main.Init(),
				messages.ResizeCmd(m.width, m.height-1),
				messages.LoadPageCmd(m.vault, date))
			return m, cmd
		}
	}

	// Pass on other messages to the current mode
	m.main, cmd = m.main.Update(msg)
	return m, cmd
}

func (m Model) View() string {
	var sb strings.Builder
	sb.WriteString("Vault: " + styles.Highlight(m.vault.Path))
	sb.WriteString(" Date: " + styles.Highlight(m.date.String()))
	if m.page != nil {
		sb.WriteString(" Page: " + styles.Highlight(m.page.Path))
	} else {
		sb.WriteString(" Page: " + styles.Highlight("No page loaded"))
	}
	sb.WriteString("\n")
	if m.error != nil {
		sb.WriteString(" Error: " + styles.Error(m.error.Error()))
	} else {
		sb.WriteString(m.main.View())
	}
	return sb.String()
}
