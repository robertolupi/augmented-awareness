package config

import (
	"github.com/spf13/viper"
	"github.com/stretchr/testify/assert"
	"os"
	"testing"
)

func TestInitConfig(t *testing.T) {
	// Create a temporary config file
	file, err := os.CreateTemp("", ".journal.yaml")
	assert.NoError(t, err)
	defer os.Remove(file.Name())

	// Write some config to the file
	_, err = file.WriteString("vault:\n  path: /tmp/test-vault\n")
	assert.NoError(t, err)
	file.Close()

	viper.SetConfigType("yaml")

	// Initialize the config
	err = InitConfig(file.Name())
	assert.NoError(t, err)

	// Check that the values are loaded correctly
	assert.Equal(t, "/tmp/test-vault", viper.GetString(VaultPath))
	assert.Equal(t, "Journal and events", viper.GetString(JournalSection))
	assert.Equal(t, "~/.cache/journal", viper.GetString(DataPath))
}
