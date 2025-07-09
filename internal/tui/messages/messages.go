package messages

import (
	tea "github.com/charmbracelet/bubbletea"
	"journal/internal/obsidian"
)

type ResizeMsg struct {
	Width  int
	Height int
}

func ResizeCmd(width, height int) tea.Cmd {
	return func() tea.Msg {
		return ResizeMsg{
			Width:  width,
			Height: height,
		}
	}
}

type PreviousPageMsg struct{}

func PreviousPageCmd() tea.Cmd {
	return func() tea.Msg {
		return PreviousPageMsg{}
	}
}

type NextPageMsg struct{}

func NextPageCmd() tea.Cmd {
	return func() tea.Msg {
		return NextPageMsg{}
	}
}

type LoadPageMsg struct {
	Date  obsidian.Date
	Page  *obsidian.Page
	Error error
}

func LoadPageCmd(vault *obsidian.Vault, date obsidian.Date) tea.Cmd {
	return func() tea.Msg {
		page, err := vault.Page(date.String())
		if err != nil {
			return LoadPageMsg{
				Date:  date,
				Error: err,
			}
		}
		return LoadPageMsg{
			Date: date,
			Page: page,
		}
	}
}

func ErrorCmd(err error) tea.Cmd {
	return func() tea.Msg {
		return err
	}
}
