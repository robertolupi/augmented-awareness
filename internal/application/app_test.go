package application

import (
	"github.com/stretchr/testify/assert"
	"testing"
)

const testVaultPath = "../../test_vault"
const testJournalSection = "Schedule"

func TestNew(t *testing.T) {
	dataPath := t.TempDir()
	app, err := New(testVaultPath, testJournalSection, dataPath)
	if err != nil {
		t.Fatalf("Failed to create new application: %v", err)
	}

	assert.Equal(t, app.VaultPath, testVaultPath, "Vault path should match")
	assert.Equal(t, app.JournalSection, testJournalSection, "Journal section should match")
	assert.Equal(t, app.DataPath, dataPath, "Data path should match")
	assert.NotNil(t, app.Vault, "Vault should not be nil")
}

func AppForTesting(t *testing.T) *App {
	app, err := New(testVaultPath, testJournalSection, t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	return app
}
