package styles

import "github.com/charmbracelet/lipgloss"

var (
	BaseStyle = lipgloss.NewStyle().
			BorderStyle(lipgloss.NormalBorder()).
			BorderForeground(lipgloss.Color("240"))
	HighlightStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("205"))
	KeyStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("222"))
	ErrorStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("1"))
)

func Highlight(s string) string {
	return HighlightStyle.Render(s)
}

func Key(s string) string {
	return KeyStyle.Render(s)
}

func Error(s string) string {
	return ErrorStyle.Render(s)
}
