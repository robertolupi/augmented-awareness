package tui

import (
	"github.com/charmbracelet/bubbles/progress"
	tea "github.com/charmbracelet/bubbletea"
	"log"
	"strings"
)

type ProgressBar struct {
	text string
	progress.Model
	errors []error
}

type UpdateProgressMsg struct {
	Text     string
	Progress float64
}

type ErrorProgressMsg struct {
	Error error
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
		progressBar.text = msg.Text
		return progressBar, progressBar.Model.SetPercent(msg.Progress)
	case ErrorProgressMsg:
		progressBar.errors = append(progressBar.errors, msg.Error)
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c":
			return progressBar, tea.Quit
		}
	}
	pbar, cmd := progressBar.Model.Update(msg)
	progressBar.Model = pbar.(progress.Model)
	return progressBar, cmd
}

func (progressBar ProgressBar) View() string {
	var sb strings.Builder
	if len(progressBar.errors) > 0 {
		sb.WriteString("\nErrors:\n")
		for _, err := range progressBar.errors {
			sb.WriteString("- " + err.Error() + "\n")
		}
	}
	sb.WriteString(progressBar.Model.View() + "\n")
	sb.WriteString(progressBar.text)
	return sb.String()
}

type SetProgressFunc func(text string, progress float64)
type ReportErrorFunc func(err error)
type LongRunningFunc func(SetProgressFunc, ReportErrorFunc) error

func ShowProgress(f LongRunningFunc) error {
	progressBar := NewProgressBar()
	p := tea.NewProgram(progressBar, tea.WithAltScreen())

	setProgress := func(text string, progress float64) {
		p.Send(UpdateProgressMsg{Text: text, Progress: progress})
	}
	reportError := func(err error) {
		p.Send(ErrorProgressMsg{Error: err})
	}

	var resultErr error

	go func() {
		resultErr = f(setProgress, reportError)
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
