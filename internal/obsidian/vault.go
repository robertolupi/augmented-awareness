package obsidian

import (
	"fmt"
	"io/fs"
	"os"
)

type Vault struct {
	Path string
	FS   fs.FS
}

func NewVault(path string) (*Vault, error) {
	if path == "" {
		return nil, fmt.Errorf("vault path cannot be empty")
	}

	// Expand ~ in the path
	if path[0] == '~' {
		homeDir, err := os.UserHomeDir()
		if err != nil {
			return nil, fmt.Errorf("failed to get home directory: %w", err)
		}
		path = homeDir + path[1:]
	}

	// Check if the path exists
	info, err := os.Stat(path)
	if err != nil {
		return nil, fmt.Errorf("failed to stat vault path: %w", err)
	}
	if !info.IsDir() {
		return nil, fmt.Errorf("vault path is not a directory")
	}

	// Check if the .obsidian directory exists
	obsidianDir := path + "/.obsidian"
	if _, err := os.Stat(obsidianDir); os.IsNotExist(err) {
		return nil, fmt.Errorf(".obsidian directory does not exist in the vault path")
	}

	return &Vault{
		Path: path,
		FS:   os.DirFS(path),
	}, nil
}
