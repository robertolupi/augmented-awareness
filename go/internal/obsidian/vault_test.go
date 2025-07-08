package obsidian

import (
	"fmt"
	"os"
	"testing"
)

func NewTestVault(t *testing.T) *Vault {
	t.Helper()

	vault, err := NewVault("../../test_vault")
	if err != nil {
		t.Fatalf("NewVault returned an error: %v", err)
	}

	return vault
}

func TestNewVault(t *testing.T) {
	dir, err := os.Getwd()
	if err != nil {
		t.Fatalf("Failed to get current directory: %v", err)
	}
	fmt.Printf("Current directory: %s", dir)

	vault := NewTestVault(t)
	if vault == nil {
		t.Fatalf("NewTestVault returned nil")
	}
}
