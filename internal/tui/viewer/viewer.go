package viewer

import (
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/mistakenelf/teacup/markdown"
	"journal/internal/obsidian"
	"journal/internal/tui/messages"
	"path"
)

type Model struct {
	vault *obsidian.Vault

	width  int
	height int

	markdown markdown.Model
}

func New(vault *obsidian.Vault) Model {
	return Model{
		vault:    vault,
		width:    80,
		height:   24,
		markdown: markdown.New(true, false, lipgloss.AdaptiveColor{Light: "0", Dark: "255"}),
	}
}

func (m Model) Init() tea.Cmd {
	return m.markdown.Init()
}

func (m *Model) Resize(width, height int) {
	m.width = width
	m.height = height
	m.markdown.SetSize(width, height)
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		case "left":
			return m, messages.PreviousPageCmd()
		case "right":
			return m, messages.NextPageCmd()
		}
	case messages.LoadPageMsg:
		if msg.Error != nil {
			return m, m.markdown.SetFileName("")
		} else {
			return m, m.markdown.SetFileName(path.Join(m.vault.Path, msg.Page.Path))
		}
	case messages.ResizeMsg:
		m.Resize(msg.Width, msg.Height)
	}

	var cmd tea.Cmd
	m.markdown, cmd = m.markdown.Update(msg)
	return m, cmd
}

func (m Model) View() string {
	return m.markdown.View()
}
