package tui

import (
	"github.com/charmbracelet/bubbles/progress"
	tea "github.com/charmbracelet/bubbletea"
	"log"
)

type ProgressBar struct {
	text string
	progress.Model
}

type UpdateProgressMsg struct {
	Percent float64
}

func NewProgressBar() ProgressBar {
	return ProgressBar{
		Model: progress.New(progress.WithDefaultGradient()),
	}
}

func (progressBar ProgressBar) Init() tea.Cmd {
	return progressBar.Model.Init()
}

func (progressBar ProgressBar) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	switch msg := msg.(type) {
	case UpdateProgressMsg:
		return progressBar, progressBar.Model.SetPercent(msg.Percent)
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c":
			return progressBar, tea.Quit
		}
	}
	model, cmd := progressBar.Model.Update(msg)
	return ProgressBar{Model: model.(progress.Model)}, cmd
}

func (progressBar ProgressBar) View() string {
	return progressBar.Model.View()
}

type SetProgressFunc func(float64)
type LongRunningFunc func(SetProgressFunc) error

func ShowProgress(f LongRunningFunc) error {
	progressBar := NewProgressBar()
	p := tea.NewProgram(progressBar, tea.WithAltScreen())

	setProgress := func(percent float64) {
		p.Send(UpdateProgressMsg{Percent: percent})
	}

	var resultErr error

	go func() {
		resultErr = f(setProgress)
		if resultErr != nil {
			log.Println("Error during long-running operation: %v", resultErr)
		}
		p.Send(tea.Quit)
	}()

	if _, err := p.Run(); err != nil {
		return err
	}

	return resultErr
}
