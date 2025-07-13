package application

import "journal/internal/obsidian"

type App struct {
	VaultPath      string
	JournalSection string
	DataPath       string
	Vault          *obsidian.Vault
}

func New(vaultPath, journalSection, dataPath string) (*App, error) {
	vault, err := obsidian.NewVault(vaultPath)
	if err != nil {
		return nil, err
	}

	return &App{
		VaultPath:      vaultPath,
		JournalSection: journalSection,
		DataPath:       dataPath,
		Vault:          vault,
	}, nil
}
