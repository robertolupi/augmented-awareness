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

func NewTempVault(t *testing.T) *Vault {
	t.Helper()

	tempDir := t.TempDir()

	testVault := NewTestVault(t)

	// Copy the test vault contents to the temporary directory
	err := os.CopyFS(tempDir, testVault.FS)
	if err != nil {
		t.Fatalf("Failed to copy test vault to temporary directory: %v", err)
	}

	tempVault, err := NewVault(tempDir)
	if err != nil {
		t.Fatalf("NewVault returned an error: %v", err)
	}

	return tempVault
}

func TestTempVault(t *testing.T) {
	tempVault := NewTempVault(t)
	if tempVault == nil {
		t.Fatalf("NewTempVault returned nil")
	}

	// Check if the temporary vault has the expected pages
	page, err := tempVault.Page("2025-04-01")
	if err != nil {
		t.Fatalf("Failed to get page from temporary vault: %v", err)
	}

	if page == nil || len(page.Content) == 0 {
		t.Fatal("Expected page content to be non-empty")
	}
}
