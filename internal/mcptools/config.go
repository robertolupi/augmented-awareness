package mcptools

import (
	"journal/internal/application"
)

var app *application.App

func SetApp(a *application.App) {
	app = a
}
