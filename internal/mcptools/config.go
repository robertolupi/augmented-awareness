package mcptools

import (
	"journal/internal/obsidian"
)

var vault *obsidian.Vault
var journalSection string
var dataPath string

// SetVault sets the vault instance to be used by MCP tools.
func SetVault(v *obsidian.Vault) {
	if v == nil {
		panic("vault cannot be nil")
	}
	vault = v
}

func SetJournalSection(section string) {
	journalSection = section
}

func SetDataPath(path string) {
	dataPath = path
}
